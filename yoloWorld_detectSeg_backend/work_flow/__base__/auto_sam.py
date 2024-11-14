import os
import threading
import traceback
import cv2
import numpy as np
import logging

from . import __preferred_device__
from .clip import ChineseClipONNX
from ..engines.model import Model
from ..engines.types import AutoLabelingResult
from ..flows import LRUCache
from ..utils.segment_anything import sam_model_registry, SamAutomaticMaskGenerator
from ..utils.shape import Shape


class SegmentAnythingAutomatic(Model):
    """Segmentation model using SegmentAnything"""

    class Meta:
        required_config_names = [
            "type",
            "name",
            "display_name",
            "encoder_model_path",
            "decoder_model_path",
        ]
        widgets = [
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

    def __init__(self, config_path, on_message) -> None:
        # Run the parent class's init method
        super().__init__(config_path, on_message)

        # Get encoder and decoder model paths
        model_abs_path = self.get_model_abs_path(
            self.config, "model_path"
        )
        if not model_abs_path or not os.path.isfile(
            model_abs_path
        ):
            raise FileNotFoundError(
                "Could not download or initialize encoder of Segment Anything."
            )
        model_type = self.config.get("model_type", None)
        sam = sam_model_registry[model_type](checkpoint=model_abs_path)
        self.model = SamAutomaticMaskGenerator(sam, output_mode='binary_mask')
        # CLIP flows
        self.clip_net = None
        clip_txt_model_path = self.config.get("txt_model_path", "")
        clip_img_model_path = self.config.get("img_model_path", "")
        if clip_txt_model_path and clip_img_model_path:
            if self.config["model_type"] == "cn_clip":
                clip_txt_model_path = self.get_model_abs_path(
                    self.config, "txt_model_path"
                )
                _ = self.get_model_abs_path(self.config, "txt_extra_path")
                clip_img_model_path = self.get_model_abs_path(
                    self.config, "img_model_path"
                )
                _ = self.get_model_abs_path(self.config, "img_extra_path")
                model_arch = self.config["model_arch"]
                self.clip_net = ChineseClipONNX(
                    clip_txt_model_path,
                    clip_img_model_path,
                    model_arch,
                    device=__preferred_device__,
                )
            self.classes = self.config.get("classes", [])

    def post_process(self, data, image=None):
        """
        Post process masks
        """
        # Find contours
        approx_contours = []
        for ann in data:
            mask = ann['segmentation'] * 255
            mask = np.array(mask).astype(np.uint8)
            contours, _ = cv2.findContours(
                mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE
            )
            max_contour = max(contours, key=cv2.contourArea)
            epsilon = 0.001 * cv2.arcLength(max_contour, True)
            approx = cv2.approxPolyDP(max_contour, epsilon, True)
            approx_contours.append(approx)

        # Remove too big contours ( >90% of image size)
        if len(approx_contours) > 1:
            image_size = data[0]['segmentation'].shape[0] * data[0]['segmentation'].shape[1]
            areas = [cv2.contourArea(contour) for contour in approx_contours]
            avg_area = np.mean(areas)
            filtered_approx_contours = []
            for contour, area in zip(approx_contours, areas):
                if area < image_size * 0.9 or area > avg_area * 0.2:
                    filtered_approx_contours.append(contour)
            approx_contours = filtered_approx_contours
        # Contours to shapes
        shapes = []
        if self.output_mode == "polygon":
            for i, approx in enumerate(approx_contours):
                # Scale points
                points = approx.reshape(-1, 2)
                points[:, 0] = points[:, 0]
                points[:, 1] = points[:, 1]
                points = points.tolist()
                if len(points) < 3:
                    continue
                points.append(points[0])

                # Create shape
                shape = Shape(flags={})
                for point in points:
                    point[0] = int(point[0])
                    point[1] = int(point[1])
                    shape.add_point(point[0], point[1])
                shape.shape_type = "polygon"
                shape.closed = True
                shape.fill_color = "#000000"
                shape.line_color = "#000000"
                shape.line_width = 1
                shape.label = f"AUTOLABEL_OBJECT: {i}"
                shape.selected = False
                shapes.append(shape)
        elif self.output_mode in ["rectangle", "rotation"]:
            for i, approx in enumerate(approx_contours):
                x_min = 100000000
                y_min = 100000000
                x_max = 0
                y_max = 0
                # Scale points
                points = approx.reshape(-1, 2)
                points[:, 0] = points[:, 0]
                points[:, 1] = points[:, 1]
                points = points.tolist()
                if len(points) < 3:
                    continue
                # Create shape
                shape = Shape(flags={})
                for point in points:
                    x_min = min(x_min, point[0])
                    y_min = min(y_min, point[1])
                    x_max = max(x_max, point[0])
                    y_max = max(y_max, point[1])
                    point[0] = int(point[0])
                    point[1] = int(point[1])
                    shape.add_point(point[0], point[1])
                shape.shape_type = (
                    "rectangle" if self.output_mode == "rectangle" else "rotation"
                )
                shape.closed = True
                shape.fill_color = "#000000"
                shape.line_color = "#000000"
                shape.line_width = 1
                if self.clip_net is not None and self.classes:
                    img = image[y_min:y_max, x_min:x_max]
                    out = self.clip_net(img, self.classes)
                    shape.cache_label = self.classes[int(np.argmax(out))]
                shape.label = f"AUTOLABEL_OBJECT: {i}"
                shape.selected = False
                shapes.append(shape)
        return shapes

    def predict_shapes(self, image, filename=None, binary_mask=False):
        """
        Predict shapes from image
        """
        if image is None:
            return AutoLabelingResult([], replace=False)

        try:
            self.model.predictor.model.to(__preferred_device__)
            data = self.model.generate(image)
            shapes = self.post_process(data, image)
        except Exception as e:  # noqa
            logging.warning("Could not inference model")
            logging.error(e)
            traceback.print_exc()
            return AutoLabelingResult([], replace=False)

        result = []
        if not binary_mask:
            return [AutoLabelingResult(shapes, replace=False)]
        for shape in shapes:
            result.append(AutoLabelingResult([shape], replace=False,
                                             _binary_drawing=True))

