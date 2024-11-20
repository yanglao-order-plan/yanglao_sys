import torch

from .build_onnx_engine import OnnxBaseModel
from .build_dnn_engine import DnnBaseModel

import importlib


def load_model_class(model_type):
    if model_type not in model_module_map:
        raise ValueError(f"Unknown model type: {model_type}")

    module_path, class_name = model_module_map[model_type]
    module = importlib.import_module(module_path)
    model_class = getattr(module, class_name)
    return model_class

def clear_gpu_memory():
    torch.cuda.empty_cache()
    torch.cuda.synchronize()
    print("GPU memory cleared.")

# 模型类型到模块路径和类名的完整映射
model_module_map = {
    "yolov5": ("work_flow.flows.yolov5", "YOLOv5"),
    "yolov6": ("work_flow.flows.yolov6", "YOLOv6"),
    "yolov7": ("work_flow.flows.yolov7", "YOLOv7"),
    "yolov8": ("work_flow.flows.yolov8", "YOLOv8"),
    "yolov8_sahi": ("work_flow.flows.yolov8_sahi", "YOLOv8_SAHI"),
    "yolov8_seg": ("work_flow.flows.yolov8_seg", "YOLOv8_Seg"),
    "yolov9": ("work_flow.flows.yolov9", "YOLOv9"),
    "yolov10": ("work_flow.flows.yolov10", "YOLOv10"),
    "yolo11": ("work_flow.flows.yolo11", "YOLO11"),
    "yolow": ("work_flow.flows.yolow", "YOLOW"),
    "yolov5_seg": ("work_flow.flows.yolov5_seg", "YOLOv5_Seg"),
    "yolov5_ram": ("work_flow.flows.yolov5_ram", "YOLOv5_RAM"),
    "yolow_ram": ("work_flow.flows.yolow_ram", "YOLOW_RAM"),
    "yolo_nas": ("work_flow.flows.yolo_nas", "YOLO_NAS"),
    "damo_yolo": ("work_flow.flows.damo_yolo", "DAMO_YOLO"),
    "gold_yolo": ("work_flow.flows.gold_yolo", "Gold_YOLO"),
    "grounding_dino": ("work_flow.flows.grounding_dino", "Grounding_DINO"),
    "ram": ("work_flow.flows.ram", "RAM"),
    "internimage_cls": ("work_flow.flows.internimage_cls", "InternImage_CLS"),
    "pulc_attribute": ("work_flow.flows.pulc_attribute", "PULC_Attribute"),
    "yolov5_sam": ("work_flow.flows.yolov5_sam", "YOLOv5SegmentAnything"),
    "yolov8_efficientvit_sam": ("work_flow.flows.yolov8_efficientvit_sam", "YOLOv8_EfficientViT_SAM"),
    "grounding_sam_hq": ("work_flow.flows.grounding_sam", "GroundingSAM"),
    "grounding_sam2": ("work_flow.flows.grounding_sam2", "GroundingSAM2"),
    "open_vision": ("work_flow.flows.open_vision", "OpenVision"),
    "doclayout_yolo": ("work_flow.flows.doclayout_yolo", "DocLayoutYOLO"),
    "yolov5_obb": ("work_flow.flows.yolov5_obb", "YOLOv5OBB"),
    "segment_anything": ("work_flow.flows.segment_anything", "SegmentAnything"),
    "segment_anything_2": ("work_flow.flows.segment_anything_2", "SegmentAnything2"),
    "segment_anything_2_video": ("work_flow.flows.segment_anything_2_video", "SegmentAnything2Video"),
    "efficientvit_sam": ("work_flow.flows.efficientvit_sam", "EfficientViT_SAM"),
    "sam_med2d": ("work_flow.flows.sam_med2d", "SAM_Med2D"),
    "edge_sam": ("work_flow.flows.edge_sam", "EdgeSAM"),
    "sam_hq": ("work_flow.flows.sam_hq", "SAM_HQ"),
    "yolov5_resnet": ("work_flow.flows.yolov5_resnet", "YOLOv5_ResNet"),
    "rtdetr": ("work_flow.flows.rtdetr", "RTDETR"),
    "rtdetrv2": ("work_flow.flows.rtdetrv2", "RTDETRv2"),
    "yolov6_face": ("work_flow.flows.yolov6_face", "YOLOv6Face"),
    "yolox_dwpose": ("work_flow.flows.yolox_dwpose", "YOLOX_DWPose"),
    "rtmdet_pose": ("work_flow.flows.rtmdet_pose", "RTMDet_Pose"),
    "clrnet": ("work_flow.flows.clrnet", "CLRNet"),
    "ppocr_v4": ("work_flow.flows.ppocr_v4", "PPOCRv4"),
    "yolov5_cls": ("work_flow.flows.yolov5_cls", "YOLOv5_CLS"),
    "yolov5_car_plate": ("work_flow.flows.yolov5_car_plate", "YOLOv5CarPlateDetRec"),
    "yolov8_cls": ("work_flow.flows.yolov8_cls", "YOLOv8_CLS"),
    "yolo11_cls": ("work_flow.flows.yolo11_cls", "YOLO11_CLS"),
    "yolov5_det_track": ("work_flow.flows.yolov5_det_track", "YOLOv5_Det_Tracker"),
    "yolov8_det_track": ("work_flow.flows.yolov8_det_track", "YOLOv8_Det_Tracker"),
    "yolo11_det_track": ("work_flow.flows.yolo11_det_track", "YOLO11_Det_Tracker"),
    "yolov8_seg_track": ("work_flow.flows.yolov8_seg_track", "YOLOv8_Seg_Tracker"),
    "yolo11_seg_track": ("work_flow.flows.yolo11_seg_track", "YOLO11_Seg_Tracker"),
    "yolov8_obb_track": ("work_flow.flows.yolov8_obb_track", "YOLOv8_Obb_Tracker"),
    "yolo11_obb_track": ("work_flow.flows.yolo11_obb_track", "YOLO11_Obb_Tracker"),
    "yolov8_pose_track": ("work_flow.flows.yolov8_pose_track", "YOLOv8_Pose_Tracker"),
    "yolo11_pose_track": ("work_flow.flows.yolo11_pose_track", "YOLO11_Pose_Tracker"),
    "rmbg": ("work_flow.flows.rmbg", "RMBG"),
    "depth_anything": ("work_flow.flows.depth_anything", "DepthAnything"),
    "depth_anything_v2": ("work_flow.flows.depth_anything_v2", "DepthAnythingV2"),
    "lama": ("work_flow.flows.lama", "Lama"),
    "ppocr_v4_lama": ("work_flow.flows.ppocr_v4_lama", "PPOCRv4LAMA"),
    "unidet": ("work_flow.flows.unidet", "UniDet"),
    "setr_mla": ("work_flow.flows.setr_mla", "SETR_MLA"),
    "clip": ("work_flow.flows.chinese_clip", "ChineseCLIP"),
    "automatic_segment_anything": ("work_flow.flows.auto_sam", "AutoSAM"),
    "sam_panoptic": ("work_flow.flows.sam_panoptic", "SAM_Panoptic"),
    "ram_grounding_dino": ("work_flow.flows.ram_grounding_dino", "RAM_Grounding_DINO"),
    "arcface": ("work_flow.flows.arcface", "Arc_Face"),
}