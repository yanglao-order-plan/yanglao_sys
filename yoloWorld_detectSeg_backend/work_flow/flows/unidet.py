import os
import sys
import traceback
import logging
import argparse
from typing import Tuple

import cv2
import torch

from . import __preferred_device__, Model, Shape, AutoLabelingResult
from detectron2.config import get_cfg
from work_flow.utils.unidet.config import add_unidet_config
from work_flow.utils.unidet.predictor import UnifiedVisualizationDemo

class UniDet(Model):
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
            "rectangle": "Rectangle",
        }
        default_output_mode = "rectangle"

    def __init__(self, model_config, on_message) -> None:
        # Run the parent class's init method
        super().__init__(model_config, on_message)

        # Get encoder and decoder model paths
        model_abs_path = self.get_model_abs_path(
            self.config, "det_model_path"
        )
        if not model_abs_path or not os.path.isfile(
            model_abs_path
        ):
            raise FileNotFoundError(
                "Could not download or initialize encoder of Unidet."
            )
        args = self.parse_args(model_abs_path)
        args.confidence_threshold = self.config.get("confidence_threshold", 0.25)
        cfg = self.setup_cfg(args)
        self.model = UnifiedVisualizationDemo(cfg)
        # self.model.cpu_device = torch.device(__preferred_device__)

    @staticmethod
    def parse_args(model_abs_path):
        parser = argparse.ArgumentParser(description="Unified Detection Demo")
        parser.add_argument("--device", type=str, default=__preferred_device__, help="The device to run generation on.")

        parser.add_argument(
            "--detection_config",
            default="work_flow/configs/unidet/Unified_learned_OCIM_RS200_6x+2x.yaml",
            metavar="FILE",
            help="path to config file",
        )
        parser.add_argument(
            "--confidence-threshold",
            type=float,
            default=0.5,
            help="Minimum score for instance predictions to be shown",
        )
        parser.add_argument(
            "--opts",
            help="Modify config options using the command-line 'KEY VALUE' pairs",
            default=["MODEL.WEIGHTS",model_abs_path],
            nargs=argparse.REMAINDER,
        )

        return parser.parse_args()

    def setup_cfg(self, args):
        # load config from file and command-line arguments
        cfg = get_cfg()
        add_unidet_config(cfg)
        cfg.merge_from_file(args.detection_config)
        cfg.merge_from_list(args.opts)
        # Set score_threshold for builtin models
        cfg.MODEL.RETINANET.SCORE_THRESH_TEST = args.confidence_threshold
        cfg.MODEL.ROI_HEADS.SCORE_THRESH_TEST = args.confidence_threshold
        cfg.MODEL.PANOPTIC_FPN.COMBINE.INSTANCES_CONFIDENCE_THRESH = args.confidence_threshold
        cfg.freeze()
        return cfg

    def pack_results(self, predictions, visualized_output, new_metadata):
        instances = predictions["instances"]
        boxes = instances.pred_boxes.tensor.tolist()
        scores = instances.scores.tolist()
        classes = instances.pred_classes.tolist()
        class_names = new_metadata
        shapes = []
        for box, score, cls_id in zip(boxes, scores, classes):
            cls_name = class_names[cls_id]
            box = [int(x) for x in box]
            x1, y1, x2, y2 = box
            score = round(score, 2)
            shape = Shape(
                label=cls_name,
                score=score,
                shape_type="rectangle"
            )
            shape.add_point(x1, y1)
            shape.add_point(x2, y1)
            shape.add_point(x2, y2)
            shape.add_point(x1, y2)
            shapes.append(shape)
        return AutoLabelingResult(shapes, replace=True, avatars=[visualized_output.get_image()])

    def pack_raw(self, predictions, visualized_output, new_metadata):
        instances = predictions["instances"]
        boxes = instances.pred_boxes.tensor.tolist()
        scores = instances.scores.tolist()
        classes = instances.pred_classes.tolist()
        data = []
        for box, score, cls_id in zip(boxes, scores, classes):
            cls_name = new_metadata[cls_id]
            box = [round(x, 2) for x in box]
            score = round(score, 2)

            item = {
                "bounding_box": box,
                "type": "UniDet",
                "category_id": cls_id,
                "category_name": cls_name,
                "confidence": score
            }
            data.append(item)
        return data, visualized_output.get_image()

    def predict_shapes(self, image, filename=None, raw=False) -> AutoLabelingResult|Tuple:
        """
        Predict shapes from image
        """
        if image is None:
            return AutoLabelingResult([], replace=False)
        try:
            predictions, visualized_output = self.model.run_on_image(image)
            if raw:
                return self.pack_raw(predictions, visualized_output, self.model.metadata.thing_classes)
            else:
                return self.pack_results(predictions, visualized_output, self.model.metadata.thing_classes)
        except Exception as e:  # noqa
            logging.warning("Could not inference model")
            logging.error(e)
            traceback.print_exc()
            return AutoLabelingResult([], replace=False)
