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
bp = Blueprint(name='infer', import_name=__name__)

DATETIME_FORMAT = "%Y-%m-%d_%H-%M-%S-%f"


# 要刷新不选择，要选择不刷新
# 暂时使用weights代替flows
@bp.route('/task/current')
@jwt_required(refresh=True)
def get_current_task():
    # 查询所有任务类型及其关联的任务
    task_type = TaskTypeModel.query.filter_by(id=session['task_type']).first()
    task = TaskModel.query.filter_by(id=session['task']).first()
    data = {
        'taskTypeName': task_type.name,
        'taskName': task.name,
    }
    return response(code=0, message='获取当前调用选择任务成功', data=data)


# 暂时使用weights代替flows
@bp.route('/task/all')
@jwt_required(refresh=True)
def get_all_tasks():
    # 查询所有任务类型及其关联的任务
    task_types = TaskTypeModel.query.all()
    # 构建返回给前端的字典结构
    data = []
    for task_type in task_types:
        for task in task_type.tasks:  # 装载全部配置
            data.append({
                'taskTypeName': task_type.name,
                'taskName': task.name
            })
    return response(code=0, message='获取所有任务映射成功', data=data)


@bp.route('/task/switch', methods=['POST'])
@jwt_required(refresh=True)
def switch_task():
    task_type_name = request.json.get('switchTaskTypeName', None).strip()
    task_name = request.json.get('switchTaskName', None).strip()
    if task_type_name is None:
        return response(code=1, message='切换模型失败，未选择任务类型')
    if task_name is None:
        return response(code=1, message='切换模型失败，未选择任务')
    task_type = TaskTypeModel.query.filter_by(name=task_type_name).first()
    if task_type is None:
        return response(code=1, message='切换模型失败，选择任务类型不存在')
    task = TaskModel.query.filter_by(name=task_name, type_id=task_type.id).first()
    if task is None:
        return response(code=1, message='切换模型失败，选择任务不存在')
    if task not in task_type.tasks:
        return response(code=1, message='切换模型失败，选择任务不属于选择任务类型')
    data = []
    for flow in task.flows:
        # model_manager.load_model_config(flow)  # 顺道装载
        for release in flow.releases:
            data.append({
                'flowName': flow.name,
                'releaseName': release.name,
                'releaseShowName': release.show_name,
            })
        # data.append(flow.to_dict())
    print_cyan(f'切换成功，当前任务类型：{task_type.name}，当前任务{task.name}')
    session['task_type'] = task_type.id
    session['task'] = task.id
    return response(code=200, message='切换任务类型成功', data=data)


# 暂时使用weights代替flows
@bp.route('/flow/current')
@jwt_required(refresh=True)
def get_current_flow():
    # 查询所有任务类型及其关联的任务
    flow = FlowModel.query.filter_by(id=session['flow']).first()
    release = ReleaseModel.query.filter_by(id=session['release']).first()
    data = {
        'flowName': flow.name,
        'releaseName': release.name,
    }
    return response(code=0, message='获取当前调用选中模型成功', data=data)


# 暂时使用weights代替flows
@bp.route('/flow/switch', methods=['POST'])
@jwt_required(refresh=True)
def switch_flow():
    # 查询所有任务类型及其关联的任务
    flow_name = request.json.get('switchFlowName', None).strip()
    release_name = request.json.get('switchReleaseName', None).strip()
    if not flow_name:
        return response(code=1, message='切换模型失败，未选择工作流模型')
    elif not release_name:
        return response(code=1, message='切换模型失败，未选择模型版本')
    # 构建返回给前端的字典结构
    try:
        flow = FlowModel.query.filter_by(name=flow_name).first()
    except Exception as e:
        return response(code=1, message='切换模型失败，选择工作流模型不存在')
    try:
        release = ReleaseModel.query.filter_by(name=release_name).first()
    except Exception as e:
        return response(code=1, message='切换模型失败，选择模型版本不存在')
    if release not in flow.releases:
        return response(code=1, message='切换模型失败，选择模型版本不属于选择工作流模型')
    session['flow'] = flow.id
    session['release'] = release.id  # 装载该模型的配置
    model_manager.load_model_config(release)
    data = {
        'weight': release.to_weights(),
        'param': release.to_params()
    }
    session['param'] = release.params
    return response(code=0, message='切换模型成功', data=data)


