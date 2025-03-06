import base64
import json
import logging
import os.path
from datetime import datetime
from typing import List

import cv2
import numpy as np
import requests
from geopy import Nominatim
from sqlalchemy import desc

from work_flow.engines import load_model_class
from database_models import WorkOrderModel, ServiceModel, ServiceLogModel,MemberModel, EmployeeModel, ExecuteModel
import requests
from PIL import Image
from io import BytesIO


def get_access_token(API_KEY, SECRET_KEY):
    """
    使用 AK，SK 生成鉴权签名（Access Token）
    :return: access_token，或是None(如果错误)
    """
    url = "https://aip.baidubce.com/oauth/2.0/token"
    params = {"grant_type": "client_credentials", "client_id": API_KEY, "client_secret": SECRET_KEY}
    return str(requests.post(url, params=params).json().get("access_token"))

# 获取地址的经纬度范围
def get_address_bounds(address):
    geolocator = Nominatim(user_agent="geoapiExercises")

    location = geolocator.geocode(address)
    if location:
        latitude = location.latitude
        longitude = location.longitude

        # 返回一个包含经纬度的元组
        # 这里我们可以假设返回的是一个简单的点，不涉及精确的矩形范围
        return latitude, longitude
    else:
        print(f"无法找到地址: {address}")
        return None


# 判断给定经纬度是否在范围内
def is_point_in_area(bounds, location):
    min_lat, max_lat, min_lon, max_lon = bounds
    latitude, longitude = location
    # 检查给定的经纬度是否在边界框内
    return min_lat <= latitude <= max_lat and min_lon <= longitude <= max_lon

def split_images(field: str)->List:
    # 将 field 字符串按分号分割成 URL 列表
    if field is None or not field:
        return []
    urls = field.split(',')
    images = []
    for url in urls:
        try:
            # 从 URL 下载图片
            response = requests.get(url)
            response.raise_for_status()  # 如果请求失败会抛出异常
            # 将下载的内容转化为图片
            img = Image.open(BytesIO(response.content))
            img = np.array(img)
            img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
            images.append(img)  # 添加到图片列表
        except Exception as e:
            print(f"Error downloading or processing image from {url}: {e}")
    return images

def get_url_image(url: str):
    response = requests.get(url)
    response.raise_for_status()
    img = Image.open(BytesIO(response.content))
    img = np.array(img)
    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    return img


def base64_encode_image(image) -> str:
    buffered = BytesIO()
    image=np.array(image)
    im_base64 = Image.fromarray(image)
    im_base64.save(buffered, format="JPEG")
    img_str = base64.b64encode(buffered.getvalue()).decode('utf-8')
    return f"data:image/jpeg;base64,{img_str}"

class LogItem:
    def __init__(self, msg, type, avatars=[]):
        self.msg = msg
        self.type = type
        self.avatars = avatars

    def get_dict(self, key):
        # avatars = [base64_encode_image(avatar) for avatar in self.avatars]
        return {'field': key, 'msg': self.msg, 'type': self.type, 'avatars': self.base_avatars}

    def save_avatar(self, avatar, path):
        if isinstance(avatar, str):
            img = get_url_image(avatar)
        elif isinstance(avatar, np.ndarray):
            img = avatar
        else:
            raise ValueError(f"Invalid avatar type: {type(avatar)}")
        cv2.imwrite(path, img)

    def save(self, path):
        # 创建路径文件夹
        os.makedirs(path, exist_ok=True)

        # 保存msg为txt文件
        msg_file_path = os.path.join(path, "log.json")
        # with open(msg_file_path, 'w') as f:
        #     f.write(self.msg)

        with open(msg_file_path, 'w', encoding='utf-8') as f:
            json.dump({'msg': self.msg, 'type': self.type}, f, ensure_ascii=False, indent=4)

        # 创建avatars文件夹
        avatars_folder = os.path.join(path, 'avatars')
        os.makedirs(avatars_folder, exist_ok=True)
        # local_avatars = []
        base_avatars = []
        # 遍历avatars并处理图片和附加信息
        for i, avatar in enumerate(self.avatars):
            if isinstance(avatar, tuple) and len(avatar) == 2:
                img, info = avatar
                # 如果是元组，则第一个元素是图片，第二个是附加信息
                avatar_folder = os.path.join(avatars_folder, f"{i + 1}")
                os.makedirs(avatar_folder, exist_ok=True)
                avatar_file_path = os.path.join(avatars_folder, f"{i + 1}.jpeg")
                self.save_avatar(img, avatar_file_path)
                # 保存附加信息
                with open(os.path.join(avatar_folder, "info.txt"), 'w') as f:
                    f.write(str(info))
            else:
                # 如果是单一图片，直接保存
                avatar_file_path = os.path.join(avatars_folder, f"{i + 1}.jpeg")
                self.save_avatar(avatar, avatar_file_path)
            base_avatars.append(base64_encode_image(img))

        self.base_avatars = base_avatars


