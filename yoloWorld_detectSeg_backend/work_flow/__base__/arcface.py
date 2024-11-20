import math
import os
import re
import traceback

import cv2
import numpy as np
import logging

import torch

from . import __preferred_device__
from .clip import ChineseClipONNX
from ..engines.model import Model
from ..engines.types import AutoLabelingResult
from ..utils.arcface import get_model
from ..utils.segment_anything import sam_model_registry, SamAutomaticMaskGenerator
from ..utils.shape import Shape


class ArcFace(Model):
    """Segmentation model using SegmentAnything"""

    class Meta:
        required_config_names = [
            "type",
            "name",
            "display_name",
            "model_path",
            "model_type",
        ]
        widgets = [
            "output_label",
        ]
        output_modes = {
            "rectangle": "Rectangle",
            "rotation": "Rotation",
        }
        default_output_mode = "rectangle"

    def __init__(self, config_path, on_message) -> None:
        # Run the parent class's init method
        super().__init__(config_path, on_message)

        # Get encoder and decoder model paths
        model_abs_path = self.get_model_abs_path(self.config, "model_path")
        if not model_abs_path or not os.path.isfile(
            model_abs_path
        ):
            raise FileNotFoundError(
                "Could not download or initialize encoder of ArcFace net."
            )
        self.model_type = self.config.get('model_type', None)
        if self.model_type is None:
            raise ValueError("model_type is required in config")
        self.net = get_model(self.model_type)
        self.net.load_state_dict(torch.load(model_abs_path, weights_only=True))
        self.net.eval()
        self.device = 'cuda' if __preferred_device__ == 'GPU' else 'cpu'

    def preprocess(self, image):
        img = cv2.resize(image, (112, 112))
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img = np.transpose(img, (2, 0, 1))
        img = torch.from_numpy(img).unsqueeze(0).float()
        img.div_(255).sub_(0.5).div_(0.5)
        img = img.to(self.device)
        return img

    @torch.no_grad()
    def predict_shapes(self, image, minor=None, sim_threshold=0.5):
        """
        Predict shapes from image
        """
        if image is None or minor is None:
            return AutoLabelingResult([], replace=False)

        try:
            self.net.to(self.device)
            cv_img1 = self.preprocess(image)
            cv_img2 = self.preprocess(minor)
            feat1 = self.net(cv_img1).numpy()[0]
            feat2 = self.net(cv_img2).numpy()[0]
            sum: float = 0
            len1: float = 0
            len2: float = 0
            for i in range(512):
                n1 = feat1[i]
                n2 = feat2[i]
                sum += n1 * n2
                len1 += n1 * n1
                len2 += n2 * n2
            len1 = math.sqrt(len1)
            len2 = math.sqrt(len2)
            div = sum / len1 / len2
            flag = div > sim_threshold
            description = f"Face Similarity: {div}\n Is the Same: {flag}"
        except Exception as e:  # noqa
            logging.warning("Could not inference model")
            logging.error(e)
            traceback.print_exc()
            return AutoLabelingResult([], replace=False)

        return AutoLabelingResult([], description=description, replace=False)