# 暂时使用weights代替flows
@bp.route('/weight/current')
@jwt_required(refresh=True)
def get_current_weight():
    weight_ids = session['weight']
    data = {}
    for key, wid in weight_ids.items():
        weight = WeightModel.query.filter_by(id=wid).first()
        data[key] = weight.to_dict()
    return response(code=0, message='获取当前调用选中模型成功', data=data)


# 暂时使用weights代替flows
@bp.route('/weight/switch', methods=['POST'])
@jwt_required(refresh=True)
def switch_weight():
    weightKey = request.json.get('switchWeightKey', None).strip()
    weightName = request.json.get('switchWeightName', None).strip()
    if weightKey is None or weightName is None:
        return response(code=1, message='切换权重失败，未选择权重')
    release = ReleaseModel.query.filter_by(id=session['release']).first()
    if weightKey not in release.keys:
        return response(code=1, message='切换权重失败，权重不属于工作流主键')
    weight = WeightModel.query.filter_by(name=weightName).first()
    if weight is None:
        return response(code=1, message='切换权重失败，当前权重不存在')
    if not release.check_weight(weight):
        return response(code=1, message='切换权重失败，当前版本下该权重不可用')

    if 'weight' not in session:
        session['weight'] = {}
    session['weight'][weightKey] = weight.id
    print_cyan(f'切换成功，当前权重主键: {weightKey}，当前权重名称: {weightName}')
    return response(code=0, message='获取当前调用选中模型成功')


# 暂时使用weights代替flows
@bp.route('/param/current')
@jwt_required(refresh=True)
def get_current_param():
    return response(code=0, message='获取当前调用选中模型成功', data=session['param'])


# 暂时将固定参数
@bp.route('/param/switch', methods=['POST'])
@jwt_required(refresh=True)
def switch_param():
    param = request.json.get('param', None).strip()
    if param:
        return response(code=1, message='修改配置失败，未设置配置')
    key, value = param.values()

    release = ReleaseModel.query.filter_by(id=session['release']).first()
    if key not in release.params:
        return response(code=1, message='切换配置失败，该配置不属于工作流主键')
    if type(release.params[key]) != type(value):
        return response(code=1, message='切换配置失败，配置类型不匹配')

    if 'param' not in session:
        session['param'] = {}
    session['param'][key] = value
    return response(code=0, message='配置修改成功')


@bp.route('/model/load')
@jwt_required(refresh=True)
def load_model():
    if 'release' not in session:
        return response(code=1, message='模型装载失败，未选择版本')
    release_id = session['release']
    if 'weight' not in session:
        return response(code=1, message='模型装载失败，未选择权重')
    weight_keys = session['weight']
    release = ReleaseModel.query.filter_by(id=release_id).first()
    config = release.to_config()
    for key in release.keys:
        if key not in weight_keys:
            return response(code=1, message=f'模型装载失败，权重选择不完整，缺少{key}')
        weight = WeightModel.query.filter_by(id=weight_keys[key]).first()
        config[key] = weight.to_config()
    if release.params is not None and release.params:
        if 'param' not in session:
            return response(code=1, message='模型装载失败，未设置配置')
        param = session['param']
        config.update(param)
    model_manager.load_model(release_id, config)
    data = model_manager.get_model_hypers()
    session['hyper'] = {item['hyperName']: item['hyperDefault'] if 'hyperDefault' in item else None
                        for item in data}  # 存初始值
    print_cyan(f'模型装载成功')
    return response(code=200, message=f'{release.name}模型装载成功', data=data)


@bp.route('/hyper/current')
@jwt_required(refresh=True)
def get_current_hyper():
    hyper = session['hyper']
    data = []
    full_hyper = model_manager.get_model_hypers()
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
    data = {
        'resultBase64': result_base64,
        'predictResult': predict_shapes,
        'predictDescription': predict_description,
        'period': (end_time - start_time).total_seconds()
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
    return base64.b64encode(buffered.getvalue()).decode('utf-8')