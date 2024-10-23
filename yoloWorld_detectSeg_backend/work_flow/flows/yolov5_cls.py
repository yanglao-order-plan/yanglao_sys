import numpy as np
from . import AutoLabelingResult, YOLO, softmax


class YOLOv5_CLS(YOLO):
    class Meta:
        required_config_names = [
            "type",
            "name",
            "display_name",
            "model_path",
        ]
        widgets = [
            "button_run",
        ]
        output_modes = {
            "rectangle": "Rectangle",
        }
        default_output_mode = "rectangle"

    def postprocess(self, outs, topk=1):
        """
        Classification:
            Post-processes the output of the network.

        Args:
            outs (list): Output predictions from the network.
            topk (int): Number of top predictions to consider.

        Returns:
            str: Predicted label.
        """
        res = softmax(np.array(outs)).tolist()
        index = np.argmax(res)
        label = str(self.classes[index])

        return label

    def predict_shapes(self, image, image_path=None):
        """
        Predict shapes from image
        """

        if image is None:
            return []

        blob = self.preprocess(image, upsample_mode="centercrop")
        predictions = self.net.get_ort_inference(blob)
        label = self.postprocess(predictions)
        result = AutoLabelingResult(
            shapes=[], replace=False, description=label
        )
        return result
