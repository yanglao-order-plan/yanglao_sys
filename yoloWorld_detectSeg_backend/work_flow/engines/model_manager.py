import logging
import os
import copy

import time
import traceback
from idlelib.configdialog import tracers
from importlib.resources import files

import cv2
import mmcv
import yaml

from threading import Lock

from torch.fx.experimental.proxy_tensor import track_tensor

from utils.backend_utils.colorprinter import print_cyan
from work_flow.engines import load_model_class
from work_flow.engines.types import AutoLabelingResult
from work_flow.utils import xyxyxyxy_to_xyxy, base64_img_to_rgb_cv_img
from work_flow.utils.singal import AutoSignal
from work_flow.configs.config import get_config, save_config
from work_flow.configs import auto_labeling as auto_labeling_configs
from .constant import CUSTOM_MODELS, marks_model_list, reset_tracker_model_list, conf_model_list, iou_model_list, \
    preserve_existing_annotations_state_model_list, PARAMS

CONFIG_ROOT = 'work_flow/configs'

# 处理模型预测的全过程，负责回显
class ModelManager:
    """Model manager"""
    MAX_NUM_CUSTOM_MODELS = 5
    model_configs_changed = AutoSignal(list)  # 模型-配置列表
    new_model_status = AutoSignal(str)  # 新载模型-状态
    new_model_status.connect(print_cyan)
    model_loaded = AutoSignal(dict)   # 新载模型-信息
    output_modes_changed = AutoSignal(dict, str)
    def __init__(self):
        super().__init__()
        self.model_index = {}
        self.model_configs = {}
        self.task_configs = {}  # 存放任务配置及其下model_id
        self.loaded_model_config = None
        self.loaded_model_config_lock = Lock()
        self.model_download_thread = None
        self.model_execution_thread = None
        self.model_execution_thread_lock = Lock()
        self.kwargs = {}
        self.post_kwargs = {}

    def load_model_configs(self, releases):
        """Load model configs"""
        for release in releases:
            self.load_model_config(release)

    def load_model_config(self, release):
        self.model_configs[release.id] = release.to_config

    def get_model_configs(self):
        """Return model infos"""
        return self.model_configs

    def get_model_hypers_local(self):
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
        self.kwargs.clear()
        for key, value in hyper.items():
            if key == 'origin_image':
                self.kwargs['image'] = base64_img_to_rgb_cv_img(value)
            elif key == 'mask_image':
                self.kwargs['mask'] = base64_img_to_rgb_cv_img(value)
            elif key == 'minor_image':
                self.kwargs['minor'] = base64_img_to_rgb_cv_img(value)
            elif key == 'shapes_prompt':
                self.set_auto_labeling_marks(value)
            elif key == "conf_threshold":
                self.set_auto_labeling_conf(value)
            elif key == 'sim_threshold':
                self.kwargs['sim_threshold'] = value
            elif key in ['iou_threshold', 'box_threshold']:
                self.set_auto_labeling_iou(value)
            elif key == 'toggle_preserve_existing_annotations':
                self.set_auto_labeling_preserve_existing_annotations_state(value)
            elif key == 'reset_tracker':
                if value:
                    self.set_auto_labeling_reset_tracker()
            elif key == 'output_mode':
                self.set_output_mode(value)
            elif key == 'text_prompt':
                self.kwargs['text_prompt'] = value
            elif key == 'run_tracker':
                self.kwargs['run_tracker'] = value
            elif key == 'mask_enhance':
                self.kwargs['mask_enhance'] = value
            elif key == 'prompt_mode':
                self.kwargs['prompt_mode'] = value
            elif key == 'scale':
                self.kwargs['scale'] = value
            else:
                self.post_kwargs[key] = value

    def set_output_mode(self, mode):
        """Set output mode"""
        if self.loaded_model_config and self.loaded_model_config["model"]:
            self.loaded_model_config["model"].set_output_mode(mode)


    def on_model_download_finished(self):
        """Handle model download thread finished"""
        if self.loaded_model_config and self.loaded_model_config["model"]:
            logging.info("Model loaded. Ready for labeling.")
            logging.info(self.loaded_model_config)
        else:
            self.model_loaded.emit({})

    def load_model_configs_yaml(self):
        """Load model configs"""
        # Load list of default models
        with open(os.path.join(CONFIG_ROOT, 'categorize.yaml'), 'r', encoding='utf-8') as f:
            model_type = yaml.safe_load(f)
        with open(os.path.join(CONFIG_ROOT, 'models.yaml'), 'r', encoding='utf-8') as f:
            model_list = yaml.safe_load(f)

        # Load model configs
        model_configs = []
        for idx, model in enumerate(model_list):
            config_file = model["config_file"]
            if config_file.startswith(":/"):  # Config file is in resources
                config_file_name = config_file[2:]
                with open(os.path.join(CONFIG_ROOT, 'auto_labeling', config_file_name), 'r', encoding='utf-8') as f:
                    model_config = yaml.safe_load(f)
                    model_config["config_file"] = config_file
            else:  # Config file is in local file system
                with open(config_file, "r", encoding="utf-8") as f:
                    model_config = yaml.safe_load(f)
                    model_config["config_file"] = os.path.normpath(
                        os.path.abspath(config_file)
                    )
            model_config["is_custom_model"] = model.get(
                "is_custom_model", False
            )
            tt, t = self.find_model_type(model_config["type"], model_type)
            if tt not in self.task_configs:
                self.task_configs[tt] = {}
            if t not in self.task_configs[tt]:
                self.task_configs[tt][t] = {}
            flow_name = model_config['type']
            release_name = model_config['name']
            release_show_name = model_config['display_name']
            if flow_name not in self.task_configs[tt][t]:
                self.task_configs[tt][t][flow_name] = {}
            self.task_configs[tt][t][flow_name][release_name] = (idx, release_show_name)
            model_config["task_type"] = tt
            model_config["task"] = t

            self.model_configs[idx] = model_config

        # Sort by last used
        for i, model_config in enumerate(model_configs):
            # Keep order for integrated models
            if not model_config.get("is_custom_model", False):
                model_config["last_used"] = -i
            else:
                model_config["last_used"] = model_config.get(
                    "last_used", time.time()
                )
        model_configs.sort(key=lambda x: x.get("last_used", 0), reverse=True)

    def find_model_type(self, model_type, configs):
        for task_type, value in configs.items():
            for task, v in value.items():
                if model_type in v:
                    return task_type, task
        return 'unkown', 'unkown'


    def load_model(self, model_id, config=None):
        """Run model loading in a thread"""
        print_cyan("Loading model: {model_name}. Please wait...".format(
                model_name=self.model_configs[model_id]['display_name']))
        if config is not None:
            self.model_configs[model_id].update(config)
        self._load_model(model_id)

    def _load_model(self, model_id):
        """Load and return model info"""
        model_config = copy.deepcopy(self.model_configs[model_id])
        model_type = model_config.get("type")
        try:
            ModelClass = load_model_class(model_type)
            model_config["model"] = ModelClass(model_config, on_message=self.new_model_status.emit)
            logging.info(f"✅ Model loaded successfully: {model_type}")
        except Exception as e:
            error_message = str(e)
            stack_trace = traceback.format_exc()  # 获取完整的异常堆栈信息
            self.new_model_status.emit(f"Error in loading model: {error_message}")
            logging.error(
                f"❌ Error in loading model: {model_type} with error: {error_message}\nStack trace:\n{stack_trace}")
            return

        self.loaded_model_config = model_config
        return self.loaded_model_config

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

    def set_auto_labeling_marks(self, value):
        """Set auto labeling marks
        (For example, for segment_anything model, it is the marks for)
        """
        if (
            self.loaded_model_config is None
            or self.loaded_model_config["type"] not in marks_model_list
            or value is None
        ):
            return
        marks = []
        for v in value:
            mark = {'type': v['type']}
            if v['type'] == 'point':
                mark['data'] = [v['x'], v['y']]
            elif v['type'] == 'rectangle':
                points = [(p['x'], p['y']) for p in v['points']]
                mark['data'] = xyxyxyxy_to_xyxy(points)
            marks.append(mark)
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
            or value is None
        ):
            return
        self.loaded_model_config["model"].set_auto_labeling_conf(value)

    def set_auto_labeling_iou(self, value):
        """Set auto labeling iou"""
        if (
            self.loaded_model_config is None
            or self.loaded_model_config["type"] not in iou_model_list
            or value is None
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

    def set_auto_labeling_result(self, result):
        self.result = result

    # 之前是qt槽函数，现在是普通的队列设置函数
    def predict_shapes(self):
        """Predict shapes.
        This function starts a thread to run the prediction.
        """
        if self.loaded_model_config is None:
            self.new_model_status.emit("Model is not loaded. Choose a mode to continue.")
            return
        self.new_model_status.emit("Inferencing AI model. Please wait...")
        if (
            self.model_execution_thread is not None
            and self.model_execution_thread.isRunning()
        ):
            self.new_model_status.emit(
                "Another model is being executed."
                " Please wait for it to finish."
            )
            return

        try:
            results = self.loaded_model_config["model"].predict_shapes(**self.kwargs)
            if not hasattr(results, "image") or results.image is None:
                results.image = self.kwargs.get("image")
        except Exception as e:  # noqa
            error_message = str(e)
            stack_trace = traceback.format_exc()  # 获取完整的异常堆栈信息
            self.new_model_status.emit(f"Error in loading model: {error_message}")
            logging.error(f"Error in model prediction: {e}\n{stack_trace}. Please check the model.")
            raise
        print(results)
        results.load_kwargs(**self.post_kwargs)
        return results

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
