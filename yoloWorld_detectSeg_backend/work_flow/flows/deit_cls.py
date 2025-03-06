import os

import PIL
import cv2
import numpy as np
import torch
from PIL import ImageEnhance, Image
import torch.nn as nn
from work_flow.app_info import __preferred_device__
from work_flow.engines.model import Model
from work_flow.engines.types import AutoLabelingResult
from work_flow.engines.build_onnx_engine import OnnxBaseModel
from work_flow.utils.cbiaformer.tta import tta_transforms
from work_flow.utils.shape import Shape


def get_info(classes_path):
    with open(classes_path, encoding='utf-8') as f:
        class_names = f.readlines()
    names = []
    indexs = []
    for data in class_names:
        name, index = data.split(' ')
        names.append(name)
        indexs.append(int(index))

    return names, indexs

class DEIT_CLS(Model):
    """Image tagging model using Recognize Anything Model (RAM)"""
    T = 0.45
    length=16
    result = [0] * length
    classes_map = 'E:\GitHub\yanglao_sys\yoloWorld_detectSeg_backend\work_flow\configs\cbiaformer/annotations.txt'
    class Meta:
        required_config_names = [
            "type",
            "name",
            "display_name",
            "model_path",
        ]
        widgets = ["button_run"]
        output_modes = {
            "rectangle": "Rectangle",
        }
        default_output_mode = "rectangle"

    def __init__(self, model_config, on_message) -> None:
        # Run the parent class's init method
        super().__init__(model_config, on_message)
        model_name = self.config["type"]
        model_abs_path = self.get_model_abs_path(self.config, "model_path")
        if not model_abs_path or not os.path.isfile(model_abs_path):
            raise FileNotFoundError(
                f"Could not download or initialize {model_name} model."
            )
        self.classes_names, self.label_names = get_info(self.classes_map)
        self.net = OnnxBaseModel(model_abs_path, 'CPU')
        self.input_shape = self.net.get_input_shape()[-2:]

    def preprocess(self, input_image, input_shape):
        """
        Pre-processes the input image before feeding it to the network.
        """
        h, w = input_shape
        image = cv2.resize(input_image, (w, h))
        input_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        # pillow增强策略
        c = ImageEnhance.Color(input_image)
        input_image = c.enhance(2)
        # 显示处理后的图片
        # input_image.show(title="Processed Image")
        # TTA增强策略
        arg_blobs = []
        for transform in tta_transforms:
            augmented_image = transform(input_image).unsqueeze(0).numpy()
            arg_blobs.append(augmented_image)
        return arg_blobs

    def inference(self, blob):
        outs = self.net.get_ort_inference(blob, extract=False)
        return outs

    def postprocess(self, all_logits):
        """
        Post-processes the network's output.
        """
        final_sigmoid = torch.stack(all_logits)
        tmp = final_sigmoid.gt(self.T)
        indices = torch.where(tmp)[-1]

        return indices

    def predict_shapes(self, image, image_path=None):
        """
        Predict shapes from image
        """

        if image is None:
            return []

        arg_blobs = self.preprocess(image.copy(), self.input_shape)
        all_logits = [torch.tensor(np.array((self.inference(arg_blob))))
                      for arg_blob in arg_blobs]
        # 平均汇总所有增强变换的结果
        indices = self.postprocess(all_logits)
        description = self.get_description(indices)
        result = AutoLabelingResult(
            shapes=[], replace=False, description=description
        )
        return result

    @staticmethod
    def load_tag_list():
        import importlib.resources as pkg_resources
        from work_flow.configs import ram
        with pkg_resources.path(ram, 'ram_tag_list.txt') as p:
            tag_list = p.read_text().splitlines()
        tag_list = np.array(tag_list)
        with pkg_resources.path(ram, 'ram_tag_list_chinese.txt') as p:
            tag_list_chinese = p.read_text(encoding='utf-8').splitlines()
        tag_list_chinese = np.array(tag_list_chinese)
        return tag_list, tag_list_chinese

    def get_description(self, indices):
        cls_names = [self.classes_names[idx] for idx in indices if self.classes_names[idx] != '其他类']
        descriptions = ' | '.join(cls_names)
        return descriptions

    def unload(self):
        del self.net
