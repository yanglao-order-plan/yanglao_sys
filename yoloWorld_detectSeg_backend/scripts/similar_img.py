import json
import logging
import urllib.parse
from io import BytesIO

import cv2
import numpy as np
# encoding:utf-8

import requests
import base64

from PIL import Image

from database_using import *
from work_flow.flows.ppocr_v4_lama import PPOCRv4LAMA

'''
相似图检索—入库
'''
max_size_kbs = 3 * 1024  # 最大尺寸限制，转换为字节（3MB）
compress_save_path = 'E:\GitHub\yanglao_sys\yoloWorld_detectSeg_backend\scripts/compress_save.jpg'

# 图像压缩逻辑
def pic_compress(img_cv, current_size, quality=90, step=5, pic_type='.jpeg'):
    # 读取图片bytes
    print("图片压缩前的大小为(KB)：", current_size)
    pic_byte = cv2.imencode(pic_type, img_cv, [int(cv2.IMWRITE_JPEG_QUALITY), quality])[1]
    while current_size > max_size_kbs:
        pic_byte = cv2.imencode(pic_type, img_cv, [int(cv2.IMWRITE_JPEG_QUALITY), quality])[1]
        if quality - step < 0:
            break
        quality -= step
        current_size = len(pic_byte) / 1024
    print("图片压缩后的大小为(KB)：", current_size, "压缩质量为：", quality)
    pic_base64 = base64.b64encode(pic_byte.tobytes()).decode('utf-8')
    print(f"Base64编码后的大小: {len(pic_base64) / 1024:.2f} KB")
    return pic_base64

class Service_stage():
    start_service = "start_img"
    servicing = "img_url"
    end_service = "end_img"

# 读取 JSON 文件
with open('E:\GitHub\yanglao_sys\yoloWorld_detectSeg_backend\scripts\model_config.json', 'r', encoding='utf-8') as f:
    model_config = json.load(f)

API_KEY = "gwcTSOuEW0M07fMSNb7I62sV"
SECRET_KEY = "d75FG1eqS0XL025pbyX5gRf1R20MriGi"
access_token = ''
model = PPOCRv4LAMA(model_config, logging.info)

def img_url_to_np(img_url):
    '''
    将图片 URL 转换为 NumPy 数组
    '''
    response = requests.get(img_url)
    if response.status_code == 200:
        # 使用 OpenCV 读取图片并转换为 NumPy 数组
        img = np.array(bytearray(response.content), dtype=np.uint8)
        img = cv2.imdecode(img, cv2.IMREAD_COLOR)  # 解码为图片格式
        size = img.nbytes / 1024  # 当前图片大小（KB）
        return img, size
    else:
        raise Exception(f"Failed to fetch image from URL: {img_url}")

def base64_to_np(base64_str):
    '''
    将 base64 字符串转换为 NumPy 数组
    '''
    img_bytes = base64.b64decode(base64_str)
    img = cv2.imdecode(np.frombuffer(img_bytes, np.uint8), cv2.IMREAD_COLOR)
    return img

def np_to_url(np_image):
    '''
    将处理后的 NumPy 图像转换为可以上传的图片格式
    这里将图像转为 base64 格式
    '''
    _, img_encoded = cv2.imencode('.jpeg', np_image)  # 将图片编码为 JPEG 格式
    img_base64_str = base64.b64encode(img_encoded.tobytes()).decode('utf-8')  # 编码为 base64 字符串
    # img_base64_byte = base64.b64decode(img_encoded)
    # url = urllib.parse.quote(img_base64_byte)
    return img_base64_str

def handle_before_add(img_url):
    img_np, size = img_url_to_np(img_url)
    processed_img = model.predict_shapes(img_np).image
    # if size > max_size_kbs:
    #     return pic_compress(processed_img, size)
    # else:
    return np_to_url(processed_img)

def add_img_by_url(img_url, service_id, order_id, stage, start_time):
    '''
    相似图检索—url添加
    '''
    request_url = "https://aip.baidubce.com/rest/2.0/image-classify/v1/realtime_search/similar/add"

    # 二进制方式打开图片文件
    # f = open('[本地文件]', 'rb')
    # img = base64.b64encode(f.read())
    new_base64 = handle_before_add(img_url)
    params = {"brief": "{\"service_id\": " + service_id +
                       ", \"order_id\":" + order_id +
                       ", \"img_url\": " + img_url +
                       ", \"service_stage\": " + stage +
                       ", \"start_time\": " + start_time + "}",
              "image": new_base64,
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
    start_data = '2024-03-01 00:00:00'
    end_data = '2024-04-30 23:59:59'

    # img_url = "http://www.mcwajyfw.com/imagemc/202403/20240330/3/10/1f1c0e280a7946e2a27b627ed8f286d11711794182670.jpeg"
    service_id = 406
    # order_id = 541973
    start_order_id = 445209

    satge_to_add = Service_stage.servicing
    main()
    urls_all = get_img_urls(service_id, [satge_to_add], start_data, end_data, start_order_id)
    for item in urls_all.keys():
        for url in urls_all[item]:
            add_img_by_url(url, str(service_id), str(item[0]), satge_to_add, item[1])

    # search_img()

