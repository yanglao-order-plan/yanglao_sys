from utils.backend_utils.colorprinter import print_red
from work_flow.__base__.sam2 import SegmentAnything2ONNX
from work_flow.app_info import __preferred_device__
from work_flow.engines.model import Model
from work_flow.engines.types import AutoLabelingResult
from work_flow.utils.shape import Shape
from work_flow.engines.build_onnx_engine import OnnxBaseModel
from work_flow.__base__.sam import EdgeSAMONNX
from work_flow.__base__.clip import ChineseClipONNX
from work_flow.__base__.yolo import YOLO
from work_flow.utils.general import Args, is_possible_rectangle
import work_flow.configs as configs
from work_flow.utils import softmax
from work_flow.utils.ppocr_utils.text_system import TextSystem
from work_flow.__base__.ram import RecognizeAnything
from work_flow.utils.points_conversion import cxywh2xyxy, xywh2xyxy
from work_flow.pose.rtmo_onnx import RTMO
from work_flow.__base__.rtmdet import RTMDet
from work_flow.flows.lru_cache import LRUCache
from work_flow.flows.sam_onnx import SegmentAnythingONNX
from work_flow.__base__.sam2 import build_sam2, build_sam2_camera_predictor
from work_flow.__base__.sam2_image_predictor import SAM2ImagePredictor
from work_flow.utils.general import letterbox
from work_flow.utils.points_conversion import rbox2poly
from work_flow.utils import numpy_nms, xywh2xyxy, rescale_box_and_landmark
from work_flow.utils.sahi.predict import get_sliced_prediction
from work_flow.utils.sahi.models.yolov8_onnx import Yolov8OnnxDetectionModel
from work_flow.pose.dwpose_onnx import inference_pose