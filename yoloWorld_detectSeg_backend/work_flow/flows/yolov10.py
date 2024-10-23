

from work_flow.__base__.yolo import YOLO


class YOLOv10(YOLO):
    class Meta:
        required_config_names = [
            "type",
            "name",
            "display_name",
            "model_path",
        ]
        widgets = [
            "button_run",
            "input_conf",
            "edit_conf",
            "toggle_preserve_existing_annotations",
        ]
        output_modes = {
            "point": "Point",
            "polygon": "Polygon",
            "rectangle": "Rectangle",
        }
        default_output_mode = "rectangle"
