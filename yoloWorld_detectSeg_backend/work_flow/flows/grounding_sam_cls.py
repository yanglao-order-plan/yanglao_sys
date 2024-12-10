import logging
import os
import threading

import cv2
import traceback
import onnxruntime
import numpy as np

from typing import Dict
from copy import deepcopy
from tokenizers import Tokenizer


from . import __preferred_device__, Model, AutoLabelingResult, Shape, OnnxBaseModel, Args
from .cbiaformer_cls import CBIAFORMER_CLS
from .deit_cls import DEIT_CLS
from .grounding_sam import GroundingSAM
from .lru_cache import LRUCache
from ..__base__.sam_hq import SegmentAnythingHQONNX
from ..utils.image import crop_polygon_object


class GroundingSAM_CLS(Model):
    """Open-Set instance segmentation model using GroundingSAM"""

    class Meta:
        required_config_names = [
            "type",
            "name",
            "display_name",
            "model_type",
            "model_path",
            "input_width",
            "input_height",
            "box_threshold",
            "text_threshold",
            "encoder_model_path",
            "decoder_model_path",
        ]
        widgets = [
            "edit_text",
            "button_send",
            "output_label",
            "output_select_combobox",
            "button_add_point",
            "button_remove_point",
            "button_add_rect",
            "button_clear",
            "button_finish_object",
        ]
        output_modes = {
            "polygon": "Polygon",
            "rectangle": "Rectangle",
            "rotation": "Rotation",
        }
        default_output_mode = "polygon"

    def __init__(self, model_config, on_message) -> None:
        # Run the parent class's init method
        super().__init__(model_config, on_message)

        # ----------- Grounding-DINO ---------- #
        model_type = self.config["model_type"]
        model_abs_path = self.get_model_abs_path(self.config, "model_path")
        if not model_abs_path or not os.path.isfile(model_abs_path):
            raise FileNotFoundError(
                f"Could not download or initialize {model_type} model."
            )
        self.net = GroundingSAM(self.config, logging)
        self.config['model_path'] = self.config['cls_path']
        object_type = self.config["object_type"]
        if object_type == "food":
            self.model = CBIAFORMER_CLS(self.config, logging)
        elif object_type == 'ingredient':
            self.model = DEIT_CLS(self.config, logging)


    def predict_shapes(self, image, image_path=None, text_prompt=None):
        """
        Predict shapes from image
        """
        if image is None:
            return []
        try:
            sam_results = self.net.predict_shapes(image, text_prompt=text_prompt)
            for shape in sam_results.shapes:
                cropped_img = crop_polygon_object(image.copy(), shape.points)
                results = self.model.predict_shapes(cropped_img)
                shape.description = results.description
            return sam_results

        except Exception as e:  # noqa
            logging.warning("Could not inference model")
            logging.error(e)
            traceback.print_exc()
            return AutoLabelingResult([], replace=False)
