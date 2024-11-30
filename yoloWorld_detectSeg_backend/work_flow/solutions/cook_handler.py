import re

from work_flow.solutions.base_handler import BaseHandler

def is_valid_mark(letters: str):


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
    }
    Registered_OCR_Format = {
        '姓名账号': '[\u4e00-\u9fa5]{2,5}/\d{11}',
        '身份证号': '\d{18}',
        '版本号': '\d+\.\d+\.\d+',
        '手机时间': '\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}'
    }
    def __init__(self, order_id, configs, **kwargs):
        super().__init__(order_id, configs, **kwargs)

    def opt_processing(self):
        log = []
        # 服务前
        for stage in self.img_keys:
            for img in self.fields['service_log'][stage]:
                # ppocr_v4_lama
                self.operators['ppocr_v4_lama'][stage] = {}
                letters = self.mapping_flow('ppocr_v4_lama').predict_shapes(img)
                if letters.descriptions is None:
                    continue
                for key, format in self.Registered_OCR_Format.items():
                    for shape in letters.shapes:
                        if shape.description is not None and re.match(format, shape.description):
                            self.operators['ppocr_v4_lama'][stage][key] = shape.description
                            break
                # grounding_dino
                if stage in self.Registered_Text_Prompts:
                    self.operators['grounding_dino'][stage] = {}
                    for object, text_prompts in self.Registered_Text_Prompts[stage].items():
                        self.operators[stage][object] = []
                        for text_prompt in text_prompts:
                            self.operators[stage][object].append(self.mapping_flow('grounding_dino')
                                                                     .predict_shapes(img, prompt_mode=text_prompt))
            for key, format in self.Registered_OCR_Format.items():
                if key not in self.operators['ppocr_v4_lama'][stage]:
                    log.append(f"工作流: ppocr_v4_lama 阶段: {stage} 未识别水印信息:{key}")
                elif not re.match(format, self.operators['ppocr_v4_lama'][stage]):
                    log.append(f"工作流: ppocr_v4_lama 阶段: {stage} 识别水印信息{key}格式错误:"
                               f"{self.operators['ppocr_v4_lama'][stage]}")
        return log