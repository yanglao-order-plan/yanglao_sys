import json
import logging
import urllib.parse
import cv2
import numpy as np
# encoding:utf-8

import requests
import base64
from database_using import *
from work_flow.flows.ppocr_v4_lama import PPOCRv4LAMA

'''
相似图检索—入库
'''


class Service_stage():
    start_service = "start_img"
    servicing = "img_url"
    end_service = "end_img"

# 读取 JSON 文件
with open('E:\GitHub\yanglao_sys\yoloWorld_detectSeg_backend\scripts\model_config.json', 'r', encoding='utf-8') as f:
    model_config = json.load(f)

API_KEY = "gwcTSOuEW0M07fMSNb7I62sV"
SECRET_KEY = "jQvVqWZJhvQx0DgOQQjcCuQVzvxU3ebt"
access_token = ''
model = PPOCRv4LAMA(model_config, logging.info)

def img_url_to_np(img_url):
    '''
    将图片 URL 转换为 NumPy 数组
    '''
    response = requests.get(img_url)
    print(img_url)
    if response.status_code == 200:
        # 使用 OpenCV 读取图片并转换为 NumPy 数组
        img = np.array(bytearray(response.content), dtype=np.uint8)
        img = cv2.imdecode(img, cv2.IMREAD_COLOR)  # 解码为图片格式
        return img
    else:
        raise Exception(f"Failed to fetch image from URL: {img_url}")


def np_to_url(np_image):
    '''
    将处理后的 NumPy 图像转换为可以上传的图片格式
    这里将图像转为 base64 格式
    '''
    _, img_encoded = cv2.imencode('.jpg', np_image)  # 将图片编码为 JPEG 格式
    img_base64_str = base64.b64encode(img_encoded).decode('utf-8')  # 编码为 base64 字符串
    # img_base64_byte = base64.b64decode(img_encoded)
    # url = urllib.parse.quote(img_base64_byte)
    return img_base64_str

def handle_before_add(img_url):
    img_np = img_url_to_np(img_url)
    processed_img = model.predict_shapes(img_np).image
    url = np_to_url(processed_img)
    return url

def add_img_by_url(img_url, service_id, order_id, stage, start_time):
    '''
    相似图检索—url添加
    '''
    request_url = "https://aip.baidubce.com/rest/2.0/image-classify/v1/realtime_search/similar/add"

    # 二进制方式打开图片文件
    # f = open('[本地文件]', 'rb')
    # img = base64.b64encode(f.read())
    # new_img_url = handle_before_add(img_url)
    params = {"brief": "{\"service_id\": " + service_id +
                       ", \"order_id\":" + order_id +
                       ", \"img_url\": " + img_url +
                       ", \"service_stage\": " + stage +
                       ", \"start_time\": " + start_time + "}",
              "url": img_url,
              "tags": f"{service_id}",
              }
    request_url = request_url + "?access_token=" + access_token
    headers = {'content-type': 'application/x-www-form-urlencoded'}
    response = requests.post(request_url, data=params, headers=headers)
    if response:
        print(response.json())

def search_img():
    '''
    相似图检索—检索
    '''

    request_url = "https://aip.baidubce.com/rest/2.0/image-classify/v1/realtime_search/similar/search"
    # 二进制方式打开图片文件
    f = open(r'E:\test\download\541862\img_url\82b1e93c1ab94cb5b900ac095a5250f51712806500880.jpeg', 'rb')
    img = base64.b64encode(f.read())

    params = {"image": img, "pn": 200, "rn": 100}
    request_url = request_url + "?access_token=" + access_token
    headers = {'content-type': 'application/x-www-form-urlencoded'}
    response = requests.post(request_url, data=params, headers=headers)
    if response:
        print(response.json())

def get_access_token():
    """
    使用 AK，SK 生成鉴权签名（Access Token）
    :return: access_token，或是None(如果错误)
    """
    url = "https://aip.baidubce.com/oauth/2.0/token"
    params = {"grant_type": "client_credentials", "client_id": API_KEY, "client_secret": SECRET_KEY}
    return str(requests.post(url, params=params).json().get("access_token"))

def main():
    global access_token
    access_token = get_access_token()


if __name__ == '__main__':
    start_data = '2024-3-1'
    end_data = '2024-3-30'

    # img_url = "http://www.mcwajyfw.com/imagemc/202403/20240330/3/10/1f1c0e280a7946e2a27b627ed8f286d11711794182670.jpeg"
    service_id = 406
    # order_id = 541973


    satge_to_add = Service_stage.servicing
    main()
    urls_all = get_img_urls(service_id, [satge_to_add], start_data, end_data)
    for item in urls_all.keys():
        for url in urls_all[item]:
            add_img_by_url(url, str(service_id), str(item[0]), satge_to_add, item[1])

    # search_img()

