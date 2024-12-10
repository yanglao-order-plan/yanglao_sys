import base64
import time
from platform import release

import cv2
from flask import Blueprint,request,session
import requests
from flask_jwt_extended import jwt_required
from database_models import (WorkOrderModel, ReleaseModel, ExecuteModel, WeightModel, ServiceModel, ServiceLogModel, FlowModel)
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
from work_flow.flows.ppocr_v4_lama import PPOCRv4LAMA
from work_flow.solutions import load_handler_class
from work_flow.solutions.cook_handler import CookHandler
from math import ceil
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
model_manager = ModelManager()

@bp.route('/list')
@jwt_required(refresh=True)
def get_all_order_id():
    orderId=request.args.get('orderId')
    serviceId=request.args.get('serviceId')
    data = {"list": [], "total": []}
    orders=[]
    if orderId:
        order=WorkOrderModel.query.filter_by(id=orderId).first()
        orders.append(order)
        data['total'] = 1
    elif serviceId:
        page = int(request.args.get('currentPage', 1))  # 获取页码，默认为第一页
        per_page = int(request.args.get('size', 10))  # 获取每页显示的数据量，默认为 10 条
        pagination=WorkOrderModel.query.filter_by(service_id=serviceId).paginate(page=page, per_page=per_page,error_out=False)
        orders=pagination.items
        data['total'] =pagination.total
    else:
        page = int(request.args.get('currentPage', 1))  # 获取页码，默认为第一页
        per_page = int(request.args.get('size', 10))  # 获取每页显示的数据量，默认为 10 条
        pagination = WorkOrderModel.query.paginate(page=page, per_page=per_page,error_out=False)  # 使用 paginate() 方法进行分页查询，不抛出异常
        orders = pagination.items
        data['total'] = pagination.total
    for order in orders:
        service = get_work_orderByid(order.id, order.service_id)
        service_name=ServiceModel.query.filter_by(id=order.service_id).first().name
        if service_name is None:
            service_name="未知"
        else:
            service_name=service_name
        flag=1
        if service is None: flag=0
        order_data = {
            "orderId": order.id,
            "no": order.no,
            "serviceId": order.service_id,
            "projectType": service_name,
            "flag":flag
        }
        data['list'].append(order_data)
    return response(code=1, message='查找work_order成功', data=data)

@bp.route('/order/switch/<int:order_id>', methods=['POST'])
@jwt_required(refresh=True)
def switch_order(order_id):
    # 查询所有任务类型及其关联的任务
    order = WorkOrderModel.query.filter_by(id=order_id).first()
    if not order:
        return response(code=1, message='切换工单失败，该工单不存在')
    service = ServiceModel.query.filter_by(id=order.service_id).first()
    if not service:
        return response(code=1, message='切换工单失败，该工单所属服务不存在')
    HANDLER = load_handler_class(service.name)
    data = {}
    if 'release' not in session:
        session['release'] = {}
    if 'param' not in session:
        session['param'] = {}
    if 'weight' not in session:
        session['weight'] = {}

    for flow in HANDLER.Flow_Keys:
        flow = FlowModel.query.filter_by(name=flow).first()
        data[flow.name] = []
        flow_id = flow.id
        for idx, rid in enumerate(flow.releases):
            release =ReleaseModel.query.filter_by(id=rid.id).first()
            data[flow.name] = list(data[flow.name])
            data[flow.name].append(release.name)
            if idx == 0:
                session['release'][flow_id] = release.id
                session['weight'][flow_id] = {}
                session['param'][flow_id] = {}

                if flow_id not in session['release']:
                    session['release'][flow_id] = release.id
                for key, wid_list in release.weights.items():
                    if key not in session['weight'][flow_id]:
                        session['weight'][flow_id][key] = wid_list[0]
                for key, param_default in release.params.items():
                    if key not in session['param'][flow_id]:
                        session['param'][flow_id][key] = param_default

    session['order'] = (order_id, service.name)
    return response(code=0, message='切换模型成功', data=data)

@bp.route('/order/handler/infer',  methods=['GET'])
@jwt_required(refresh=True)
def infer():
    # 从订单表中获取订单信息
    #print(session['release'])
    config = {}
    for flow_id, release_id in session['release'].items():
        flow = FlowModel.query.filter_by(id=flow_id).first()
        release = ReleaseModel.query.filter_by(id=release_id).first()
        config[flow.name] = release.to_config
        for key in release.weights:
            if key not in session['weight'][flow_id]:
                return response(code=1, message=f'模型装载失败，权重选择不完整，缺少{key}')
            #print(session['weight'][key])
            weight = WeightModel.query.filter_by(id=session['weight'][flow_id][key]).first()
            config[flow.name][key] = weight.to_config
        if release.params is not None and release.params:
            if 'param' not in session or flow_id not in session['param']:
                return response(code=1, message='模型装载失败，未设置配置')
            #print(session['param'][flow_id])
            config[flow.name].update(session['param'][flow_id])

    handler = load_handler_class(session['order'][1])(config)
    # handler.field_grab(session['order'][0])
    # base = handler.origin['start_img'][0]
    log = handler.run(session['order'][0])
    # log = {
    #     'result': [{'field': 'field', 'msg': '测试1', 'type': 'warning'}],
    #     # 'origin': [{'stage': 'start_img', 'id': 0, 'base64': base}]
    # }
    print(log)
    return response(code=0, message='模型推断已完成', data=log)

