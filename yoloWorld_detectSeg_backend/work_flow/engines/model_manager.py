import logging
import os
import copy

import time
import yaml

from threading import Lock

from utils.backend_utils.colorprinter import print_cyan
from work_flow.engines.types import AutoLabelingResult
from work_flow.utils.singal import AutoSignal
from work_flow.configs.config import get_config, save_config
from work_flow.configs import auto_labeling as auto_labeling_configs
from .constant import CUSTOM_MODELS, marks_model_list, reset_tracker_model_list, conf_model_list, iou_model_list, \
    preserve_existing_annotations_state_model_list, PARAMS


# 处理模型预测的全过程，负责回显
class ModelManager:
    """Model manager"""
    MAX_NUM_CUSTOM_MODELS = 5
    model_configs_changed = AutoSignal(list)  # 模型-配置列表
    new_model_status = AutoSignal(str)  # 新载模型-状态
    new_model_status.connect(print_cyan)
    model_loaded = AutoSignal(dict)   # 新载模型-信息
    new_auto_labeling_result = AutoSignal(AutoLabelingResult) # 自动标注结果
    auto_segmentation_model_selected = AutoSignal()  # 自动标注结果
    auto_segmentation_model_unselected = AutoSignal()
    prediction_started = AutoSignal()  # 预测开始-标志
    prediction_finished = AutoSignal()  # 预测结束-标志
    request_next_files_requested = AutoSignal()
    output_modes_changed = AutoSignal(dict, str)
    def __init__(self):
        super().__init__()
        self.model_configs = {}

        self.loaded_model_config = None
        self.loaded_model_config_lock = Lock()
        self.model_download_thread = None
        self.model_execution_thread = None
        self.model_execution_thread_lock = Lock()
        self.text_prompt = None

    def load_model_configs(self, releases):
        """Load model configs"""
        for release in releases:
            self.load_model_config(release)

    def load_model_config(self, release):
        self.model_configs[release.id] = release.to_config()

    def get_model_configs(self):
        """Return model infos"""
        return self.model_configs

    def get_model_hypers(self):
        params = []
        widgets = self.loaded_model_config["model"].get_required_widgets()
        output_modes = self.loaded_model_config["model"].Meta.output_modes
        default_output_mode = self.loaded_model_config["model"].Meta.default_output_mode
        for param in PARAMS:
            if param in widgets:
                params.append({'hyperName': param, **PARAMS[param]})
        params.append({
            'hyperName': 'output_modes',
            'hyperType': 'select',
            'hyperDefault': default_output_mode,
            'hyperConfig': {'options': output_modes, 'multiple': False},
        })
        return params

    def set_model_hyper(self, hyper):
        for key, value in hyper.items():
            if  key in ["button_add_point", "button_add_rect"]:
                self.set_auto_labeling_marks(value)
            elif key == "edit_conf":
                self.set_auto_labeling_conf(value)
            elif key == 'edit_iou':
                self.set_auto_labeling_iou(value)
            elif key == 'toggle_preserve_existing_annotations':
                self.set_auto_labeling_preserve_existing_annotations_state(value)
            elif key == 'button_reset_tracker':
                if value:
                    self.set_auto_labeling_reset_tracker()
            elif key == 'edit_text':
                self.text_prompt = value
            elif key == 'output_modes':
                self.set_output_mode(value)
            else:
                raise ValueError(f"Unknown param: {key}")

    def set_output_mode(self, mode):
        """Set output mode"""
        if self.loaded_model_config and self.loaded_model_config["model"]:
            self.loaded_model_config["model"].set_output_mode(mode)

    def on_model_download_finished(self):
        """Handle model download thread finished"""
        if self.loaded_model_config and self.loaded_model_config["model"]:
            self.new_model_status.emit("Model loaded. Ready for labeling.")
            self.model_loaded.emit(self.loaded_model_config)
            self.output_modes_changed.emit(
                self.loaded_model_config["model"].Meta.output_modes,
                self.loaded_model_config["model"].Meta.default_output_mode
            )
        else:
            self.model_loaded.emit({})


    def load_custom_model(self, config_file):
        """Run custom model loading in a thread"""
        config_file = os.path.normpath(os.path.abspath(config_file))
        if (
            self.model_download_thread is not None
            and self.model_download_thread.is_alive()
        ):
            logging.info(
                "Another model is being loaded. Please wait for it to finish."
            )
            return

        # Check config file path
        if not config_file or not os.path.isfile(config_file):
            self.new_model_status.emit(
                "An error occurred while loading the custom model: "
                "The model path is invalid."
            )
            self.new_model_status.emit(
                "Error in loading custom model: Invalid path."
            )
            return

        # Check config file content
        with open(config_file, "r", encoding="utf-8") as f:
            model_config = yaml.safe_load(f)
            model_config["config_file"] = os.path.abspath(config_file)
        if not model_config:
            self.new_model_status.emit(
                "An error occurred while loading the custom model: "
                "The config file is invalid."
            )
            self.new_model_status.emit(
                "Error in loading custom model: Invalid config file."
            )
            return
        if (
            "type" not in model_config
            or "display_name" not in model_config
            or "name" not in model_config
            or model_config["type"] not in CUSTOM_MODELS
        ):
            if "type" not in model_config:
                self.new_model_status.emit(
                    "An error occurred while loading the custom model: "
                    "The 'type' field is missing in the model configuration file."
                )
            elif "display_name" not in model_config:
                self.new_model_status.emit(
                    "An error occurred while loading the custom model: "
                    "The 'display_name' field is missing in the model configuration file."
                )
            elif "name" not in model_config:
                self.new_model_status.emit(
                    "An error occurred while loading the custom model: "
                    "The 'name' field is missing in the model configuration file."
                )
            else:
                self.new_model_status.emit(
                    "An error occurred while loading the custom model: "
                    "The model type {model_config['type']} is not supported."
                )
            self.new_model_status.emit("Error in loading custom model: Invalid config file format.")
            return

        # Add or replace custom model
        custom_models = get_config().get("custom_models", [])
        matched_index = None
        for i, model in enumerate(custom_models):
            if os.path.normpath(model["config_file"]) == os.path.normpath(
                config_file
            ):
                matched_index = i
                break
        if matched_index is not None:
            model_config["last_used"] = time.time()
            custom_models[matched_index] = model_config
        else:
            if len(custom_models) >= self.MAX_NUM_CUSTOM_MODELS:
                custom_models.sort(
                    key=lambda x: x.get("last_used", 0), reverse=True
                )
                custom_models.pop()
            custom_models = [model_config] + custom_models

        # Save config
        config = get_config()
        config["custom_models"] = custom_models
        save_config(config)

        # Reload model configs
        self.load_model_configs()

        # Load model
        self.load_model(model_config["config_file"])

    def load_model(self, model_id, config):
        """Run model loading in a thread"""
        print_cyan("Loading model: {model_name}. Please wait...".format(
                model_name=self.model_configs[model_id]["display_name"]))
        self.model_configs[model_id].update(config)
        self._load_model(model_id)
        # self.model_download_thread = threading.Thread(target=self._load_model, args=(model_id,))
        # self.model_download_thread.start()  # 按理来说，执行完毕，thread状态自动变为dead
        # self.model_download_thread.join()

    #异步方法，耗时加载模型
    def _load_model(self, model_id):  # noqa: C901
        """Load and return model info"""
        if self.loaded_model_config is not None:
            self.loaded_model_config["model"].unload()
            self.loaded_model_config = None
            self.auto_segmentation_model_unselected.emit(None)

        model_config = copy.deepcopy(self.model_configs[model_id])
        if model_config["type"] == "yolov10":
            from work_flow.flows.yolov10 import YOLOv10

            try:
                model_config["model"] = YOLOv10(
                    model_config, on_message=self.new_model_status.emit
                )
                self.auto_segmentation_model_unselected.emit(None)
                self.new_model_status.emit(
                    f"✅ Model loaded successfully: {model_config['type']}"
                )
            except Exception as e:  # noqa
                self.new_model_status.emit(
                    "Error in loading model: {error_message}".format(
                        error_message=str(e)
                    )
                )
                self.new_model_status.emit(
                    f"❌ Error in loading model: {model_config['type']} with error: {str(e)}"
                )
                return
        elif model_config["type"] == "yolo11":
            from work_flow.flows.yolo11 import YOLO11

            try:
                model_config["model"] = YOLO11(
                    model_config, on_message=self.new_model_status.emit
                )
                self.auto_segmentation_model_unselected.emit(None)
                self.new_model_status.emit(
                    f"✅ Model loaded successfully: {model_config['type']}"
                )
            except Exception as e:  # noqa
                self.new_model_status.emit(
                    "Error in loading model: {error_message}".format(
                        error_message=str(e)
                    )
                )
                self.new_model_status.emit(
                    f"❌ Error in loading model: {model_config['type']} with error: {str(e)}"
                )
                return
        elif model_config["type"] == "yolo11_seg":
            from work_flow.flows.yolo11_seg import YOLO11_Seg

            try:
                model_config["model"] = YOLO11_Seg(
                    model_config, on_message=self.new_model_status.emit
                )
                self.auto_segmentation_model_unselected.emit(None)
                logging.info(
                    f"✅ Model loaded successfully: {model_config['type']}"
                )
            except Exception as e:  # noqa
                self.new_model_status.emit(
                    "Error in loading model: {error_message}".format(
                        error_message=str(e)
                    )
                )
                self.new_model_status.emit(
                    f"❌ Error in loading model: {model_config['type']} with error: {str(e)}"
                )
                return
        elif model_config["type"] == "yolov8_obb":
            from work_flow.flows.yolov8_obb import YOLOv8_OBB

            try:
                model_config["model"] = YOLOv8_OBB(
                    model_config, on_message=self.new_model_status.emit
                )
                self.auto_segmentation_model_unselected.emit(None)
                self.new_model_status.emit(
                    f"✅ Model loaded successfully: {model_config['type']}"
                )
            except Exception as e:  # noqa
                self.new_model_status.emit(
                    "Error in loading model: {error_message}".format(
                        error_message=str(e)
                    )
                )
                self.new_model_status.emit(
                    f"❌ Error in loading model: {model_config['type']} with error: {str(e)}"
                )
                return
        elif model_config["type"] == "yolo11_obb":
            from work_flow.flows.yolo11_obb import YOLO11_OBB

            try:
                model_config["model"] = YOLO11_OBB(
                    model_config, on_message=self.new_model_status.emit
                )
                self.auto_segmentation_model_unselected.emit(None)
                self.new_model_status.emit(
                    f"✅ Model loaded successfully: {model_config['type']}"
                )
            except Exception as e:  # noqa
                self.new_model_status.emit(
                    "Error in loading model: {error_message}".format(
                        error_message=str(e)
                    )
                )
                self.new_model_status.emit(
                    f"❌ Error in loading model: {model_config['type']} with error: {str(e)}"
                )
                return
        elif model_config["type"] == "yolo11_pose":
            from work_flow.flows.yolo11_pose import YOLO11_Pose

            try:
                model_config["model"] = YOLO11_Pose(
                    model_config, on_message=self.new_model_status.emit
                )
                self.auto_segmentation_model_unselected.emit(None)
                logging.info(
                    f"✅ Model loaded successfully: {model_config['type']}"
                )
            except Exception as e:  # noqa
                self.new_model_status.emit(
                    "Error in loading model: {error_message}".format(
                        error_message=str(e)
                    )
                )
                self.new_model_status.emit(
                    f"❌ Error in loading model: {model_config['type']} with error: {str(e)}"
                )
                return
        elif model_config["type"] == "grounding_dino":
            from work_flow.flows.grounding_dino import Grounding_DINO

            try:
                model_config["model"] = Grounding_DINO(
                    model_config, on_message=self.new_model_status.emit
                )
                self.auto_segmentation_model_unselected.emit(None)
                logging.info(
                    f"✅ Model loaded successfully: {model_config['type']}"
                )
            except Exception as e:  # noqa
                self.new_model_status.emit(
                    "Error in loading model: {error_message}".format(
                        error_message=str(e)
                    )
                )
                self.new_model_status.emit(
                    f"❌ Error in loading model: {model_config['type']} with error: {str(e)}"
                )
                return
        elif model_config["type"] == "ram":
            from work_flow.flows.ram import RAM

            try:
                model_config["model"] = RAM(
                    model_config, on_message=self.new_model_status.emit
                )
                self.auto_segmentation_model_unselected.emit(None)
                logging.info(
                    f"✅ Model loaded successfully: {model_config['type']}"
                )
            except Exception as e:  # noqa
                self.new_model_status.emit(
                    "Error in loading model: {error_message}".format(
                        error_message=str(e)
                    )
                )
                self.new_model_status.emit(
                    f"❌ Error in loading model: {model_config['type']} with error: {str(e)}"
                )
                return
        elif model_config["type"] == "grounding_sam":
            from work_flow.flows.grounding_sam import GroundingSAM

            try:
                model_config["model"] = GroundingSAM(
                    model_config, on_message=self.new_model_status.emit
                )
                self.auto_segmentation_model_selected.emit(None)
                logging.info(
                    f"✅ Model loaded successfully: {model_config['type']}"
                )
            except Exception as e:  # noqa
                self.new_model_status.emit(
                    f"❌ Error in loading model: {model_config['type']} with error: {str(e)}"
                )
                self.new_model_status.emit(
                    "Error in loading model: {error_message}".format(
                        error_message=str(e)
                    )
                )
                return
            # Request next files for prediction
            self.request_next_files_requested.emit(None)
        elif model_config["type"] == "grounding_sam2":
            from work_flow.flows.grounding_sam2 import GroundingSAM2

            try:
                model_config["model"] = GroundingSAM2(
                    model_config, on_message=self.new_model_status.emit
                )
                self.auto_segmentation_model_selected.emit(None)
                logging.info(
                    f"✅ Model loaded successfully: {model_config['type']}"
                )
            except Exception as e:  # noqa
                self.new_model_status.emit(
                    f"❌ Error in loading model: {model_config['type']} with error: {str(e)}"
                )
                self.new_model_status.emit(
                    "Error in loading model: {error_message}".format(
                        error_message=str(e)
                    )
                )
                return
            # Request next files for prediction
            self.request_next_files_requested.emit(None)
        elif model_config["type"] == "segment_anything":
            from work_flow.flows.segment_anything import SegmentAnything

            try:
                model_config["model"] = SegmentAnything(
                    model_config, on_message=self.new_model_status.emit
                )
                self.auto_segmentation_model_selected.emit(None)
                logging.info(
                    f"✅ Model loaded successfully: {model_config['type']}"
                )
            except Exception as e:  # noqa
                self.new_model_status.emit(
                    f"❌ Error in loading model: {model_config['type']} with error: {str(e)}"
                )
                self.new_model_status.emit(
                    "Error in loading model: {error_message}".format(
                        error_message=str(e)
                    )
                )
                return
            # Request next files for prediction
            self.request_next_files_requested.emit(None)
        elif model_config["type"] == "segment_anything_2":
            from work_flow.flows.segment_anything_2 import SegmentAnything2

            try:
                model_config["model"] = SegmentAnything2(
                    model_config, on_message=self.new_model_status.emit
                )
                self.auto_segmentation_model_selected.emit(None)
                logging.info(
                    f"✅ Model loaded successfully: {model_config['type']}"
                )
            except Exception as e:  # noqa
                self.new_model_status.emit(
                    f"❌ Error in loading model: {model_config['type']} with error: {str(e)}"
                )
                self.new_model_status.emit(
                    "Error in loading model: {error_message}".format(
                        error_message=str(e)
                    )
                )
                return
            # Request next files for prediction
            self.request_next_files_requested.emit(None)

        elif model_config["type"] == "efficientvit_sam":
            from work_flow.flows.efficientvit_sam import EfficientViT_SAM

            try:
                model_config["model"] = EfficientViT_SAM(
                    model_config, on_message=self.new_model_status.emit
                )
                self.auto_segmentation_model_selected.emit(None)
                logging.info(
                    f"✅ Model loaded successfully: {model_config['type']}"
                )
            except Exception as e:  # noqa
                self.new_model_status.emit(
                    f"❌ Error in loading model: {model_config['type']} with error: {str(e)}"
                )
                self.new_model_status.emit(
                    "Error in loading model: {error_message}".format(
                        error_message=str(e)
                    )
                )
                return
            # Request next files for prediction
            self.request_next_files_requested.emit(None)
        elif model_config["type"] == "edge_sam":
            from work_flow.flows.edge_sam import EdgeSAM

            try:
                model_config["model"] = EdgeSAM(
                    model_config, on_message=self.new_model_status.emit
                )
                self.auto_segmentation_model_selected.emit(None)
                logging.info(
                    f"✅ Model loaded successfully: {model_config['type']}"
                )
            except Exception as e:  # noqa
                self.new_model_status.emit(
                    f"❌ Error in loading model: {model_config['type']} with error: {str(e)}"
                )
                self.new_model_status.emit(
                    "Error in loading model: {error_message}".format(
                        error_message=str(e)
                    )
                )
                return
            # Request next files for prediction
            self.request_next_files_requested.emit(None)
        elif model_config["type"] == "sam_hq":
            from work_flow.flows.sam_hq import SAM_HQ

            try:
                model_config["model"] = SAM_HQ(
                    model_config, on_message=self.new_model_status.emit
                )
                self.auto_segmentation_model_selected.emit()
                logging.info(
                    f"✅ Model loaded successfully: {model_config['type']}"
                )
            except Exception as e:  # noqa
                self.new_model_status.emit(
                    f"❌ Error in loading model: {model_config['type']} with error: {str(e)}"
                )
                self.new_model_status.emit(
                    "Error in loading model: {error_message}".format(
                        error_message=str(e)
                    )
                )
                return
            # Request next files for prediction
            self.request_next_files_requested.emit(None)
        elif model_config["type"] == "ppocr_v4":
            from work_flow.flows.ppocr_v4 import PPOCRv4

            try:
                model_config["model"] = PPOCRv4(
                    model_config, on_message=self.new_model_status.emit
                )
                self.auto_segmentation_model_unselected.emit(None)
                logging.info(
                    f"✅ Model loaded successfully: {model_config['type']}"
                )
            except Exception as e:  # noqa
                self.new_model_status.emit(
                    "Error in loading model: {error_message}".format(
                        error_message=str(e)
                    )
                )
                self.new_model_status.emit(
                    f"❌ Error in loading model: {model_config['type']} with error: {str(e)}"
                )
                return

        elif model_config["type"] == "yolo11_cls":
            from work_flow.flows.yolo11_cls import YOLO11_CLS

            try:
                model_config["model"] = YOLO11_CLS(
                    model_config, on_message=self.new_model_status.emit
                )
                self.auto_segmentation_model_unselected.emit(None)
                logging.info(
                    f"✅ Model loaded successfully: {model_config['type']}"
                )
            except Exception as e:  # noqa
                self.new_model_status.emit(
                    "Error in loading model: {error_message}".format(
                        error_message=str(e)
                    )
                )
                self.new_model_status.emit(
                    f"❌ Error in loading model: {model_config['type']} with error: {str(e)}"
                )
                return

        elif model_config["type"] == "yolo11_det_track":
            from work_flow.flows.yolo11_det_track import YOLO11_Det_Tracker

            try:
                model_config["model"] = YOLO11_Det_Tracker(
                    model_config, on_message=self.new_model_status.emit
                )
                self.auto_segmentation_model_unselected.emit(None)
                logging.info(
                    f"✅ Model loaded successfully: {model_config['type']}"
                )
            except Exception as e:  # noqa
                self.new_model_status.emit(
                    "Error in loading model: {error_message}".format(
                        error_message=str(e)
                    )
                )
                self.new_model_status.emit(
                    f"❌ Error in loading model: {model_config['type']} with error: {str(e)}"
                )
                return

        elif model_config["type"] == "yolo11_seg_track":
            from work_flow.flows.yolo11_seg_track import YOLO11_Seg_Tracker

            try:
                model_config["model"] = YOLO11_Seg_Tracker(
                    model_config, on_message=self.new_model_status.emit
                )
                self.auto_segmentation_model_unselected.emit(None)
                logging.info(
                    f"✅ Model loaded successfully: {model_config['type']}"
                )
            except Exception as e:  # noqa
                self.new_model_status.emit(
                    "Error in loading model: {error_message}".format(
                        error_message=str(e)
                    )
                )
                self.new_model_status.emit(
                    f"❌ Error in loading model: {model_config['type']} with error: {str(e)}"
                )
                return

        elif model_config["type"] == "yolo11_obb_track":
            from work_flow.flows.yolo11_obb_track import YOLO11_Obb_Tracker

            try:
                model_config["model"] = YOLO11_Obb_Tracker(
                    model_config, on_message=self.new_model_status.emit
                )
                self.auto_segmentation_model_unselected.emit(None)
                logging.info(
                    f"✅ Model loaded successfully: {model_config['type']}"
                )
            except Exception as e:  # noqa
                self.new_model_status.emit(
                    "Error in loading model: {error_message}".format(
                        error_message=str(e)
                    )
                )
                self.new_model_status.emit(
                    f"❌ Error in loading model: {model_config['type']} with error: {str(e)}"
                )
                return

        elif model_config["type"] == "yolo11_pose_track":
            from work_flow.flows.yolo11_pose_track import YOLO11_Pose_Tracker

            try:
                model_config["model"] = YOLO11_Pose_Tracker(
                    model_config, on_message=self.new_model_status.emit
                )
                self.auto_segmentation_model_unselected.emit(None)
                logging.info(
                    f"✅ Model loaded successfully: {model_config['type']}"
                )
            except Exception as e:  # noqa
                self.new_model_status.emit(
                    "Error in loading model: {error_message}".format(
                        error_message=str(e)
                    )
                )
                self.new_model_status.emit(
                    f"❌ Error in loading model: {model_config['type']} with error: {str(e)}"
                )
                return
        elif model_config["type"] == "rmbg":
            from work_flow.flows.rmbg import RMBG

            try:
                model_config["model"] = RMBG(
                    model_config, on_message=self.new_model_status.emit
                )
                self.auto_segmentation_model_unselected.emit(None)
                logging.info(
                    f"✅ Model loaded successfully: {model_config['type']}"
                )
            except Exception as e:  # noqa
                self.new_model_status.emit(
                    "Error in loading model: {error_message}".format(
                        error_message=str(e)
                    )
                )
                self.new_model_status.emit(
                    f"❌ Error in loading model: {model_config['type']} with error: {str(e)}"
                )
                return
        elif model_config["type"] == "depth_anything":
            from work_flow.flows.depth_anything import DepthAnything

            try:
                model_config["model"] = DepthAnything(
                    model_config, on_message=self.new_model_status.emit
                )
                self.auto_segmentation_model_unselected.emit(None)
                logging.info(
                    f"✅ Model loaded successfully: {model_config['type']}"
                )
            except Exception as e:  # noqa
                self.new_model_status.emit(
                    "Error in loading model: {error_message}".format(
                        error_message=str(e)
                    )
                )
                self.new_model_status.emit(
                    f"❌ Error in loading model: {model_config['type']} with error: {str(e)}"
                )
                return
        elif model_config["type"] == "depth_anything_v2":
            from work_flow.flows.depth_anything_v2 import DepthAnythingV2

            try:
                model_config["model"] = DepthAnythingV2(
                    model_config, on_message=self.new_model_status.emit
                )
                self.auto_segmentation_model_unselected.emit(None)
                logging.info(
                    f"✅ Model loaded successfully: {model_config['type']}"
                )
            except Exception as e:  # noqa
                self.new_model_status.emit(
                    "Error in loading model: {error_message}".format(
                        error_message=str(e)
                    )
                )
                self.new_model_status.emit(
                    f"❌ Error in loading model: {model_config['type']} with error: {str(e)}"
                )
                return
        else:
            raise Exception(f"Unknown model type: {model_config['type']}")

        self.loaded_model_config = model_config
        self.on_model_download_finished()

    def set_cache_auto_label(self, text, gid):
        """Set cache auto label"""
        valid_models = [
            "segment_anything_2_video",
        ]
        if (
            self.loaded_model_config is not None
            and self.loaded_model_config["type"] in valid_models
        ):
            self.loaded_model_config["model"].set_cache_auto_label(text, gid)

    def set_auto_labeling_marks(self, marks):
        """Set auto labeling marks
        (For example, for segment_anything model, it is the marks for)
        """
        if (
            self.loaded_model_config is None
            or self.loaded_model_config["type"] not in marks_model_list
        ):
            return
        self.loaded_model_config["model"].set_auto_labeling_marks(marks)

    def set_auto_labeling_reset_tracker(self):
        """Resets the tracker to its initial state,
        clearing all tracked objects and internal states.
        """
        if (
            self.loaded_model_config is None
            or self.loaded_model_config["type"] not in reset_tracker_model_list
        ):
            return
        self.loaded_model_config["model"].set_auto_labeling_reset_tracker()

    def set_auto_labeling_conf(self, value):
        """Set auto labeling confidences"""
        if (
            self.loaded_model_config is None
            or self.loaded_model_config["type"] not in conf_model_list
        ):
            return
        self.loaded_model_config["model"].set_auto_labeling_conf(value)

    def set_auto_labeling_iou(self, value):
        """Set auto labeling iou"""
        if (
            self.loaded_model_config is None
            or self.loaded_model_config["type"] not in iou_model_list
        ):
            return
        self.loaded_model_config["model"].set_auto_labeling_iou(value)

    def set_auto_labeling_preserve_existing_annotations_state(self, state):

        if (
            self.loaded_model_config is not None
            and self.loaded_model_config["type"] in preserve_existing_annotations_state_model_list
        ):
            self.loaded_model_config[
                "model"
            ].set_auto_labeling_preserve_existing_annotations_state(state)

    def set_auto_labeling_prompt(self):
        model_list = ["segment_anything_2_video"]
        if (
            self.loaded_model_config is not None
            and self.loaded_model_config["type"] in model_list
        ):
            self.loaded_model_config["model"].set_auto_labeling_prompt()

    def unload_model(self):
        """Unload model"""
        if self.loaded_model_config is not None:
            self.loaded_model_config["model"].unload()
            self.loaded_model_config = None

    def predict_shapes(
        self, image, filename=None, text_prompt=None, run_tracker=False
    ):
        """Predict shapes.
        NOTE: This function is blocking. The model can take a long time to
        predict. So it is recommended to use predict_shapes_threading instead.
        """
        if self.loaded_model_config is None:
            self.new_model_status.emit("Model is not loaded. Choose a mode to continue.")
            self.prediction_finished.emit(None)
            return
        auto_labeling_result = None
        try:
            if text_prompt is not None:
                auto_labeling_result = self.loaded_model_config[
                    "model"
                ].predict_shapes(image, filename, text_prompt=text_prompt)
            elif run_tracker is True:
                auto_labeling_result = self.loaded_model_config[
                    "model"
                ].predict_shapes(image, filename, run_tracker=run_tracker)
            else:
                auto_labeling_result = self.loaded_model_config[
                    "model"
                ].predict_shapes(image, filename)  # 如果含有媒体的类不支持serial，那就难办了
            self.new_model_status.emit("Finished inferencing AI model. Check the result.")
        except Exception as e:  # noqa
            self.new_model_status.emit(f"Error in predict_shapes: {e}")
            self.new_model_status.emit(f"Error in model prediction: {e}. Please check the model.")
        self.prediction_finished.emit(None)
        return auto_labeling_result

    def set_auto_labeling_result(self, result):
        self.result = result

    # 之前是qt槽函数，现在是普通的队列设置函数
    def predict_shapes_threading(
        self, image, filename=None, run_tracker=False
    ):
        """Predict shapes.
        This function starts a thread to run the prediction.
        """
        if self.loaded_model_config is None:
            self.new_model_status.emit("Model is not loaded. Choose a mode to continue.")
            return
        self.new_model_status.emit("Inferencing AI model. Please wait...")
        self.prediction_started.emit(None)
        self.new_auto_labeling_result.connect(self.set_auto_labeling_result)
        with self.model_execution_thread_lock:
            if (
                self.model_execution_thread is not None
                and self.model_execution_thread.isRunning()
            ):
                self.new_model_status.emit(
                    "Another model is being executed."
                    " Please wait for it to finish."
                )
                self.prediction_finished.emit(None)
                return

            if self.text_prompt is not None:
                return self.predict_shapes(image, filename, text_prompt=self.text_prompt)
            elif run_tracker is True:
                return self.predict_shapes(image, filename, run_tracker=run_tracker)
            else:
                return self.predict_shapes(image, filename)


    def on_next_files_changed(self, next_files):
        """Run prediction on next files in advance to save inference time later"""
        if self.loaded_model_config is None:
            return

        # Currently only segment_anything-like model supports this feature
        if self.loaded_model_config["type"] not in [
            "segment_anything",
            "segment_anything_2",
            "sam_med2d",
            "sam_hq",
            "yolov5_sam",
            "efficientvit_sam",
            "yolov8_efficientvit_sam",
            "grounding_sam",
            "grounding_sam2",
            "edge_sam",
        ]:
            return

        self.loaded_model_config["model"].on_next_files_changed(next_files)

if  __name__ == "__main__":
    model_manager = ModelManager()