class BaseHandler:
    local_order_addr = 'E:\Datasets\exception order'
    local_saver = "E:\Datasets\order_handle_result"
    request_url = "https://aip.baidubce.com/rest/2.0/image-classify/v1/realtime_search/similar/search"
    API_KEY = "gwcTSOuEW0M07fMSNb7I62sV"
    SECRET_KEY = "d75FG1eqS0XL025pbyX5gRf1R20MriGi"
    access_token = get_access_token(API_KEY, SECRET_KEY)
    time_format = "%Y-%m-%d %H:%M:%S"
    avatar_keys = ['document_photo', 'front_card', 'reverse_card', 'me_photo']
    img_keys = ['start_img', 'middle_img', 'end_img']
    out_keys = ['start_img', 'img_url', 'end_img']
    est_keys = ['field', 'operator', 'estimate']
    Registered_Fields = {
        'service': ['name', 'start_img_num', 'middle_img_num', 'end_img_num', 'service_frequency_day'],
        'order': ['project_type', 'order_content', 'order_area_code', 'order_area_name'],
        'service_log': [
                        'start_content', 'start_img', 'start_location', 'start_coordinate',
                        'middle_content', 'middle_img', 'middle_location', 'middle_coordinate',
                        'end_content', 'end_img', 'end_location', 'end_coordinate',
                       ],
        'member': ['id', 'name', 'type', 'emp_id'],
        'employee': ['id', 'name'],
    }
    hasEmpAvatar = False
    hasMebAvatar = False
    sim_thresh = 0.8
    def __init__(self, configs, **kwargs):
        self.flows = configs
        self.fields = {}
        self.log = {}
        self.origin = {}
        self.operators = {stage: [] for stage in self.img_keys}
        load_type = getattr(kwargs, 'load_type', 'follow')
        if load_type == 'once':
            for key, value in configs.items():
                self.register_flow(key)

    def register_flow(self, flow_name):
        self.flows[flow_name] = load_model_class(flow_name)(self.flows[flow_name], logging.info)

    def mapping_flow(self, flow_name):
        if flow_name not in self.flows:
            raise ValueError(f"Flow {flow_name} not found in flows")
        elif type(self.flows[flow_name]) == dict:
            self.register_flow(flow_name)
        return self.flows[flow_name]

    def get_local_image(self, path):
        # 定义常见图片文件扩展名
        image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.webp'}

        # 创建一个列表，用来存储图片文件的元组
        image_files = []

        # 遍历目录中的文件
        for file_name in os.listdir(path):
            # 获取文件的完整路径
            file_path = os.path.join(path, file_name)
            # 判断文件是否为文件且具有有效的图片扩展名
            if os.path.isfile(file_path) and os.path.splitext(file_name)[1].lower() in image_extensions:
                # 去除文件扩展名
                file_base_name = os.path.splitext(file_name)[0]
                # 将图片名称（去扩展名）和路径作为元组添加到列表中
                img = cv2.imread(file_path)
                image_files.append([img, file_base_name])

        return image_files

    def field_grab(self, order_id):
        os.makedirs(self.this_order_path, exist_ok=True)  # 创建本地保存路径

        local_order_path = os.path.join(self.local_order_addr, str(order_id))
        if not os.path.exists(local_order_path):
            print(10000)
            raise ValueError(f"Order {order_id} not exists in local saver")

        # 获取orm对象
        order = WorkOrderModel.query.get(order_id)
        employee_id = order.handler if order.handler == order.to_user else order.to_user
        service = ServiceModel.query.get(order.service_id)
        member = MemberModel.query.get(order.member_id)
        employee = EmployeeModel.query.get(employee_id)
        service_log = ServiceLogModel.query.filter(ServiceLogModel.order_id==order_id).first()
        # 基本信息获取
        self.fields['service'] = service.to_dict(self.Registered_Fields['service'])
        self.fields['order'] = order.to_dict(self.Registered_Fields['order'])
        self.fields['service_log'] = service_log.to_dict(self.Registered_Fields['service_log'])
        self.fields['member'] = member.to_dict(self.Registered_Fields['member'])
        self.fields['employee'] = employee.to_dict(self.Registered_Fields['employee'])
        self.fields['employee']['avatars'] = []
        self.fields['member']['avatars'] = []
        # 服务对象可能同时为系统中的注册服务者
        if self.fields['member']['emp_id'] is not None: # 若服务对象同时也是系统中的注册服务者
            self.fields['member']['avatars'] = []
            member_emp = EmployeeModel.query.get(member.emp_id)
            for key in self.avatar_keys:
                self.fields['member']['avatars'].extend(split_images(getattr(member_emp, key)))
            if len(self.fields['member']['avatars']) > 0:
                self.hasMebAvatar = True
        for key in self.avatar_keys:
            self.fields['employee']['avatars'].extend(split_images(getattr(employee, key)))
        if len(self.fields['employee']['avatars']) > 0:
            self.hasEmpAvatar = True

        # 获取服务阶段图像
        origin_path = os.path.join(self.this_order_path, "origin")
        for key in self.img_keys:
            os.makedirs(os.path.join(origin_path, key), exist_ok=True)
            # 读取本地预存图片
            key_img_path = os.path.join(local_order_path, key)
            # self.fields['service_log'][key] = split_images(self.fields['service_log'][key])
            self.fields['service_log'][key] = self.get_local_image(key_img_path)
            self.origin[key] = []
            for idx, item in enumerate(self.fields['service_log'][key]):
                img = item[0]
                local_path = os.path.join(origin_path, key, f"{idx}.jpeg")
                cv2.imwrite(local_path, img.astype(np.uint8))
                print(f"Save image to {local_path}")  # 本地路径base64化
                cvt_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                self.origin[key].append(base64_encode_image(cvt_img.astype(np.uint8)))
            self.operators[key].append({})

        self.origin['img_url'] = self.origin['middle_img']
        del self.origin['middle_img']

    def location_field(self, now_coordinate, target_location):
        bounds = get_address_bounds(target_location)
        return is_point_in_area(bounds, now_coordinate)

    def his_similar(self, img):
        '''
        相似图检索—检索
        '''
        request_url = "https://aip.baidubce.com/rest/2.0/image-classify/v1/realtime_search/similar/search"
        access_token = ''
        params = {"image": img, "pn": 200, "rn": 100}
        request_url = request_url + "?access_token=" + access_token
        headers = {'content-type': 'application/x-www-form-urlencoded'}
        response = requests.post(request_url, data=params, headers=headers)
        if response:
            results = response.json()
            sim_urls = []
            for result in results['result']:
                if result['score'] >= self.sim_thresh:
                    sim_urls.append(result['brief']['img_url'])
        else:
            return False

    def field_processing(self):
        self.log['field'] = []
        # 阶段位置
        # target_location = self.fields['order']['order_area_name']
        if self.fields['service_log']['start_location'] != self.fields['member']['area_name']:
            self.log['field'].append(LogItem("服务开始时，定位不在目标地址中", 'error'))
        if self.fields['service_log']['start_location'] != self.fields['member']['area_name']:
            self.log['field'].append(LogItem("服务进行时，定位不在目标地址中", 'error'))
        if self.fields['service_log']['start_location'] != self.fields['member']['area_name']:
            self.log['field'].append(LogItem("服务结束时，定位不在目标地址中", 'error'))
        # 记录数量
        for key in self.img_keys:
            this = f"{key}_num"
            min_num = self.fields['service'][this][0]
            max_num = self.fields['service'][this][1]
            num = len(self.fields['service_log'][key])
            if num < min_num or num > max_num:
                self.log['field'].append(LogItem(f"服务阶段{key} 记录数量: {num}不符合规定", 'error'))

        # 服务时长
        this_start_time = datetime.strptime(self.fields['service_log']['start_time'], self.time_format)
        this_end_time = datetime.strptime(self.fields['service_log']['end_time'], self.time_format)
        time_diff = (this_end_time - this_start_time).total_seconds() / 60
        if time_diff < self.fields['service']['least_service_duration']:
            self.log['field'].append(LogItem(f"服务时长{time_diff}（分钟）不符合规定", 'error'))

        # 服务频次
        early_date_time = datetime.combine(this_start_time.date(), datetime.min.time())
        early_date_time_str = early_date_time.strftime(self.time_format)
        emp_his_orders = (WorkOrderModel.query
                          .filter(WorkOrderModel.handler==self.fields['employee']['id'])
                          .filter(WorkOrderModel.start_time < early_date_time_str)
                          .order_by(desc(WorkOrderModel.start_time)))

        same_day_num = 0
        cross_order_ids = []
        orign_time = (this_start_time, this_end_time)
        this_time = (this_start_time, this_end_time)
        for order in emp_his_orders:
            now_service_log = ServiceLogModel.query.filter(ServiceLogModel.order_id == order.id).first()

            now_time = (datetime.strptime(now_service_log.start_time, self.time_format),
                        datetime.strptime(now_service_log.end_time, self.time_format))
            if now_time[0].date() != this_time[0].date():
                break
            if orign_time[0] < now_time[1]:
                cross_order_ids.append(order.id)
            this_time = now_time
            same_day_num += 1

        if same_day_num > self.fields['service']['service_frequency_day']:
            self.log['field'].append(LogItem(f"日期{this_start_time.date()}"
                                             f"服务次数{same_day_num} 超过服务类型{self.fields['service']['name']} "
                                             f"规定{self.fields['service']['service_frequency_day']}", 'error'))
        if not cross_order_ids:
            self.log['field'].append(LogItem(f"服务者{self.fields['employee']['name']} 日期{this_start_time.date()}"
                                             f"存在工单集{cross_order_ids} 未在本工单开始时间{orign_time}之前结束", 'error'))

    def load_local_estimate(self):
        handle_path = os.path.join(self.this_order_path, 'handle')
        origin_path = os.path.join(self.this_order_path, 'origin')

        for key in os.listdir(origin_path):
            key_origin_path = os.path.join(origin_path, key)
            local_images = self.get_local_image(key_origin_path)
            self.origin[key] = []
            for img, _ in local_images:
                cvt_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                self.origin[key].append(base64_encode_image(cvt_img.astype(np.uint8)))

        self.origin['img_url'] = self.origin['middle_img']
        del self.origin['middle_img']

        for key in os.listdir(handle_path):
            self.log[key] = []
            key_handle_path = os.path.join(handle_path, key)
            for dir in os.listdir(key_handle_path):
                this_log_path = os.path.join(key_handle_path, dir, 'log.json')
                with open(this_log_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)  # 使用json.load读取数据
                this_avatar_path = os.path.join(key_handle_path, dir, 'avatars')
                msg = data.get('msg', "")
                type = data.get('type', "")
                avatars = self.get_local_image(this_avatar_path)
                self.log[key].append(LogItem(msg, type, avatars))


    def opt_processing(self):
        self.log['operator'] = []
        pass

    def post_processing(self):
        self.log['estimate'] = []
        pass

    def run(self, order_id, **kwargs):
        self.this_order_path = os.path.join(self.local_saver, str(order_id))
        if os.path.exists(self.this_order_path):
            self.load_local_estimate()
        else:
            self.field_grab(order_id)
            self.field_processing()
            self.opt_processing()
            self.post_processing()
        result = {}
        result['origin'] = []
        for key in self.out_keys:
            info = self.origin[key]
            this_info = {'stage': key, "url": []}
            for idx, item in enumerate(info):
                this_info['url'].append(item)
            result['origin'].append(this_info)

        result['result'] = []
        print(self.log.keys())
        for key in self.est_keys:
            value = self.log[key]
            for id, item in enumerate(value):
                item.save(os.path.join(self.this_order_path, 'handle', key, str(id))) # 先保存后传输，将avatar转成本地保存路径
                result['result'].append(item.get_dict(key))

        return result