import base64
import re
from datetime import datetime
from io import BytesIO

import numpy as np
from PIL import Image

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


class CookHandler(BaseHandler):
    Flow_Keys = ['grounding_dino', 'sam_hq', 'ppocr_v4_lama',
                 'unidet', 'yolov6_face', 'arcface']  # 注册工作流
    Registered_Text_Prompts = {  # grounding_dino动态配置
        'start_img': {
            'door': ['door'],
            'person':['person'],
            # 'ingredient': ['ingredient']
        },
        'middle_img': {
            'person': ['person'],
            'cookware': ['cookware'], # 厨具
            'dinnerware': ['dinnerware'], # 餐具
            'ingredient': ['ingredient'],
            'food': ['food'],  # 做饭中半成品
        },
        'end_img': {
            'person': ['person'],
            # 'tool': ['tool'],  # 吃饭相关道具
            # 'food': ['food'],
            'receipt': ['receipt made by paper'] # 回执单
        },
    },
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
        for stage in self.img_keys:
            match_flag = {key: False for key in self.Registered_OCR_Format}
            if all(match_flag.values()): # 每阶段仅有一张图片满足要求即可
                continue
            for id, img in enumerate(self.fields['service_log'][stage]):
                results = self.mapping_flow('ppocr_v4_lama').predict_shapes(img)
                if results.descriptions is not None:
                    self.fields['service_log'][stage][id] = results.image
                    for key, format in self.Registered_OCR_Format.items():
                        for shape in results.shapes:
                            if shape.description is not None and re.match(format, shape.description):
                                match_flag[key] = True
                                self.operators['ppocr_v4_lama'][stage][key] = shape.description
            # 水印提取异常检测
            for key, format in self.Registered_OCR_Format.items():
                if key not in self.operators['ppocr_v4_lama'][stage]:
                    self.log['opterator'].append(LogItem(f"工作流: ppocr_v4_lama 阶段: {stage} 未识别水印信息:{key}",
                                                         'warning'))
                elif not re.match(format, self.operators['ppocr_v4_lama'][stage]):
                    self.log['opterator'].append(LogItem(f"工作流: ppocr_v4_lama 阶段: {stage} 识别水印信息{key}格式错误:",
                                                         'warning'))
        # 对象检测
        for stage in self.img_keys:
            # grounding_dino
            if stage in self.Registered_Text_Prompts:
                self.operators['grounding_dino'][stage] = {}
                for id, img in enumerate(self.fields['service_log'][stage]):
                    self.operators['grounding_dino'][stage][id] = {}
                    for object, text_prompts in self.Registered_Text_Prompts[stage].items():
                        self.operators['grounding_dino'][stage][id][object] = []
                        for text_prompt in text_prompts:
                            self.operators['grounding_dino'][stage][id][object].extend(self.mapping_flow('grounding_dino')
                             .predict_shapes(img, prompt_mode=text_prompt))

                        # 二次提取逻辑
                        if object == 'ingredient':
                            if stage not in self.operators['cbiaformer_cls']:
                                self.operators['cbiaformer_cls'][stage] = {}
                            if id not in self.operators['cbiaformer_cls'][stage]:
                                self.operators['cbiaformer_cls'][stage][id] = []
                            for results in self.operators['grounding_dino'][id][stage][object]:
                                for shape in results.shapes:
                                    cropped_obj = crop_polygon_object(img.copy(), shape.points)
                                    (self.operators['cbiaformer_cls'][stage][id]
                                     .append(self.mapping_flow('cbiaformer_cls')
                                             .predict_shapes(cropped_obj).description))
                        if object == 'food':
                            if stage not in self.operators['cbiaformer_cls']:
                                self.operators['cbiaformer_cls'][stage] = {}
                            if id not in self.operators['cbiaformer_cls'][stage]:
                                self.operators['cbiaformer_cls'][stage][id] = []
                            for results in self.operators['grounding_dino'][id][stage][object]:
                                for shape in results.shapes:
                                    cropped_obj = crop_polygon_object(img.copy(), shape.points)
                                    self.operators['cbiaformer_cls'][stage][id].append(
                                        self.mapping_flow('cbiaformer_cls').
                                        predict_shapes(cropped_obj).description)

                        if object == 'person':
                            if stage not in self.operators['yolov6-face']:
                                self.operators['yolov6-face'][stage] = {}
                            if id not in self.operators['yolov6-face'][stage]:
                                self.operators['yolov6-face'][stage][id] = []

                            if stage not in self.operators['arcface']:
                                self.operators['arcface'][stage] = {}
                            if id not in self.operators['arcface'][stage]:
                                self.operators['arcface'][stage][id] = []

                            for shape in self.operators[stage][id][object].shapes:
                                cropped_obj = crop_polygon_object(img.copy(), shape.points)
                                face_results = (self.mapping_flow('yolov6-face')
                                                .predict_shapes(cropped_obj))
                                faces = face_results.avatars
                                self.operators['yolov6-face'][stage][id].extend(faces)
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
        for stage, info in self.operators['ppocr_v4_lama'].items():
            name_account = info['姓名账号'].split('/')
            name, account = name_account[0], name_account[1]
            if name != self.fields['employee']['name']:
                self.log['opterator'].append(
                    LogItem(f"工作流: grounding_dino 阶段: {stage} 未检测到任何对象{object}",
                            'warning'))
                self.log['estimate'] = f"阶段: {stage} 水印姓名: {name} 系统姓名: {self.fields['employee']['name']} 不匹配"
            if account != self.fields['employee']['phone_no']:
                self.log['estimate'] = f"阶段: {stage} 水印账号: {account} 系统账号: {self.fields['employee']['phone_no']} 不匹配"

        start_phone_time = time_format(self.operators['ppocr_v4_lama']['start_img']['手机时间'])
        start_system_time = time_format(self.fields['service_log']['start_time'])
        middle_phone_time = time_format(self.operators['ppocr_v4_lama']['middle_img']['手机时间'])
        middle_system_time = time_format(self.fields['service_log']['middle_time'])
        end_phone_time = time_format(self.operators['ppocr_v4_lama']['end_img']['手机时间'])
        end_system_time = time_format(self.fields['service_log']['end_time'])

        if start_phone_time<start_system_time or start_phone_time > middle_system_time:
            self.log['opterator'].append(LogItem(f"阶段: start 手机时间: {start_phone_time} 不在系统时域内: {(start_system_time, middle_system_time)}",
                                                 'warning'))
        if middle_phone_time<middle_system_time or middle_phone_time > end_system_time:
            self.log['opterator'].append(LogItem(f"阶段: middle 手机时间: {start_phone_time} 不在系统时域内: {(middle_system_time, end_system_time)}",
                                                 'warning'))
        if end_phone_time>end_system_time:
            self.log['opterator'].append(LogItem(f"阶段: middle 手机时间: {start_phone_time} 不在系统时域内: {(end_system_time, '--')}",
                                                 'warning'))

        # 做饭相关语义匹配
        ingredients = []
        for stage, infos in self.operators['cbiaformer_cls'].items():
            for id, info in infos.items():
                cls_names = info.split(' | ')
                ingredients.extend(cls_names)
        ingredients = set(ingredients)
        foods = []
        for stage, infos in self.operators['cbiaformer_cls'].items():
            for id, info in infos.items():
                cls_names = info.split(' | ')
                foods.extend(cls_names)
        foods = set(foods)

        if not(ingredients & foods):
            self.log['estimate'] = f"检测食材类别集:{ingredients}与检测食物类别集:{foods} 无交集"

        # 判断
        emp_attr, meb_attr= None, None
        if self.hasEmpAvatar:
            emp_attr = (self.mapping_flow('arcface')
                        .get_embedding(self.fields['employee']['avatars'][0]))
        if self.hasMebAvatar:
            meb_attr = (self.mapping_flow('arcface')
                        .get_embedding(self.fields['member']['avatars'][0]))

        exist_emp, exist_meb = {}, {}
        is_emp_live = False
        for stage, faces in self.operators['arcface'].items():
            exist_emp[stage] = {}
            exist_meb[stage] = {}
            for id, face in faces.items():
                exist_emp[stage][id] = False
                exist_meb[stage][id] = False
                for attr in face:
                    if self.mapping_flow('arcface').predict_embeddings(emp_attr, attr):
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
            for shape in objects['receipt']:
                cropped_receipt = crop_polygon_object(self.fields['service_log']['end_img'][id].copy(),
                                                      shape.points)
                receipt_results = self.mapping_flow('ppocr_v4_lama').predict_shapes(cropped_receipt)
                if self.fields['member']['name'] not in receipt_results.descriptions:
                    self.log['estimate'].append(LogItem("回执单未检测到服务对象姓名",
                                                        'error'))

