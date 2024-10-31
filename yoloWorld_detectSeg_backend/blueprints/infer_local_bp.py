import math
import os
from pprint import pprint
from typing import List, Tuple

import cv2
import imgviz
import numpy as np
from flask import Blueprint, request, render_template, g, redirect, session
from PIL import Image, ImageDraw, ImageFont
import datetime
import base64
from io import BytesIO
from flask_jwt_extended import jwt_required
from database_models import (WeightModel, TaskTypeModel, TaskModel, FlowModel, ReleaseModel,
                             WeightModel, ReleaseWeightModel, ResultModel)
from utils.backend_utils.dir_utils import *
from utils.backend_utils.model_handler import load_model
from utils.backend_utils.response_utils import response
from utils.backend_utils.colorprinter import *
from work_flow.engines.model_manager import ModelManager
from work_flow.engines.types import AutoLabelingMode
from work_flow.utils import base64_img_to_rgb_cv_img

from work_flow.utils.canvas import Canvas

'''
前后端code约定：
code: 0 成功 前端无消息弹窗
code: 1 失败 前端无消息弹窗
code: 200 前端消息弹窗Success
code: 201 前端消息弹窗Error
code: 202 前端消息弹窗Warning
code: 203 前端消息弹窗Info
code: 204 前端通知弹窗Success
code: 205 前端通知弹窗Error
code: 206 前端通知弹窗Warning
code: 207 前端通知弹窗Info
'''
model_manager = ModelManager()
predict_drawer = Canvas()
LABEL_COLORMAP = imgviz.label_colormap()
bp = Blueprint(name='infer_local', import_name=__name__)

DATETIME_FORMAT = "%Y-%m-%d_%H-%M-%S-%f"


# 要刷新不选择，要选择不刷新
# 暂时使用weights代替flows
@bp.route('/flow/current')
@jwt_required(refresh=True)
def get_current_flow():
    # 查询所有任务类型及其关联的任务
    data = {
        'taskTypeName': session['task_type'],
        'taskName': session['task'],
        'flowName': session['flow'],
        'releaseName': session['release']
    }
    return response(code=0, message='获取当前调用选择任务成功', data=data)


# 暂时使用weights代替flows
@bp.route('/flow/all')
@jwt_required(refresh=True)
def get_all_flows():
    # 查询所有任务类型及其关联的任务
    # 构建返回给前端的字典结构
    data = []
    model_manager.load_model_configs_yaml()
    for tt, ts in model_manager.task_configs.items():
        for t, fs  in ts.items():  # 装载全部配置
            for f, rs in fs.items():
                for r, detail in rs.items():
                    data.append({
                        'taskTypeName': tt,
                        'taskName': t,
                        'flowName': f,
                        'releaseName': r,
                        'releaseShowName': detail[1],
                    })
    return response(code=0, message='获取所有任务映射成功', data=data)


@bp.route('/flow/switch', methods=['POST'])
@jwt_required(refresh=True)
def switch_flow():
    task_type_name = request.json.get('switchTaskTypeName', None).strip()
    task_name = request.json.get('switchTaskName', None).strip()
    flow_name = request.json.get('switchFlowName', None).strip()
    release_name = request.json.get('switchReleaseName', None).strip()
    if task_type_name is None:
        return response(code=1, message='切换模型失败，未选择任务类型')
    if task_name is None:
        return response(code=1, message='切换模型失败，未选择任务')
    if task_type_name not in model_manager.task_configs:
        return response(code=1, message='切换模型失败，选择任务类型不存在')
    if task_name not in model_manager.task_configs[task_type_name]:
        return response(code=1, message='切换模型失败，选择任务不存在')
    if flow_name not in model_manager.task_configs[task_type_name][task_name]:
        return response(code=1, message='切换模型失败，选择流程不存在')
    if release_name not in model_manager.task_configs[task_type_name][task_name][flow_name]:
        return response(code=1, message='切换模型失败，选择版本不存在')
    session['task_type'] = task_type_name
    session['task'] = task_name
    session['flow'] = flow_name
    session['release'] = release_name
    print_cyan(f'切换成功，当前任务类型：{task_type_name}，当前任务{task_name}，当前流程{flow_name}，当前版本{release_name}')
    return response(code=200, message='切换工作流成功')

