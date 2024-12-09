import base64
from typing import List

import numpy as np
import requests
from geopy import Nominatim

from work_flow.engines import load_model_class
from database_models import WorkOrderModel, ServiceModel, ServiceLogModel,MemberModel, EmployeeModel, ExecuteModel
import requests
from PIL import Image
from io import BytesIO

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
    if field is None:
        return []
    urls = field.split(';')
    images = []
    for url in urls:
        try:
            # 从 URL 下载图片
            response = requests.get(url)
            response.raise_for_status()  # 如果请求失败会抛出异常
            # 将下载的内容转化为图片
            img = Image.open(BytesIO(response.content))
            images.append(img)  # 添加到图片列表
        except Exception as e:
            print(f"Error downloading or processing image from {url}: {e}")

    return images

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

    def get_dict(self):
        avatars = [base64_encode_image(avatar) for avatar in self.avatars]
        return {'msg': self.msg, 'type':self.type ,'avatars': avatars}

class BaseHandler:
    avatar_keys = ['document_photo', 'front_card', 'reverse_card', 'me_photo']
    img_keys = ['start_img', 'middle_img', 'end_img']
    Registered_Fields = {
        'service': ['name', 'start_img_num', 'service_img_num', 'end_img_num'],
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
        self.operators = {stage: [] for stage in self.img_keys}
        load_type = getattr(kwargs, 'load_type', 'follow')
        if load_type == 'once':
            for key, value in configs.items():
                self.register_flow(key)

    def register_flow(self, flow_name):
        self.flows[flow_name] = load_model_class(flow_name)(self.flows[flow_name])

    def mapping_flow(self, flow_name):
        if flow_name not in self.flows:
            raise ValueError(f"Flow {flow_name} not found in flows")
        elif self.flows[flow_name] is dict:
            self.register_flow(flow_name)
        return self.flows[flow_name]

    def field_grab(self, order_id):
        # 获取orm对象
        order = WorkOrderModel.query.get(order_id)
        employee_id = order.handler if order.handler == order.to_user else order.to_user
        service = ServiceModel.query.get(order.service_id)
        member = MemberModel.query.get(order.member_id)
        employee = EmployeeModel.query.get(employee_id)
        service_log = ServiceLogModel.query.get(order_id=order_id)
        # 基本信息获取
        self.fields['service'] = service.to_dict(self.Registered_Fields['service'])
        self.fields['order'] = order.to_dict(self.Registered_Fields['order'])
        self.fields['service_log'] = service_log.to_dict(self.Registered_Fields['service_log'])
        self.fields['member'] = member.to_dict(self.Registered_Fields['member'])
        self.fields['employee'] = employee.to_dict(self.Registered_Fields['employee'])

        # 服务对象可能同时为系统中的注册服务者
        if self.fields['member']['emp_id'] is not None: # 若服务对象同时也是系统中的注册服务者
            self.fields['member']['avatars'] = []
            member_emp = EmployeeModel.query.get(member.emp_id)
            for key in self.avatar_keys:
                self.fields['member']['avatars'].extend(split_images(getattr(member_emp, key)))
        for key in self.avatar_keys:
            self.fields['employee']['avatars'].extend(split_images(getattr(employee, key)))
        # 获取服务阶段图像
        for key in self.img_keys:
            self.fields['service_log'][key] = split_images(self.fields['service_log'][key])
            self.operators[key].append({})

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
        target_location = self.fields['order']['order_area_name']
        near_start = self.location_field(self.fields['service_log']['start_coordinate'],
                                         target_location)
        near_middle = self.location_field(self.fields['service_log']['middle_coordinate'],
                                         target_location)
        near_end = self.location_field(self.fields['service_log']['end_coordinate'],
                                         target_location)
        if not near_start:
            self.log['field'].append(LogItem("服务开始时，定位不在目标地址中", 'error'))
        if not near_middle:
            self.log['field'].append(LogItem("服务进行时，定位不在目标地址中", 'error'))
        if not near_end:
            self.log['field'].append(LogItem("服务结束时，定位不在目标地址中", 'error'))


    def opt_processing(self):
        self.log['opterator'] = []
        pass

    def post_processing(self):
        self.log['estimate'] = []
        pass

    def run(self, order_id, **kwargs):
        self.field_grab(order_id)
        self.field_processing()
        self.opt_processing()
        self.post_processing()
        return self.log
