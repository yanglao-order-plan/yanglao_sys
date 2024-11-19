import os
import cv2
import numpy as np

from work_flow.app_info import __preferred_device__
from work_flow.engines.model import Model
from work_flow.engines.types import AutoLabelingResult
from work_flow.engines.build_onnx_engine import OnnxBaseModel


class RecognizeAnything(Model):
    """Image tagging model using Recognize Anything Model (RAM)"""

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
        # TODO 目前无法使用gpu推理 -1073740791 (0xC0000409)
        self.net = OnnxBaseModel(model_abs_path, 'CPU')
        self.input_shape = self.net.get_input_shape()[-2:]
        self.tag_mode = self.config.get("tag_mode", "")  # ['en', 'cn']

        # load tag list
        self.tag_list, self.tag_list_chinese = self.load_tag_list()
        delete_tags = self.config.get("delete_tags", [])
        filter_tags = self.config.get("filter_tags", [])
        if delete_tags:
            self.delete_tag_index = [
                self.tag_list.tolist().index(label) for label in delete_tags
            ]
        elif filter_tags:
            self.delete_tag_index = [
                index
                for index, item in enumerate(self.tag_list)
                if item not in filter_tags
            ]
        else:
            self.delete_tag_index = []

    def preprocess(self, input_image, input_shape):
        """
        Pre-processes the input image before feeding it to the network.
        """
        h, w = input_shape
        image = cv2.resize(input_image, (w, h))
        image = image / 255.0
        mean = np.array([0.485, 0.456, 0.406])
        std = np.array([0.229, 0.224, 0.225])
        image = (image - mean) / std
        image = np.transpose(image, (2, 0, 1))
        image = np.expand_dims(image, 0).astype(np.float32)
        return image

    def inference(self, blob):
        outs = self.net.get_ort_inference(blob, extract=False)
        return outs

    def postprocess(self, outs):
        """
        Post-processes the network's output.
        """
        tags, bs = outs
        tags[:, self.delete_tag_index] = 0
        tag_output = []
        tag_output_chinese = []
        for b in range(bs[0]):
            index = np.argwhere(tags[b] == 1)
            token = self.tag_list[index].squeeze(axis=1)
            tag_output.append(" | ".join(token))
            token_chinese = self.tag_list_chinese[index].squeeze(axis=1)
            tag_output_chinese.append(" | ".join(token_chinese))

        return tag_output, tag_output_chinese

    def predict_shapes(self, image, image_path=None):
        """
        Predict shapes from image
        """

        if image is None:
            return []

        blob = self.preprocess(image, self.input_shape)
        outs = self.inference(blob)
        tags = self.postprocess(outs)
        description = self.get_results(tags)
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

    def get_results(self, tags):
        en_tags, zh_tag = tags
        image_description = en_tags[0] + "\n" + zh_tag[0]
        if self.tag_mode == "en":
            return en_tags[0]
        elif self.tag_mode == "zh":
            return zh_tag[0]
        return image_description

    def get_labels(self, tags):
        en_tags, zh_tag = tags
        if self.tag_mode == "en":
            return en_tags[0].split(' | ')
        elif self.tag_mode == "zh":
            return zh_tag[0].split(' | ')
        else:
            raise ValueError("Unknown tag mode")


    def unload(self):
        del self.net
