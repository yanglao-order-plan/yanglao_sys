import base64
import time

import cv2
from flask import Blueprint,request,session
import requests
from flask_jwt_extended import jwt_required
from database_models import (WorkOrderModel, ReleaseModel, ExecuteModel, WeightModel, ServiceModel, FlowModel, )
from utils.backend_utils.response_utils import response
from work_flow.engines.model_manager import ModelManager
from utils.backend_utils.colorprinter import *
import onnxruntime as ort
import numpy as np
from PIL import Image
from io import BytesIO
import json
import datetime
import numpy

from work_flow.solutions import load_handler_class
from work_flow.solutions.cook_handler import CookHandler

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

bp = Blueprint(name='work_order', import_name=__name__,url_prefix='/work_order')
from work_flow.utils.canvas import Canvas
predict_drawer = Canvas()

@bp.route('/list/all')
@jwt_required(refresh=True)
def get_all_order_id():
    orders = WorkOrderModel.query.all()
    data = []
    for order in orders:
        order_data = {
            "orderId": order.order_id,
            "serviceId": order.service_id,
            "orderContent": order.order_content,
        }
        data.append(order_data)
    return response(code=1, message='查找work_order成功', data=data)

@bp.route('/list/one', methods=['GET'])
@jwt_required(refresh=True)
def get_work_orderByid():
    # 从订单表中获取订单信息
    order_id = request.args.get('order_id', None).strip()
    print_red(order_id)
    order = WorkOrderModel.query.filter_by(order_id=order_id).first()
    if not order:
        return response(code=0,message='未找到工单信息')
    # 获取每个订单的详细信息和相关图片
    # 直接通过order对象访问关联的图片
    image_sets = [image.image_set for image in order.image_sets]
    # 拼接最终返回的JSON数据
    data = {
        "orderId": order.order_id,
        "serviceId": order.service_id,
        "orderContent": order.order_content,
        "handle": order.handle,
        "startTime": order.start_time,
        "endTime": order.end_time,
        "imageSet": image_sets  # 返回对应的图片信息（多个图片的JSON数据）
    }
    print_red(data)
    return response(code=1,message='查找work_order成功',data=data)

@bp.route('/order/switch/<int:order_id>', methods=['POST'])
@jwt_required(refresh=True)
def switch_order(order_id):
    # 查询所有任务类型及其关联的任务
    order = WorkOrderModel.query.filter_by(id=order_id).first()
    if not order:
        return response(code=1, message='切换工单失败，该工单不存在')
    service = ServiceModel.query.filter_by(id=order_id).first()
    if not service:
        return response(code=1, message='切换工单失败，该工单所属服务不存在')
    HANDLER = load_handler_class(service.name)
    data = {}
    for flow in HANDLER.Flow_Keys:
        flow = FlowModel.query.filter_by(name=flow).first()
        data[flow.name] = []
        for rid in flow.releases:
            release = ReleaseModel.get(rid)
            data[flow.name].append(release.name)
    session['order'] = (order_id, service.name)
    return response(code=0, message='切换模型成功', data=data)


@bp.route('/order/switch/<str:release_name>', methods=['POST'])
@jwt_required(refresh=True)
def switch_release(release_name):
    # 查询所有任务类型及其关联的任务
    release = ReleaseModel.query.filter_by(name=release_name).first()
    if not release:
        return response(code=1, message='切换版本失败，该版本不存在')
    flow_id = release.flow_id
    data = {
        'weight': release.to_weights,
        'param': release.to_params
    }

    if 'release' not in session:
        session['release'] = {}
    session['release'][flow_id] = release.id
    if 'param' not in session:
        session['param'] = {}
    session['param'][flow_id] = release.params
    if 'weight' not in session:
        session['weight'] = {}
    session['weight'][flow_id] = {key: wid_list[0] for key, wid_list in release.weights.items()}

    return response(code=0, message='切换模型成功', data=data)

@bp.route('/order/param/current', methods=['POST'])
@jwt_required(refresh=True)
def get_current_param():
    paramRelease = request.json.get('switchParamRelease', '').strip()
    paramName = request.json.get('currentParamName', None).strip()
    release = ReleaseModel.query.filter_by(name=paramRelease).first()
    data = {'argName': paramName, 'argValue':
        session['param'][release.flow_id][paramName]}
    return response(code=0, message='获取当前静态参数获取成功', data=data)

@bp.route('/order/param/switch', methods=['POST'])
@jwt_required(refresh=True)
def switch_param():
    paramRelease = request.json.get('switchParamRelease', '').strip()
    paramName = request.json.get('switchParamName', '').strip()
    paramValue = request.json.get('switchParamValue', None)
    if isinstance(paramValue, str):
        paramValue = paramValue.strip()
    if not paramName:
        return response(code=1, message='修改配置失败，未设置配置')

    release = ReleaseModel.query.filter_by(name=paramRelease).first()
    if not paramName or paramName not in release.params:
        return response(code=1, message='切换配置失败，该配置不属于工作流主键')

    if 'param' not in session:
        session['param'] = {}

    session['param'][release.flow_id] = paramValue

    return response(code=0, message='配置修改成功')

