import base64
import time

import cv2
from flask import Blueprint,request,session
import requests
from flask_jwt_extended import jwt_required
from database_models import (OrderModel, ReleaseModel, ExecuteModel, WeightModel, )
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

@bp.route('/list/all')
@jwt_required(refresh=True)
def get_all_order_id():
    orders = OrderModel.query.all()
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
    order = OrderModel.query.filter_by(order_id=order_id).first()
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

@bp.route('/infer/<int:order_id>',  methods=['GET'])
@jwt_required(refresh=True)
def infer(order_id):
    # 从订单表中获取订单信息
    order = OrderModel.query.filter_by(order_id=order_id).first()
    if not order:
        return response(code=1, message='查找信息失败')
    # 获取与订单相关的图片信息
    image_sets = [image.image_set for image in order.images]  # 通过关系直接获取图片数据
    #print(image_sets)
    data= {
        "orderId": order.order_id,
        "serviceId": order.service_id,
        "orderContent": order.order_content,
        "handle": order.handle,
        "startTime": order.start_time,
        "endTime": order.end_time,
        "imageSet": image_sets  # 返回对应的图片信息（多个图片的JSON数据）
    }
    # 解析 'imageSet' 字符串
    image_set_json = data['imageSet'][0]  # 取出列表中的 JSON 字符串
    image_set = json.loads(image_set_json)  # 将 JSON 字符串解析为 Python 字典
    #将所有图片 URL 合并为一个列表
    images = image_set["pre"] + image_set["in"] + image_set["after"]
    # orderId=data['orderId']
    serviceId = data['serviceId']
    flow = ExecuteModel.query.filter_by(service_id=serviceId).first()
    # release
    release = ReleaseModel.query.filter_by(flow_id=flow.flow_id).first()
    config = release.to_config  # 用于装载模型
    session['flow'] = flow.flow_id
    session['release'] = release.id  # 装载该模型的配置
    print(session)
    model_manager.load_model_config(release)
    session['param'] = release.params
    session['weight'] = {key: wid_list[0] for key, wid_list in release.weights.items()}
    for key in release.weights:
        weight = WeightModel.query.filter_by(id=session['weight'][key]).first()
        config[key] = weight.to_config
    if release.params is not None and release.params:
        config.update(session['param'])
    release_id = session['release']
    model_manager.load_model(release_id, config)
    session['hyper'] = release.hypers

    # 存初始值
    #print(session)
    #print(f'模型装载成功')
    results=[]

    for category, image_urls in image_set.items():
        print(f"Testing category: {category}")
        for image_url in image_urls:
            print(f"Processing image: {image_url}")
            session['hyper']['origin_image'] = image_url
            #session['hyper']['mask_image'] = image_url
            model_manager.set_model_hyper(session['hyper'])
            start_time = datetime.datetime.now()
            auto_labeling_result = model_manager.predict_shapes()
            end_time = datetime.datetime.now()
            predict_drawer.load_results(auto_labeling_result)
            resultImage = predict_drawer.draw()
            image = Image.fromarray(resultImage)
            image.show()
            result_base64 = base64_encode_image(resultImage)
            result = {
                'resultBase64': 123456,
                'inferResult': image_url,
                'inferDescription': predict_drawer.description,
                'inferPeriod': end_time,
            }
            #print(data['inferDescription'])
            results.append(result)
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