@bp.route('/release/switch/<string:release_name>', methods=['POST'])
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

@bp.route('/order/weight/all/<string:release_name>', methods=['GET'])
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
    print(paramRelease, release)
    #release = ReleaseModel.query.filter_by(name=session['release']).first()
    if weightKey not in release.weights:
        return response(code=1, message='切换权重失败，权重不属于工作流主键')
    weight = WeightModel.query.filter_by(name=weightName).first()
    if weight is None:
        return response(code=1, message='切换权重失败，当前权重不存在')

    if not release.check_weight(weight):
        return response(code=1, message='切换权重失败，当前版本下该权重不可用')
    #release = ReleaseModel.query.filter_by(id=paramRelease).first()
    if 'weight' not in session:
        session['weight'] = {}
    if release.flow_id not in session['weight']:
        session['weight'][release.flow_id] = {}
    session['weight'][release.flow_id][weightKey] = weight.id
    print_cyan(f'切换成功，当前权重主键: {weightKey}，当前权重名称: {weightName}')
    return response(code=0, message='获取当前调用选中模型成功')

@bp.route('/order/weight/current', methods=['POST'])
@jwt_required(refresh=True)
def get_current_weight():
    paramRelease = request.json.get('switchParamRelease', '').strip()
    weightKey = request.json.get('currentWeightKey', None).strip()
    release = ReleaseModel.query.filter_by(name=paramRelease).first()
    print(paramRelease, release)
    wid = session['weight'][release.flow_id][weightKey]
    weight = WeightModel.query.filter_by(id=wid).first()
    data = {'weightName': weight.name if weight is not None else None}
    return response(code=0, message='获取当前调用选中模型成功', data=data)


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
    if release.flow_id not in session['param']:
        session['param'][release.flow_id] = {}

    session['param'][release.flow_id][paramName] = paramValue

    return response(code=0, message='配置修改成功')

@bp.route('/order/param/current', methods=['POST'])
@jwt_required(refresh=True)
def get_current_param():
    paramRelease = request.json.get('switchParamRelease', '').strip()
    paramName = request.json.get('currentParamName', None).strip()
    release = ReleaseModel.query.filter_by(name=paramRelease).first()
    print(session['param'], type(release.flow_id))
    data = {'argName': paramName, 'argValue':
        session['param'][release.flow_id][paramName]}
    return response(code=0, message='获取当前静态参数获取成功', data=data)

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
    #print("Formatted image input shape:", image_input.shape)  # 应该是 (1, 3, H, W)
    return image_input

# 根据Id查找信息
def get_work_orderByid(order_id,service_id):
    # 从订单表中获取订单信息
    #print_red(order_id)
    # 获取每个订单的详细信息和相关图片
    service = ServiceLogModel.query.filter_by(order_id=order_id).first()
    if not service:
        return None
    startImgs = []
    if service.start_img is not None:
        startImgs.extend(service.start_img.split(','))

    imgUrls = []
    if service.img_url is not None:
        imgUrls.extend(service.img_url.split(','))

    endImgs = []
    if service.end_img is not None:
        endImgs.extend(service.end_img.split(','))

    # 拼接最终返回的JSON数据
    data = {
        "orderId": order_id,
        "serviceId": service_id,
        ""
        "startLocation": service.start_location,
        "location": service.location,
        "endLocation": service.end_location,
        "startTime": service.start_time,
        "endTime": service.end_time,
        "startImg": startImgs,  # 返回对应的图片信息（多个图片的JSON数据）
        "imgUrl": imgUrls,
        "endImg": endImgs
    }
    #print_red(data)
    return data

# 推理图片
def infer_picture(url,model):
    resp = requests.get(url)
    img = Image.open(BytesIO(resp.content))
    img=np.array(img)
    start_time = datetime.datetime.now()
    result = model.predict_shapes(img)
    end_time = datetime.datetime.now()
    predict_drawer.load_results(result)
    resultImage = predict_drawer.draw()
    image = Image.fromarray(resultImage)
    #image.show()
    result_base64 = base64_encode_image(resultImage)

    # session['hyper']['origin_image'] = img
    # #print(session)
    # model_manager.set_model_hyper(session['hyper'])
    # start_time = datetime.datetime.now()
    # auto_labeling_result = model_manager.predict_shapes()
    # end_time = datetime.datetime.now()
    # predict_drawer.load_results(auto_labeling_result)
    # resultImage = predict_drawer.draw()
    # image = Image.fromarray(resultImage)
    # #image.show()
    # result_base64 = base64_encode_image(resultImage)
    result = {
    'originImage': url,
    'resultBase64': result_base64,
    'inferResult': predict_drawer.get_shape_dict(),
    'inferDescription': predict_drawer.description,
    'inferPeriod': (end_time - start_time).total_seconds(),
    }
    return result

# 日志回调
def on_message(message):
    print("[INFO]", message)

def base64_encode_image(image) -> str:
    buffered = BytesIO()
    image=np.array(image)
    im_base64 = Image.fromarray(image)
    im_base64.save(buffered, format="JPEG")
    img_str = base64.b64encode(buffered.getvalue()).decode('utf-8')
    return f"data:image/jpeg;base64,{img_str}"