@bp.route('/order/weight/current', methods=['POST'])
@jwt_required(refresh=True)
def get_current_weight():
    paramRelease = request.json.get('switchParamRelease', '').strip()
    weightKey = request.json.get('currentWeightKey', None).strip()
    release = ReleaseModel.query.filter_by(name=paramRelease).first()

    wid = session['weight'][release.flow_id][weightKey]
    weight = WeightModel.query.filter_by(id=wid).first()
    data = {'weightName': weight.name if weight is not None else None}
    return response(code=0, message='获取当前调用选中模型成功', data=data)

@bp.route('/order/weight/all/<str:release_name>', methods=['GET'])
@jwt_required(refresh=True)
def get_all_current_weights(release_name):
    data = []
    release = ReleaseModel.query.filter_by(name=release_name).first()
    for key, wid in session['weight'][release.id].items():
        weight = WeightModel.query.filter_by(id=wid).first()
        data.append({'weightKey': key, 'weightName': weight.name if weight is not None else None})

    return response(code=0, message='获取初始模型成功', data=data)

@bp.route('/order/weight/switch', methods=['POST'])
@jwt_required(refresh=True)
def switch_weight():
    paramRelease = request.json.get('switchParamRelease', '').strip()
    weightKey = request.json.get('switchWeightKey', None).strip()
    weightName = request.json.get('switchWeightName', None).strip()
    if weightKey is None or weightName is None:
        return response(code=1, message='切换权重失败，未选择权重')
    release = ReleaseModel.query.filter_by(name=paramRelease).first()

    if weightKey not in release.weights:
        return response(code=1, message='切换权重失败，权重不属于工作流主键')
    weight = WeightModel.query.filter_by(name=weightName).first()
    if weight is None:
        return response(code=1, message='切换权重失败，当前权重不存在')
    if not release.check_weight(weight):
        return response(code=1, message='切换权重失败，当前版本下该权重不可用')
    release = ReleaseModel.query.filter_by(id=paramRelease).first()

    if 'weight' not in session:
        session['weight'] = {}
    if release.flow_id not in session['weight']:
        session['weight'][release.flow_id] = {}
    session['weight'][release.flow_id][weightKey] = weight.id
    print_cyan(f'切换成功，当前权重主键: {weightKey}，当前权重名称: {weightName}')
    return response(code=0, message='获取当前调用选中模型成功')


@bp.route('/order/handler/infer',  methods=['GET'])
@jwt_required(refresh=True)
def infer():
    # 从订单表中获取订单信息
    config = {}
    for flow_id, release_id in session['release']:
        flow = FlowModel.query().filter_by(id=flow_id).first()
        release = ReleaseModel.query().filter_by(id=release_id).first()
        config[flow.name] = release.to_config()
        for key in release.weights:
            if key not in session['weight'][flow_id]:
                return response(code=1, message=f'模型装载失败，权重选择不完整，缺少{key}')
            weight = WeightModel.query.filter_by(id=session['weight'][key]).first()
            config[flow.name][key] = weight.to_config
        if release.params is not None and release.params:
            if 'param' not in session or flow_id not in session['param']:
                return response(code=1, message='模型装载失败，未设置配置')
            config[flow.name].update(session[flow_id]['param'])

    handler = load_handler_class(session['order'][1])(config)
    log = handler.run(session['order'][0])

    return response(code=0, message='模型推断已完成', data=log)

# 下载图片并加载
def load_image_from_url(image_url):
    response = requests.get(image_url)
    img = Image.open(BytesIO(response.content))
    return img

# 预处理图片
def preprocess_image(img):
    response = requests.get(img)
    # 使用 OpenCV 直接解码图像
    image_array = np.asarray(bytearray(response.content), dtype=np.uint8)
    image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
    # 将 BGR 转换为 RGB
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    # 转换为 (3, H, W) 的形状
    image_input = np.transpose(image, (2, 0, 1))
    # 添加批量维度，变为 (1, 3, H, W)
    image_input = np.expand_dims(image_input, axis=0)
    # 确保数据类型为 float32
    image_input = image_input.astype(np.float32)
    print("Formatted image input shape:", image_input.shape)  # 应该是 (1, 3, H, W)
    return image_input


# base64编码推断后图片(图片最后的转换接口)
def batch_base64_encode_image(results_images):
    for im in results_images.imgs:
        buffered = BytesIO()
        im_base64 = Image.fromarray(im)
        im_base64.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

def base64_encode_image(image) -> str:
    buffered = BytesIO()
    image=np.array(image)
    im_base64 = Image.fromarray(image)
    im_base64.save(buffered, format="JPEG")
    img_str = base64.b64encode(buffered.getvalue()).decode('utf-8')
    return f"data:image/jpeg;base64,{img_str}"