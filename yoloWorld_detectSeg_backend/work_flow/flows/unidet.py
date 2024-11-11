import os
import sys
import traceback
import logging
import argparse

import cv2

from . import __preferred_device__, Model,SegmentAnythingONNX, LRUCache, Shape, ChineseClipONNX, AutoLabelingResult
from ..engines import OnnxBaseModel
from ..utils import is_possible_rectangle
from UNIDET.detectron2.detectron2.config import get_cfg
from UNIDET.unidet.config import add_unidet_config
from UNIDET.unidet.predictor import UnifiedVisualizationDemo
sys.path.append('.')
sys.path.append('./UNIDET/detectron2')

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
        args.confidence_threshold = self.config.get("confidence_threshold", 0.25)
        cfg = self.setup_cfg(args)
        self.model = UnifiedVisualizationDemo(cfg)

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

    def pack_results(self, predictions, new_metadata):
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
        return AutoLabelingResult(shapes, replace=True)


    def predict_shapes(self, image, filename=None) -> AutoLabelingResult:
        """
        Predict shapes from image
        """
        if image is None:
            return AutoLabelingResult([], replace=False)

        try:
            bgr_img = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
            predictions, _ = self.model.run_on_image(bgr_img)
            return self.pack_results(predictions, self.model.metadata.thing_classes)
        except Exception as e:  # noqa
            logging.warning("Could not inference model")
            logging.error(e)
            traceback.print_exc()
            return AutoLabelingResult([], replace=False)
