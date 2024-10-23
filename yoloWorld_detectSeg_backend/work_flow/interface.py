from flask import Flask, request, jsonify
from engines.model_manager import ModelManager

app = Flask(__name__)
model_manager = ModelManager()

'''
模型装载接口
'''

@app.route('/models', methods=['GET'])
def get_model_list():
    """获取可用模型列表"""
    model_list = model_manager.get_model_configs()
    return jsonify(model_list)

@app.route('/models/load', methods=['POST'])
def load_model():
    """加载指定模型"""
    config_path = request.json.get('config_path')
    model_manager.load_model(config_path)
    return jsonify({"status": "Model loading started"})

@app.route('/models/load_custom', methods=['POST'])
def load_custom_model():
    """加载自定义模型"""
    config_file = request.json.get('config_file')
    model_manager.load_custom_model(config_file)
    return jsonify({"status": "Custom model loading started"})

@app.route('/models/unload', methods=['POST'])
def unload_model():
    """卸载当前模型"""
    model_manager.unload_model()
    return jsonify({"status": "Model unloaded"})

'''
模型推理接口
'''

@app.route('/auto_labeling/predict', methods=['POST'])
def run_auto_labeling():
    """执行自动标注任务"""
    image = request.json.get('image')  # Assume image is base64 encoded or file path
    filename = request.json.get('filename')
    model_manager.predict_shapes_threading(image, filename)
    return jsonify({"status": "Prediction started"})

@app.route('/auto_labeling/predict_vl', methods=['POST'])
def run_vl_prediction():
    """执行视觉语言自动标注"""
    image = request.json.get('image')
    filename = request.json.get('filename')
    text_prompt = request.json.get('text_prompt')
    model_manager.predict_shapes_threading(image, filename, text_prompt=text_prompt)
    return jsonify({"status": "VL Prediction started"})

@app.route('/auto_labeling/manual/add_point', methods=['POST'])
def add_point():
    """手动添加标注点"""
    marks = request.json.get('marks')
    model_manager.set_auto_labeling_marks(marks)
    return jsonify({"status": "Marks set"})

@app.route('/auto_labeling/manual/set_prompt', methods=['POST'])
def set_auto_labeling_prompt():
    """设置自动标注提示"""
    model_manager.set_auto_labeling_prompt()
    return jsonify({"status": "Prompt set"})

'''
模型模式接口
'''

@app.route('/auto_labeling/params/conf', methods=['POST'])
def set_conf_value():
    """设置置信度阈值"""
    value = request.json.get('value')
    model_manager.set_auto_labeling_conf(value)
    return jsonify({"status": "Confidence value set"})

@app.route('/auto_labeling/params/iou', methods=['POST'])
def set_iou_value():
    """设置IoU阈值"""
    value = request.json.get('value')
    model_manager.set_auto_labeling_iou(value)
    return jsonify({"status": "IoU value set"})

@app.route('/auto_labeling/params/preserve_annotations', methods=['POST'])
def set_preserve_annotations():
    """设置是否保留现有标注"""
    state = request.json.get('state')
    model_manager.set_auto_labeling_preserve_existing_annotations_state(state)
    return jsonify({"status": "Preserve annotations state set"})


@app.route('/output_modes/set', methods=['POST'])
def set_output_mode():
    """设置模型输出模式"""
    output_mode = request.json.get('output_mode')
    model_manager.set_output_mode(output_mode)
    return jsonify({"status": "Output mode set"})

@app.route('/segmentation/enable', methods=['POST'])
def enable_auto_segmentation():
    """启用自动分割"""
    model_manager.auto_segmentation_model_selected.emit()
    return jsonify({"status": "Auto segmentation enabled"})

@app.route('/segmentation/disable', methods=['POST'])
def disable_auto_segmentation():
    """禁用自动分割"""
    model_manager.auto_segmentation_model_unselected.emit()
    return jsonify({"status": "Auto segmentation disabled"})