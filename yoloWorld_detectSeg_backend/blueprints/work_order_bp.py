import base64
import time
import cv2
from flask import Blueprint,request,session
import requests
from flask_jwt_extended import jwt_required
from database_models import (WorkOrderModel, ReleaseModel, ExecuteModel, WeightModel, ServiceModel, ServiceLogModel, )
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

@bp.route('/list', methods=['GET'])
@jwt_required(refresh=True)
def get_all_order_id():
    page = int(request.args.get('currentPage', 1))  # 获取页码，默认为第一页
    per_page = int(request.args.get('size', 10))  # 获取每页显示的数据量，默认为 10 条
    pagination  = WorkOrderModel.query.paginate(page=page, per_page=per_page, error_out=False)  # 使用 paginate() 方法进行分页查询，不抛出异常
    orders = pagination.items
    total = pagination.total  # 获取总数据量
    #orders=WorkOrderModel.query.filter_by(id=4882).all()
    data = {"list": [],"total":[] }
    for order in orders:
        service = get_work_orderByid(order.id, order.service_id)
        if service is not None:
            order_data = {
                "orderId": order.id,
                "no": order.no,
                "serviceId": order.service_id,
                "projectType": order.project_type,
            }
            data['list'].append(order_data)
        else:
            total-=1
    data['total'] = total
    return response(code=1, message='查找work_order成功', data=data)


@bp.route('/infer/<int:order_id>',  methods=['GET'])
@jwt_required(refresh=True)
def infer(order_id):
    # 从订单表中获取订单信息
    service_id=WorkOrderModel.query.filter_by(id=order_id).first().service_id
    data = get_work_orderByid(order_id,service_id)
    serviceId = data['serviceId']
    #flow = ExecuteModel.query.filter_by(service_id=serviceId).first()
    flow=64
    # if flow is None:
    #     return response(code=0, message='未配置该服务类型执行的flow')
    # release
    release = ReleaseModel.query.filter_by(flow_id=flow).first()
    config = release.to_config  # 用于装载模型
    #session['flow'] = flow.flow_id
    session['flow'] =flow
    session['release'] = release.id  # 装载该模型的配置
    #print(session)
    #model_manager.load_model_config(release)
    session['param'] = release.params
    session['weight'] = {key: wid_list[0] for key, wid_list in release.weights.items()}
    for key in release.weights:
        weight = WeightModel.query.filter_by(id=session['weight'][key]).first()
        config[key] = weight.to_config
    if release.params is not None and release.params:
        config.update(session['param'])
    release_id = session['release']
    #model_manager.load_model(release_id, config)
    #session['hyper'] = release.hypers
    model=PPOCRv4LAMA(config,on_message)

    # 存初始值
    #print(session)
    #print(f'模型装载成功')
    results={"startImg": [], "imgUrl": [],"endImg":[]}
    start_img=data['startImg']
    for url in start_img:
        result=infer_picture(url,model)
        results["startImg"].append(result)
    img_url=data['imgUrl']
    for url in img_url:
        result=infer_picture(url,model)
        results["imgUrl"].append(result)
    end_img=data['endImg']
    for url in end_img:
        result=infer_picture(url,model)
        results["endImg"].append(result)

    return response(code=0, message='模型推断已完成', data=results)

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
