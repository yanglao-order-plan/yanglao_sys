import os
import sys
import traceback
import logging
import argparse

import numpy as np
from mmengine.runner import load_checkpoint

from mmseg.apis import init_model, inference_model
import cv2
import mmengine
import torch
from mmengine import DictAction

from . import __preferred_device__, Model, Shape, AutoLabelingResult
from ..__base__.clip import ChineseClipONNX
from ..utils.segment_anything import sam_model_registry, SamAutomaticMaskGenerator

sys.path.append('.')
sys.path.append('./UNIDET/detectron2')

class SETR_MLA(Model):
    """Segmentation model using SegmentAnything"""

    class Meta:
        required_config_names = [
            "type",
            "name",
            "display_name",
            "model_path",
        ]
        widgets = [
            "edit_conf",
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
                "Could not download or initialize encoder of Unidet."
            )
        args = self.parse_args(model_abs_path)
        cfg = mmengine.Config.fromfile(args.semantic_config)
        if args.options is not None:
            cfg.merge_from_dict(args.options)
        # set cudnn_benchmark
        if cfg.get('cudnn_benchmark', False):
            torch.backends.cudnn.benchmark = True
        if args.aug_test:
            # hard code index
            cfg.data.test.pipeline[1].img_ratios = [
                0.5, 0.75, 1.0, 1.25, 1.5, 1.75
            ]
            cfg.data.test.pipeline[1].flip = True
        cfg.model.pretrained = None
        cfg.data.test.test_mode = True
        self.model = init_model(args.semantic_config, args.semantic_checkpoint)
        load_checkpoint(self.model, args.semantic_checkpoint, map_location=__preferred_device__)


        # # sam enhance
        # self.sam = None
        self.enhance_mask = self.config.get("enhance_mask", False)
        if self.enhance_mask:
            model_type = self.config.get("model_type", None)
            sam_model_abs_path = self.get_model_abs_path(
                self.config, "sam_model_path"
            )
            sam = sam_model_registry[model_type](checkpoint=sam_model_abs_path)
            self.sam = SamAutomaticMaskGenerator(sam, output_mode='binary_mask')

        # if args.mask_enhance:
        # color reader
        self.color_list = np.load(args.color_list_path)  # get id-color
        self.color_list[0] = [238, 239, 20]  # set special backgrond color

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

    @staticmethod
    def parse_args(model_abs_path):
        parser = argparse.ArgumentParser()
        parser.add_argument('--semantic_config',
                            default="F:\Github\DetectSegPlatform\yoloWorld_detectSeg_backend\work_flow\configs\SER_MLA\SETR_MLA_768x768_80k_base.py",
                            help='test config file path of mmseg')
        parser.add_argument('--semantic_checkpoint',
                            default=model_abs_path,
                            help='checkpoint file of mmseg')
        parser.add_argument(
            '--aug-test', default=True, help='Use Flip and Multi scale aug')
        parser.add_argument(
            "--mask-enhance",
            type=bool,
            default=False,
            help="whether to enhance the mask in semantic segmentation",
        )
        parser.add_argument("--device", type=str, default="cuda", help="The device to run generation on.")
        parser.add_argument(
            '--options', nargs='+', action=DictAction, help='custom options')
        parser.add_argument('--color_list_path', type=str,
                            default="F:\Github\DetectSegPlatform\yoloWorld_detectSeg_backend\work_flow\configs\SER_MLA\color_list.npy")

        return parser.parse_args()

    def post_process(self, masks, classes, colors, image=None):
        """
        Post process masks
        """
        # Find contours
        approx_contours = []
        for mask in masks:
            mask[mask > 0.0] = 255
            mask[mask <= 0.0] = 0
            mask = mask.astype(np.uint8)
            contours, _ = cv2.findContours(
                mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE
            )
            max_contour = max(contours, key=cv2.contourArea)
            # Refine contours 对每个mask直接最大外接
            epsilon = 0.001 * cv2.arcLength(max_contour, True)
            approx = cv2.approxPolyDP(max_contour, epsilon, True)
            approx_contours.append(approx)
        # Remove too big contours ( >90% of image size)
        if len(approx_contours) > 1:
            image_size = masks[0].shape[0] * masks[0].shape[1]
            areas = [cv2.contourArea(contour) for contour in approx_contours]
            avg_area = np.mean(areas)
            filtered_approx_contours, filtered_classes, filtered_colors = [], [], []
            for contour, area, cls, color in zip(approx_contours, areas, classes, colors):
                if area < image_size * 0.9 or area > avg_area * 0.2:
                    filtered_approx_contours.append(contour)
                    filtered_classes.append(cls)
                    filtered_colors.append(color)

            approx_contours = filtered_approx_contours
            classes = filtered_classes
            colors = filtered_colors
        # Contours to shapes
        shapes = []
        if self.output_mode == "polygon":
            for i, (approx, cls, color) in enumerate(zip(approx_contours, classes, colors)):
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
                shape.fill_color = color
                shape.line_color = color
                shape.line_width = 1
                shape.label = f"AUTOLABEL_OBJECT: {i}"
                shape.selected = False
                shapes.append(shape)
        elif self.output_mode in ["rectangle", "rotation"]:
            for i, (approx, cls, color) in enumerate(zip(approx_contours, classes, colors)):
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
                shape.fill_color = color
                shape.line_color = color
                shape.line_width = 1
                if self.clip_net is not None and self.classes:
                    img = image[y_min:y_max, x_min:x_max]
                    out = self.clip_net(img, self.classes)
                    shape.cache_label = self.classes[int(np.argmax(out))]
                shape.label = f"AUTOLABEL_OBJECT: {i}"
                shape.selected = False
                shapes.append(shape)

        return shapes

    def enhance_masks(self, masks, image):
        # auto sam推理
        data = self.sam.generate(image)
        for meta in data:
            single_mask = sam_mask_data[i]
            single_mask_labels = pred_mask_img[single_mask] # 像素计数
            unique_values, counts = np.unique(single_mask_labels, return_counts=True, axis=0)
            max_idx = np.argmax(counts) # 语义像素id+sam像素轮廓
            single_mask_category_label = unique_values[max_idx]
            count_ratio = counts[max_idx] / counts.sum() # 增强比例（当前最多像素，其数量的百分比）

    def predict_shapes(self, image, filename=None) -> AutoLabelingResult:
        """
        Predict shapes from image
        """
        if image is None:
            return AutoLabelingResult([], replace=False)

        try:
            result = inference_model(self.model, image)
            seg = result.pred_sem_seg.data.cpu().numpy()[0]
            masks, classes, colors = [], [], []
            color_seg = np.zeros((seg.shape[0], seg.shape[1], 3), dtype=np.uint8)

            for label, color in enumerate(self.color_list):  # seg的第一维即是label的id
                color_seg[seg == label, :] = self.color_list[label]
                mask = np.zeros((seg.shape[0], seg.shape[1]), dtype=np.uint8)
                mask[seg == label] = 255
                if np.any(mask == 255):
                    masks.append(mask)
                    classes.append(label)
                    colors.append(color)

            if self.enhance_mask:
                masks = self.enhance_masks(masks, image)

            shapes = self.post_process(masks, classes, colors, image)
        except Exception as e:  # noqa
            logging.warning("Could not inference model")
            logging.error(e)
            traceback.print_exc()
            return AutoLabelingResult([], replace=False)
        
        result = AutoLabelingResult(shapes, replace=False)
        return result