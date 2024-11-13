import os
import sys
import traceback
import logging
import numpy as np

from . import __preferred_device__, Model, Shape, AutoLabelingResult
from ..__base__.clip import ChineseClipONNX


class ChineseCLIP(Model):
    """Segmentation model using SegmentAnything"""

    class Meta:
        required_config_names = [
            "type",
            "name",
            "display_name",
            "classes"
        ]
        widgets = [
            "edit_conf",
        ]
        output_modes = {
            "rectangle": "Rectangle",
        }
        default_output_mode = "rectangle"

    def __init__(self, config_path, on_message) -> None:
        # Run the parent class's init method
        super().__init__(config_path, on_message)

        self.clip_net = None
        clip_txt_model_path = self.get_model_abs_path(
            self.config, "txt_model_path"
        )
        _ = self.get_model_abs_path(self.config, "txt_extra_path")
        clip_img_model_path = self.get_model_abs_path(
            self.config, "img_model_path"
        )
        _ = self.get_model_abs_path(self.config, "img_extra_path")
        model_arch = self.config["model_arch"]
        self.model = ChineseClipONNX(
            clip_txt_model_path,
            clip_img_model_path,
            model_arch,
            device=__preferred_device__,
        )
        self.classes = self.config.get("classes", [])


    def predict_shapes(self, image, filename=None) -> AutoLabelingResult:
        """
        Predict shapes from image
        """
        if image is None:
            return AutoLabelingResult([], replace=False)

        try:
            out = self.model(image, self.classes)
            return AutoLabelingResult([], replace=False, description=self.classes[int(np.argmax(out))])
        except Exception as e:  # noqa
            logging.warning("Could not inference model")
            logging.error(e)
            traceback.print_exc()
            return AutoLabelingResult([], replace=False)
