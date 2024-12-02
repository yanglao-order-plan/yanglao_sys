import re

from work_flow.solutions.base_handler import BaseHandler
from work_flow.utils.image import crop_polygon_object


class CookHandler(BaseHandler):
    Registered_Text_Prompts = {  # grounding_dino动态配置
        'start_img': {
            'door': ['door'],
            'person':['person'],
            'ingredient': ['ingredient']
        },
        'middle_img': {
            'person': ['person'],
            'tool': ['tool'], # 做饭相关道具
            'ingredient': ['ingredient'],
            'food': ['food'],  # 做饭中半成品
        },
        'end_img': {
            'person': ['person'],
            'tool': ['tool'],  # 吃饭相关道具
            'food': ['food'],
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
            for id, img in enumerate(self.fields['service_log'][stage]):
                # ppocr_v4_lama
                results = self.mapping_flow('ppocr_v4_lama').predict_shapes(img)
                if results.descriptions is not None:
                    self.operators[stage]['image'] = results.img
                    self.operators[stage]['water_mark'] = {}
                    for key, format in self.Registered_OCR_Format.items():
                        for shape in results.shapes:
                            if shape.description is not None and re.match(format, shape.description):
                                self.operators[stage]['water_mark'][key] = shape.description
        # 对象检测
        for stage in self.img_keys:
            if stage in self.Registered_Text_Prompts:
                for id, img in enumerate(self.fields['service_log'][stage]):
                    self.operators[stage][id]['object'] = {}
                    for object, text_prompts in self.Registered_Text_Prompts[stage].items():
                        self.operators[stage][id]['object'][object] = []
                        for text_prompt in text_prompts:
                            self.operators[stage][id]['object'][object].append(self.mapping_flow('grounding_dino')
                             .predict_shapes(img, prompt_mode=text_prompt))

                        # 二次提取逻辑
                        if object == 'ingredient':
                            self.operators['cbiaformer_cls'][stage] = []
                            for dino_results in self.operators[stage][id]['object'][object]:
                                for shape in dino_results.shapes:
                                    cropped_obj = crop_polygon_object(img.copy(), shape.points)
                                    self.operators['cbiaformer_cls'][stage].append(self.mapping_flow('cbiaformer_cls').
                                                                                           predict_shapes(cropped_obj))
                        elif object == 'food':
                            self.operators['swin_net'][stage] = []
                            for shape in self.operators[stage][object].shapes:
                                cropped_obj = crop_polygon_object(img.copy(), shape.points)
                                self.operators['swin_net'][stage].append(self.mapping_flow('cbiaformer_cls').
                                                                                       predict_shapes(cropped_obj))
                        elif object == 'person':
                            self.operators['yolov6_face'][stage] = []
                            self.operators['arcface'][stage] = []
                            for shape in self.operators[stage][object].shapes:
                                cropped_obj = crop_polygon_object(img.copy(), shape.points)
                                face_results = (self.mapping_flow('yolov6-face')
                                                .predict_shapes(cropped_obj))
                                faces = face_results.avatars
                                self.operators['yolov6'][stage].append([self.mapping_flow('arcface').get_embedding(face)
                                                                        for face in faces])

    def post_processing(self):
        super().post_processing()
        # 检测阶段是否存在水印
        for key, format in self.Registered_OCR_Format.items():
            if key not in self.operators['ppocr_v4_lama'][stage]:
                self.log['opterator'].append(f"工作流: ppocr_v4_lama 阶段: {stage} 未识别水印信息:{key}")
            elif not re.match(format, self.operators['ppocr_v4_lama'][stage]):
                self.log['opterator'].append(f"工作流: ppocr_v4_lama 阶段: {stage} 识别水印信息{key}格式错误:")
        pass
