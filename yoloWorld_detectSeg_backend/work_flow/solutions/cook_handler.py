import base64
import re
from datetime import datetime
from io import BytesIO

import cv2
import numpy as np
import requests
from PIL import Image

from work_flow.flows.pixel_analysis import PixelAnalysis
from work_flow.solutions.base_handler import BaseHandler, LogItem
from work_flow.utils.image import crop_polygon_object

def time_format(time_str, format="%Y-%m-%d %H:%M:%S"):
    datetime.strptime(time_str, format)

def is_all_true(d):
    # 遍历字典中的每个键值对
    for value in d.values():
        if isinstance(value, dict):  # 如果值是字典，递归判断
            if not is_all_true(value):
                return False
        elif not value:  # 如果值为 False（0、None、False 等）
            return False
    return True

mark_time_format = "%Y-%m-%d%H:%M:%S"
special_thresh_for_dino = {
    'door': 0.4,
    'person': 0.65,
    'food': 0.5,
    'ingredient': 0.5,
    'cookware': 0.45,
    'dinnerware': 0.45,
    'paper receipt': 0.65
}
class CookHandler(BaseHandler):
    sim_score = 0.8
    Flow_Keys = ['grounding_dino', 'ppocr_v4_lama', 'yolov6_face', 'arcface', 'cbiaformer_cls', "deit_cls"]  # 注册工作流
    pixelanalysis = PixelAnalysis()
    Registered_Text_Prompts = { # grounding_dino动态配置
        'start_img': {
            'door': ['open door'],
            'person':['person'],
            'cookware': ['cookware', 'pot', 'turner', 'rice cooker'],  # 厨具
            # 'food': ['food'],
            # 'ingredient': ['ingredient'],
        },
        'middle_img': {
            'person': ['person', 'hand', 'arm'],
            'cookware': ['cookware'], # 厨具
            'dinnerware': ['dinnerware'], # 餐具
            'food': ['food'],
            'ingredient': ['ingredient'],
        },
        'end_img': {
            'person': ['person'],
            'dinnerware': ['dinnerware'],  # 吃饭相关道具
            # 'food': ['food'],
            # 'ingredient': ['ingredient'],
            'paper receipt': ['receipt made by paper'] # 回执单
        }
    }
    Enhanced_Keys = ['ingredient', 'food']
    Registered_OCR_Format = {
        '姓名账号': '[\u4e00-\u9fa5]{2,5}/\d{11}',
        '身份证号': '\d{18}',
        '版本号': '\d+\.\d+\.\d+',
        '手机时间': '\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}'
    }
    def __init__(self, configs, **kwargs):
        super().__init__(configs, **kwargs)


    def opt_processing(self):
        super().opt_processing()
        # 文字水印提取+消除
        self.operators['ppocr_v4_lama'] = {}
        for stage in self.img_keys:
            self.operators['ppocr_v4_lama'][stage] = {}
            for id, img in enumerate(self.fields['service_log'][stage]):
                print(f'water mark remove and extract Processing {stage} image {id}')
                results = self.mapping_flow('ppocr_v4_lama').predict_shapes(img)
                if stage == 'middle_img':
                    # 重复图像
                    _, img_encoded = cv2.imencode('.jpeg', results.image)  # 将图片编码为 JPEG 格式
                    img_base64_str = base64.b64encode(img_encoded.tobytes()).decode('utf-8')  # 编码为 base64 字符串
                    params = {"image": img_base64_str, "pn": 200, "rn": 100}
                    request_url = self.request_url + "?access_token=" + self.access_token
                    headers = {'content-type': 'application/x-www-form-urlencoded'}
                    response = requests.post(request_url, data=params, headers=headers)
                    sim_containers = []
                    print(response.json())
                    for result in response.json()['result']:
                        if result['score'] >= self.sim_score:
                            order_id = result['score']['brief']['order_id']
                            img_url = result['score']['brief']['img_url']
                            sim_containers.append((order_id, img_url))
                    if not sim_containers:
                        self.log['opterator'].append(LogItem(f"工作流 相似图像数据库 阶段: {stage} 图像id: {id} 识别到相似图片",
                                                             'warning', avatars=sim_containers))
                    # 网图识别
                    online_result = self.pixelanalysis.predict_shapes(results.image, mode='saturation')
                    if online_result.shapes[0].label:
                        self.log['opterator'].append(
                            LogItem(f"工作流 网图识别 阶段: {stage} 图像id: {id} {online_result.description}",
                                    'warning'))

                if results.description is not None:
                    self.fields['service_log'][stage][id] = results.image
                    self.operators['ppocr_v4_lama'][stage][id] = None
                    for shape in results.shapes:
                        if shape.description is not None and "手机时间" in shape.description:
                            if "手机时间：" in shape.description:
                                time_str = shape.description.replace("手机时间：", "").strip()
                            else:
                                time_str = shape.description.replace("手机时间:", "").strip()
                            time_str = time_str.replace("：", ":")
                            print(time_str)
                            self.operators['ppocr_v4_lama'][stage][id] = datetime.strptime(time_str, mark_time_format)

                        else:
                            self.log['opterator'].append(
                                LogItem(f"工作流: ppocr_v4_lama 阶段: {stage} 图像: {id} 未识别水印信息:手机时间",
                                        'warning'))

            this_mark_array = list(self.operators['ppocr_v4_lama'][stage].values())
            if len(this_mark_array) > 1 and this_mark_array[0] is not None and this_mark_array[-1] is not None:
                lat_duration = (this_mark_array[-1] - this_mark_array[0]).total_seconds() / 60
                if lat_duration < self.fields['service']['least_service_duration']:
                    self.log['field'].append(LogItem(f"阶段: {stage} 服务时长{lat_duration}（分钟）不符合规定", 'error'))
            else:
                self.log['field'].append(LogItem(f"阶段: {stage} 无法确定持续时间", 'warning'))

        # 对象检测(按照)
        is_ingredient_employee_cook = False
        is_food_member_eat = False  # 同框记录flag
        self.operators['grounding_dino'] = {}
        self.operators['yolov6_face'] = {}
        self.operators['arcface'] = {}
        self.operators['deit_cls'] = {}
        self.operators['cbiaformer_cls'] = {}
        for stage in self.img_keys:
            # grounding_dino
            if stage in self.Registered_Text_Prompts:
                self.operators['grounding_dino'][stage] = {}
                for id, img in enumerate(self.fields['service_log'][stage]):
                    # cv2.imshow(f'{stage}_{id}', img)
                    # cv2.waitKey(0)
                    self.operators['grounding_dino'][stage][id] = {}
                    for object, text_prompts in self.Registered_Text_Prompts[stage].items():
                        if object in special_thresh_for_dino:  # 特殊置信度赋值
                            self.mapping_flow('grounding_dino').box_threshold = special_thresh_for_dino[object]
                        self.operators['grounding_dino'][stage][id][object] = []
                        for text_prompt in text_prompts:
                            print(text_prompt)
                            self.operators['grounding_dino'][stage][id][object].extend(self.mapping_flow('grounding_dino')
                             .predict_shapes(img, text_prompt=text_prompt).shapes)

                        # 二次提取逻辑
                        if len(self.operators["grounding_dino"][stage][id][object]) > 0:
                            if object == 'ingredient':
                                if stage not in self.operators['deit_cls']:
                                    self.operators['deit_cls'][stage] = {}
                                if id not in self.operators['deit_cls'][stage]:
                                    self.operators['deit_cls'][stage][id] = []
                                for shape in self.operators['grounding_dino'][stage][id][object]:
                                    cropped_obj = crop_polygon_object(img.copy(), shape.points)
                                    (self.operators['deit_cls'][stage][id]
                                     .append(self.mapping_flow('deit_cls')
                                             .predict_shapes(cropped_obj).description))

                            if object == 'food':
                                if stage not in self.operators['cbiaformer_cls']:
                                    self.operators['cbiaformer_cls'][stage] = {}
                                if id not in self.operators['cbiaformer_cls'][stage]:
                                    self.operators['cbiaformer_cls'][stage][id] = []
                                for shape in self.operators['grounding_dino'][stage][id][object]:
                                    cropped_obj = crop_polygon_object(img.copy(), shape.points)
                                    self.operators['cbiaformer_cls'][stage][id].append(
                                        self.mapping_flow('cbiaformer_cls').
                                        predict_shapes(cropped_obj).description)

                            if object == 'person':
                                if stage not in self.operators['yolov6_face']:
                                    self.operators['yolov6_face'][stage] = {}
                                if id not in self.operators['yolov6_face'][stage]:
                                    self.operators['yolov6_face'][stage][id] = []

                                if stage not in self.operators['arcface']:
                                    self.operators['arcface'][stage] = {}
                                if id not in self.operators['arcface'][stage]:
                                    self.operators['arcface'][stage][id] = []

                                for shape in self.operators["grounding_dino"][stage][id][object]:
                                    cropped_obj = crop_polygon_object(img.copy(), shape.points)
                                    face_results = self.mapping_flow('yolov6_face').predict_shapes(cropped_obj)
                                    if type(face_results) is not list:
                                        faces = face_results.avatars
                                        self.operators['yolov6_face'][stage][id].extend(faces)
                                        self.operators['arcface'][stage][id].extend([self.mapping_flow('arcface').get_embedding(face)
                                                                                for face in faces])

                for object, text_prompts in self.Registered_Text_Prompts[stage].items():
                    object_num = 0
                    for objects in self.operators['grounding_dino'][stage].values():
                        object_num += len(objects)
                    if object_num == 0:
                        self.log['opterator'].append(
                            LogItem(f"工作流: grounding_dino 阶段: {stage} 未检测到任何对象{object}",
                                    'warning'))

    def post_processing(self):
        super().post_processing()
        # 水印信息匹配
        # for stage, info in self.operators['ppocr_v4_lama'].items():
        #     name_account = info['姓名账号'].split('/')
        #     name, account = name_account[0], name_account[1]
        #     if name != self.fields['employee']['name']:
        #         self.log['opterator'].append(
        #             LogItem(f"工作流: grounding_dino 阶段: {stage} 未检测到任何对象{object}",
        #                     'warning'))
        #         self.log['estimate'] = f"阶段: {stage} 水印姓名: {name} 系统姓名: {self.fields['employee']['name']} 不匹配"
        #     if account != self.fields['employee']['phone_no']:
        #         self.log['estimate'] = f"阶段: {stage} 水印账号: {account} 系统账号: {self.fields['employee']['phone_no']} 不匹配"

        # start_phone_time = time_format(self.operators['ppocr_v4_lama']['start_img']['手机时间'])
        # start_system_time = time_format(self.fields['service_log']['start_time'])
        # middle_phone_time = time_format(self.operators['ppocr_v4_lama']['middle_img']['手机时间'])
        # middle_system_time = time_format(self.fields['service_log']['middle_time'])
        # end_phone_time = time_format(self.operators['ppocr_v4_lama']['end_img']['手机时间'])
        # end_system_time = time_format(self.fields['service_log']['end_time'])

        # if start_phone_time<start_system_time or start_phone_time > middle_system_time:
        #     self.log['opterator'].append(LogItem(f"阶段: start 手机时间: {start_phone_time} 不在系统时域内: {(start_system_time, middle_system_time)}",
        #                                          'warning'))
        # if middle_phone_time<middle_system_time or middle_phone_time > end_system_time:
        #     self.log['opterator'].append(LogItem(f"阶段: middle 手机时间: {start_phone_time} 不在系统时域内: {(middle_system_time, end_system_time)}",
        #                                          'warning'))
        # if end_phone_time>end_system_time:
        #     self.log['opterator'].append(LogItem(f"阶段: middle 手机时间: {start_phone_time} 不在系统时域内: {(end_system_time, '--')}",
        #                                          'warning'))

        # # 开始阶段-食物/食材
        # start_cook = []
        # for id, infos in self.operators['deit_cls']['start_img'].items():
        #     for info in infos.items():
        #         for item in info: # 一图像中存在多个菜品
        #             cls_names = item.split(' | ')
        #             start_cook.extend(cls_names)
        # for id, infos in self.operators['cbiaformer_cls']['start_img'].items():
        #     for info in infos.items():
        #         for item in info: # 一图像中存在多个菜品
        #             cls_names = item.split(' | ')
        #             start_cook.extend(cls_names)
        # start_cook = set(start_cook)
        # # 中间阶段-食物/食材
        # middle_cook = []
        # for id, infos in self.operators['deit_cls']['middle_img'].items():
        #     for info in infos.items():
        #         for item in info: # 一图像中存在多个菜品
        #             cls_names = item.split(' | ')
        #             middle_cook.extend(cls_names)
        # for id, infos in self.operators['cbiaformer_cls']['middle_img'].items():
        #     for info in infos.items():
        #         for item in info: # 一图像中存在多个菜品
        #             cls_names = item.split(' | ')
        #             middle_cook.extend(cls_names)
        # middle_cook = set(middle_cook)
        # # 结束阶段-食物/食材
        # end_cook = []
        # for id, infos in self.operators['deit_cls']['end_img'].items():
        #     for info in infos.items():
        #         for item in info: # 一图像中存在多个菜品
        #             cls_names = item.split(' | ')
        #             end_cook.extend(cls_names)
        # for id, infos in self.operators['cbiaformer_cls']['end_img'].items():
        #     for info in infos.items():
        #         for item in info: # 一图像中存在多个菜品
        #             cls_names = item.split(' | ')
        #             end_cook.extend(cls_names)
        # end_cook = set(end_cook)
        #
        # # 开始=中间
        # if not(start_cook & middle_cook):
        #     self.log['estimate'] = f"检测食材类别集:{ingredients}与检测食物类别集:{foods} 无交集"
        # # 开始-结束
        # if not(start_cook & end_cook):
        #     self.log['estimate'] = f"检测食材类别集:{ingredients}与检测食物类别集:{foods} 无交集"
        # # 中间-结束
        # if not(middle_cook & end_cook):
        #     self.log['estimate'] = f"检测食材类别集:{ingredients}与检测食物类别集:{foods} 无交集"

        # 做饭相关语义匹配
        ingredients = []
        for stage, infos in self.operators['deit_cls'].items():
            for id, info in infos.items():
                for item in info: # 一图像中存在多个菜品
                    cls_names = item.split(' | ')
                    ingredients.extend(cls_names)
        ingredients = set(ingredients)
        foods = []
        for stage, infos in self.operators['cbiaformer_cls'].items():
            for id, info in infos.items():
                for item in info: # 一图像中存在多个菜品
                    cls_names = item.split(' | ')
                    foods.extend(cls_names)
        foods = set(foods)

        if not(ingredients & foods):
            self.log['estimate'].append(LogItem(f"检测食材类别集:{ingredients}与检测食物类别集:{foods} 无交集",
                                                type='error'))

        # 判断
        emp_attr, meb_attr= None, None
        if self.hasEmpAvatar:
            emp_attr = (self.mapping_flow('arcface')
                        .get_embedding(self.fields['employee']['avatars'][0]))
        if self.hasMebAvatar:
            meb_attr = (self.mapping_flow('arcface')
                        .get_embedding(self.fields['member']['avatars'][0]))

        exist_emp,   exist_meb = {}, {}
        is_emp_live = False
        for stage, faces in self.operators['arcface'].items():
            exist_emp[stage] = {}
            exist_meb[stage] = {}
            for id, face in faces.items():
                exist_emp[stage][id] = False
                exist_meb[stage][id] = False
                for attr in face:
                    if self.hasEmpAvatar and self.mapping_flow('arcface').predict_embeddings(emp_attr, attr):
                        is_emp_live = True
                        exist_emp[stage][id] = True
                    if self.hasMebAvatar and self.mapping_flow('arcface').predict_embeddings(meb_attr, attr):
                        exist_meb[stage][id] = True

        if not is_emp_live:
            self.log['estimate'].append(LogItem("志愿者未出现在任何阶段",
                                                 'error'))
        if not is_all_true(exist_meb):
            self.log['estimate'].append(LogItem("服务对象未出现在任何阶段",
                                                 'error'))

        # 回执单字迹检测
        isMebReceipt = False
        for id, objects in self.operators['grounding_dino']['end_img'].items():
            for shape in objects['paper receipt']:
                cropped_receipt = crop_polygon_object(self.fields['service_log']['end_img'][id].copy(),
                                                      shape.points)
                receipt_results = self.mapping_flow('ppocr_v4_lama').predict_shapes(cropped_receipt)
                if self.fields['member']['name'] not in receipt_results.description:
                    self.log['estimate'].append(LogItem("回执单未检测到服务对象姓名",
                                                        'error'))

                if self.hasMebAvatar and exist_meb['end_img'][id]:
                    isMebReceipt = True  # 老人于回执单同时出现
                elif len(self.operators['grounding_dino']['end_img'][id]['person'])>0:
                    isMebReceipt = True  # 若没有老人头像，用人代替

        if isMebReceipt:
            self.log['estimate'].append(LogItem("服务对象与回执单未同时出现",
                                                 'warning'))

