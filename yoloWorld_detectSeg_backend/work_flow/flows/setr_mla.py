import os
import random
import sys
import traceback
import logging
import argparse

import mmcv
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
            self.config, "seg_model_path"
        )
        print(model_abs_path)
        if not model_abs_path or not os.path.isfile(
            model_abs_path
        ):
            raise FileNotFoundError(
                "Could not download or initialize encoder of setr_mla."
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
                            default="work_flow/configs/SER_MLA/SETR_MLA_768x768_80k_base.py",
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
                            default="work_flow/configs/SER_MLA/color_list.npy")
        return parser.parse_args()

    def post_process(self, masks, classes, colors, image=None):
        """
        Post process masks
        输入: 每个蒙版的范围、类别、颜色
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
        for i, (approx, cls, color) in enumerate(zip(approx_contours, classes, colors)):
            if self.output_mode == "polygon":
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
            elif self.output_mode in ["rectangle", "rotation"]:
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
                if self.clip_net is not None and self.classes:
                    img = image[y_min:y_max, x_min:x_max]
                    out = self.clip_net(img, self.classes)
                    shape.cache_label = self.classes[int(np.argmax(out))]
            else:
                raise ValueError(f"Invalid output mode: {self.output_mode}")
            shape.closed = True
            shape.fill_color = color
            shape.line_color = color
            shape.line_width = 1
            shape.selected = False
            shapes.append(shape)

        return shapes

    def color_mask(self, img, seg):
        masks, classes, colors = [], [], []
        color_seg = np.zeros((seg.shape[0], seg.shape[1], 3), dtype=np.uint8)
        for label, color in enumerate(self.color_list):  # catagory之前外的label与color分配
            color_seg[seg == label, :] = self.color_list[label]
            mask = np.zeros((seg.shape[0], seg.shape[1]), dtype=np.uint8)
            mask[seg == label] = 255
            if np.any(mask == 255):
                masks.append(mask)
                classes.append(label)
                colors.append(color)
        # 蒙版分割效果
        img = img * 0.5 + color_seg * 0.5
        img = img.astype(np.uint8)
        cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        # mmcv.imwrite(img, "output/pred_vis.png")
        # mmcv.imwrite(seg, "output/pred_mask.png")
        return masks, classes, colors, img

    def predict_raw(self, image):
        self.model.to(__preferred_device__)
        result = inference_model(self.model, image)
        self.model.to('cpu')
        seg = result.pred_sem_seg.data.cpu().numpy()[0]
        return seg

    def predict_shapes(self, image, filename=None) -> AutoLabelingResult:
        """
        Predict shapes from image
        """
        if image is None:
            return AutoLabelingResult([], replace=False)

        try:
            seg = self.predict_raw(image)
            masks, classes, colors, pred_vis = self.color_mask(image.copy(), seg)
            shapes = self.post_process(masks, classes, colors, image)
        except Exception as e:  # noqa
            logging.warning("Could not inference model")
            logging.error(e)
            traceback.print_exc()
            return AutoLabelingResult([], replace=False)

        result = AutoLabelingResult(shapes, replace=False, avatars=[pred_vis])
        return result