import os

from . import __preferred_device__, Shape, Model, AutoLabelingResult, get_sliced_prediction, Yolov8OnnxDetectionModel


class YOLOv8_SAHI(Model):
    """Object detection model using YOLOv8 with SAHI"""

    class Meta:
        required_config_names = [
            "type",
            "name",
            "display_name",
            "model_path",
            "slice_height",
            "slice_width",
            "overlap_height_ratio",
            "overlap_width_ratio",
            "nms_threshold",
            "confidence_threshold",
            "classes",
        ]
        widgets = ["button_run"]
        output_modes = {
            "rectangle": "Rectangle",
        }
        default_output_mode = "rectangle"

    def __init__(self, model_config, on_message) -> None:
        # Run the parent class's init method
        super().__init__(model_config, on_message)

        model_abs_path = self.get_model_abs_path(self.config, "model_path")
        if not model_abs_path or not os.path.isfile(model_abs_path):
            raise FileNotFoundError(
                "Could not download or initialize YOLOv8 model."
            )
        category_mapping = {
            str(ind): category_name
            for ind, category_name in enumerate(self.config["classes"])
        }
        self.net = Yolov8OnnxDetectionModel(
            model_path=model_abs_path,
            nms_threshold=self.config["nms_threshold"],
            confidence_threshold=self.config["confidence_threshold"],
            category_mapping=category_mapping,
            device=__preferred_device__,
        )
        self.slice_height = self.config["slice_height"]
        self.slice_width = self.config["slice_width"]
        self.overlap_height_ratio = self.config["overlap_height_ratio"]
        self.overlap_width_ratio = self.config["overlap_width_ratio"]

    def predict_shapes(self, image, image_path=None):
        """
        Predict shapes from image
        """

        if image is None:
            return []

        results = get_sliced_prediction(
            image,
            self.net,
            slice_height=self.slice_height,
            slice_width=self.slice_width,
            overlap_height_ratio=self.overlap_height_ratio,
            overlap_width_ratio=self.overlap_width_ratio,
            verbose=0,
        )
        shapes = []

        for out in results.object_prediction_list:
            xmin = out.bbox.minx
            ymin = out.bbox.miny
            xmax = out.bbox.maxx
            ymax = out.bbox.maxy
            shape = Shape(
                label=str(out.category.name), shape_type="rectangle", flags={}
            )
            shape.add_point(xmin, ymin)
            shape.add_point(xmax, ymin)
            shape.add_point(xmax, ymax)
            shape.add_point(xmin, ymax)
            shapes.append(shape)

        result = AutoLabelingResult(shapes, replace=True)
        return result

    def unload(self):
        del self.net
