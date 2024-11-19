import os

from . import __preferred_device__, AutoLabelingResult, RecognizeAnything, OnnxBaseModel, Grounding_DINO


class RAM_Grounding_DINO:
    def __init__(self, model_config, on_message) -> None:
        # Run the parent class's init method
        self.grounding_dino = Grounding_DINO(model_config, on_message)
        model_config['model_path'] = model_config['tag_model_path']
        self.ram = RecognizeAnything(model_config, on_message)

    def set_output_mode(self, mode):
        self.grounding_dino.set_output_mode(mode)

    def predict_shapes(self, image, prompt_mode='split'):
        """
        Predict shapes from image
        """
        if image is None:
            return []

        blob = self.ram.preprocess(image, self.ram.input_shape)
        outs = self.ram.net.get_ort_inference(blob, extract=False)
        tags = self.ram.postprocess(outs)
        if prompt_mode == 'split':
            labels = self.ram.get_labels(tags)
            shapes = []
            for label in labels:
                results = self.grounding_dino.predict_shapes(image=image, text_prompt=label)
                shapes.extend(results.shapes)
        elif prompt_mode == 'whole':
            prompt = self.ram.get_results(tags)
            shapes = self.grounding_dino.predict_shapes(image=image, text_prompt=prompt)
        else:
            raise ValueError(f"Unknown mode: {prompt_mode}")

        return AutoLabelingResult(shapes=shapes, replace=True)