@bp.route('/model/load')
@jwt_required(refresh=True)
def load_model():
    if 'task_type' not in session:
        return response(code=1, message='模型装载失败，未选择任务类型')
    task_type = session['task_type']
    if 'task' not in session:
        return response(code=1, message='模型装载失败，未选择任务')
    task = session['task']
    if 'flow' not in session:
        return response(code=1, message='模型装载失败，未选择工作流')
    flow = session['flow']
    if 'release' not in session:
        return response(code=1, message='模型装载失败，未选择版本')
    release = session['release']
    model_id = model_manager.task_configs[task_type][task][flow][release][0]
    model_manager.load_model(model_id)
    data = model_manager.get_model_hypers_local()
    session['hyper'] = {item['hyperName']: item['hyperDefault'] if 'hyperDefault' in item else None
                        for item in data}  # 存初始值
    print_cyan(f'模型装载成功')
    return response(code=200, message=f'{release}模型装载成功', data=data)

@bp.route('/hyper/current')
@jwt_required(refresh=True)
def get_current_hyper():
    hyper = session['hyper']
    data = []
    full_hyper = model_manager.get_model_hypers_local()
    for key, value in hyper.items():
        cfg = {'name': key}
        cfg.update(full_hyper[key])
        if 'default' in cfg:
            cfg['default'] = value
        else:
            cfg['default'] = None
        data.append(cfg)
    return response(code=200, message=f'获取当前超参数成功', data=data)

@bp.route('/hyper/switch', methods=['POST'])
@jwt_required(refresh=True)
def switch_hyper():
    hyperName = request.json.get('switchHyperName', None)
    hyperValue = request.json.get('switchHyperValue', None)
    if hyperName or hyperValue:
        return response(code=1, message='修改超参数失败，未设置超参数')
    try:
        session['hyper'][hyperName] = hyperValue
    except Exception as e:
        return response(code=1, message=f'修改参数失败，{e}')

    return response(code=0, message='配置修改成功')


@bp.route('/model/predict', methods=['POST'])
def predict_model():
    # 检查请求中是否包含 base64 字符串
    if "originalBase64" not in request.json:
        return response(code=1, message='模型推断失败，未检测到图像base64编码')
    # 获取 base64 编码的图片字符串
    base64_data = request.json["originalBase64"]
    # 解码 base64 字符串
    hyper = session['hyper']
    # 模型推理
    start_time = datetime.datetime.now()
    model_manager.set_model_hyper(hyper)
    image = base64_img_to_rgb_cv_img(base64_data)
    auto_labeling_result = model_manager.predict_shapes_threading(image)
    predict_shapes = auto_labeling_result.shapes
    predict_description = auto_labeling_result.description
    predict_drawer.load_image(image)
    predict_drawer.load_shapes(predict_shapes)
    resultImage = predict_drawer.draw()
    result_base64 = base64_encode_image(resultImage)
    resultImage = Image.fromarray(resultImage)
    resultImage.show()
    end_time = datetime.datetime.now()
    predict_shapes = [shape.to_dict() for shape in predict_shapes]
    data = {
        'resultBase64': result_base64,
        'inferResult': predict_shapes,
        'inferDescription': predict_description,
        'inferPeriod': (end_time - start_time).total_seconds()
    }
    return response(code=0, message='模型推断已完成', data=data)


# base64编码推断后图片(图片最后的转换接口)
def batch_base64_encode_image(results_images):
    for im in results_images.imgs:
        buffered = BytesIO()
        im_base64 = Image.fromarray(im)
        im_base64.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

def base64_encode_image(image):
    buffered = BytesIO()
    im_base64 = Image.fromarray(image)
    im_base64.save(buffered, format="JPEG")
    img_str = base64.b64encode(buffered.getvalue()).decode('utf-8')
    return f"data:image/jpeg;base64,{img_str}"