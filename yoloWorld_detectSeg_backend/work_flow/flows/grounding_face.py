import logging
import os
import threading

import cv2
import traceback

import numpy
import onnxruntime
import numpy as np

from typing import Dict
from copy import deepcopy
from tokenizers import Tokenizer


from . import __preferred_device__, Model, AutoLabelingResult, Shape, OnnxBaseModel, Args, Grounding_DINO
from .cbiaformer_cls import CBIAFORMER_CLS
from .grounding_sam import GroundingSAM
from .lru_cache import LRUCache
from .yolov6_face import YOLOv6Face
from ..__base__.sam_hq import SegmentAnythingHQONNX
from ..utils import xyxyxyxy_to_xyxy
from ..utils.image import crop_polygon_object

# 最终的人脸对齐图像尺寸分为两种：112x96和112x112，并分别对应结果图像中的两组仿射变换目标点,如下所示
imgSize1 = [112, 96]
imgSize2 = [112, 112]
coord5point1 = [[30.2946, 51.6963],  # 112x96的目标点
                [65.5318, 51.6963],
                [48.0252, 71.7366],
                [33.5493, 92.3655],
                [62.7299, 92.3655]]
coord5point2 = [[30.2946 + 8.0000, 51.6963],  # 112x112的目标点
                [65.5318 + 8.0000, 51.6963],
                [48.0252 + 8.0000, 71.7366],
                [33.5493 + 8.0000, 92.3655],
                [62.7299 + 8.0000, 92.3655]]

def transformation_from_points(points1, points2):
    points1 = points1.astype(numpy.float64)
    points2 = points2.astype(numpy.float64)
    c1 = numpy.mean(points1, axis=0)
    c2 = numpy.mean(points2, axis=0)
    points1 -= c1
    points2 -= c2
    s1 = numpy.std(points1)
    s2 = numpy.std(points2)
    points1 /= s1
    points2 /= s2
    U, S, Vt = numpy.linalg.svd(points1.T * points2)
    R = (U * Vt).T
    return numpy.vstack([numpy.hstack(((s2 / s1) * R, c2.T - (s2 / s1) * R * c1.T)), numpy.matrix([0., 0., 1.])])


def warp_im(img_im, orgi_landmarks, tar_landmarks):
    pts1 = numpy.float64(numpy.matrix([[point[0], point[1]] for point in orgi_landmarks]))
    pts2 = numpy.float64(numpy.matrix([[point[0], point[1]] for point in tar_landmarks]))
    M = transformation_from_points(pts1, pts2)
    dst = cv2.warpAffine(img_im, M[:2], (img_im.shape[1], img_im.shape[0]))
    return dst


class GroundingSAM_Face(Model):
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
        self.net = Grounding_DINO(self.config, logging)
        self.config['model_path'] = self.config['face_path']
        self.yolov6_face = YOLOv6Face(self.config, logging)
        self.scale = self.config.get("scale", "112x112")



    def key_transform(self, img_im, box, points):
        shape = img_im.shape
        height = shape[0]
        width = shape[1]
         # 处理该张图片中的每个
        bounding_box = xyxyxyxy_to_xyxy(box)
        pmin, pmax = min(points[:5]), max(points[:5])
        x1, y1, x2, y2 = int(min(bounding_box[0], pmin)), \
            int(min(bounding_box[1], pmin)), \
            int(max(bounding_box[2], pmax)), \
            int(max(bounding_box[3], pmax))
        # 外扩大100%，防止对齐后人脸出现黑边
        new_x1 = max(int(1.50 * x1 - 0.50 * x2), 0)
        new_x2 = min(int(1.50 * x2 - 0.50 * x1), width - 1)
        new_y1 = max(int(1.50 * y1 - 0.50 * y2), 0)
        new_y2 = min(int(1.50 * y2 - 0.50 * y1), height - 1)

        # 得到原始图中关键点坐标
        left_eye_x = points[:5][0]
        right_eye_x = points[:5][1]
        nose_x = points[:5][2]
        left_mouth_x = points[:5][3]
        right_mouth_x = points[:5][4]
        left_eye_y = points[5:][0]
        right_eye_y = points[5:][1]
        nose_y = points[5:][2]
        left_mouth_y = points[5:][3]
        right_mouth_y = points[5:][4]

        # 得到外扩100%后图中关键点坐标
        new_left_eye_x = left_eye_x - new_x1
        new_right_eye_x = right_eye_x - new_x1
        new_nose_x = nose_x - new_x1
        new_left_mouth_x = left_mouth_x - new_x1
        new_right_mouth_x = right_mouth_x - new_x1
        new_left_eye_y = left_eye_y - new_y1
        new_right_eye_y = right_eye_y - new_y1
        new_nose_y = nose_y - new_y1
        new_left_mouth_y = left_mouth_y - new_y1
        new_right_mouth_y = right_mouth_y - new_y1

        face_landmarks = [[new_left_eye_x, new_left_eye_y],  # 在扩大100%人脸图中关键点坐标
                          [new_right_eye_x, new_right_eye_y],
                          [new_nose_x, new_nose_y],
                          [new_left_mouth_x, new_left_mouth_y],
                          [new_right_mouth_x, new_right_mouth_y]]
        face = img_im[new_y1: new_y2, new_x1: new_x2]  # 扩大100%的人脸区域
        if self.scale == '112x96':
            dst = warp_im(face, face_landmarks, coord5point1)  # 112x96对齐后尺寸
        elif self.scale == '112x112':
            dst = warp_im(face, face_landmarks, coord5point2)  # 112x112对齐后尺寸
        else:
            raise ValueError("scale must be 112x96 or 112x112")
        crop_im = dst[0:imgSize1[0], 0:imgSize1[1]]
        cv2.imshow("crop_im", crop_im)
        return crop_im

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
                result = self.yolov6_face.predict_shapes(cropped_img)
                key_points = []
                for point_shape in result.shapes:
                    key_points.append(point_shape.points[0])
                key_cropped_img = self.key_transform(image.copy(), shape.points, key_points)
                sam_results.avatars.append(key_cropped_img)  # 添加crop并打点并扭转的人脸图像
            return sam_results

        except Exception as e:  # noqa
            logging.warning("Could not inference model")
            logging.error(e)
            traceback.print_exc()
            return AutoLabelingResult([], replace=False)
