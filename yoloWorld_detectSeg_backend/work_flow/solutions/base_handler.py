from typing import List

import requests

from work_flow.engines import load_model_class
from database_models import WorkOrderModel, ServiceModel, ServiceLogModel,MemberModel, EmployeeModel, ExecuteModel
import requests
from PIL import Image
from io import BytesIO

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
    def __init__(self, order_id, configs, **kwargs):
        self.flows = configs
        self.fields = {}
        self.operators = {flow: {} for flow in configs}
        load_type = getattr(kwargs, 'load_type', 'follow')
        if load_type == 'once':
            for key, value in configs.items():
                self.register_flow(key)
        self.field_processing(order_id)

    def register_flow(self, flow_name):
        self.flows[flow_name] = load_model_class(flow_name)(self.flows[flow_name])

    def mapping_flow(self, flow_name):
        if flow_name not in self.flows:
            raise ValueError(f"Flow {flow_name} not found in flows")
        elif self.flows[flow_name] is dict:
            self.register_flow(flow_name)
        return self.flows[flow_name]

    def field_processing(self, order_id):
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
            for key in avatar_keys:
                self.fields['member']['avatars'].extend(split_images(getattr(member_emp, key)))
        for key in avatar_keys:
            self.fields['employee']['avatars'].extend(split_images(getattr(employee, key)))
        # 获取服务阶段图像
        for key in img_keys:
            self.fields['service_log'][key] = split_images(self.fields['service_log'][key])

    def opt_processing(self):
        pass

    def post_processing(self):
        pass