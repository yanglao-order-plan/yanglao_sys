from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash

from database_models import *
from flask_jwt_extended import jwt_required

from extensions import db
from utils.backend_utils.response_utils import response
from utils.backend_utils.colorprinter import *

'''
前后端code约定：
code: 0 成功 前端无消息弹窗
code: 1 失败 前端无消息弹窗
code: 200 前端消息弹窗Success
code: 201 前端消息弹窗Error
code: 202 前端消息弹窗Warning
code: 203 前端消息弹窗Info
code: 204 前端通知弹窗Success
code: 205 前端通知弹窗Error
code: 206 前端通知弹窗Warning
code: 207 前端通知弹窗Info
'''

bp = Blueprint('config-manage', __name__, url_prefix='/config-manage')


@bp.route('/tasks', methods=['GET'])
@jwt_required(refresh=True)
# 获取所有任务以及其关联的类型和流程
def get_tasks():
    tasks = TaskModel.query.all()
    result = []
    for task in tasks:
        result.append({
            'id': task.id,
            'name': task.name,
            'type_id': task.type_id,
            'type_name': task.task_type.name if task.task_type else None,
            'flows': [{'id': flow.id, 'name': flow.name} for flow in task.flows]
        })
    return jsonify(result)


# 创建新的任务及关联的流程
@bp.route('/tasks', methods=['POST'])
@jwt_required(refresh=True)
def create_task():
    data = request.get_json()
    new_task = TaskModel(name=data['name'], type_id=data.get('type_id'))

    # 添加流程
    flows_data = data.get('flows', [])
    for flow_data in flows_data:
        new_flow = FlowModel(name=flow_data['name'])
        new_task.flows.append(new_flow)

    db.session.add(new_task)
    db.session.commit()
    return jsonify(new_task.to_dict()), 201


# 更新任务及关联的流程
@bp.route('/tasks/<int:task_id>', methods=['PUT'])
@jwt_required(refresh=True)
def update_task(task_id):
    task = TaskModel.query.get_or_404(task_id)
    data = request.get_json()

    # 更新任务基本信息
    task.name = data.get('name', task.name)
    task.type_id = data.get('type_id', task.type_id)

    # 更新关联的流程
    flows_data = data.get('flows', [])
    task.flows.clear()  # 先清空原有的流程
    for flow_data in flows_data:
        new_flow = FlowModel(name=flow_data['name'])
        task.flows.append(new_flow)

    db.session.commit()
    return jsonify(task.to_dict())


# 删除任务及其关联的流程
@bp.route('/tasks/<int:task_id>', methods=['DELETE'])
@jwt_required(refresh=True)
def delete_task(task_id):
    task = TaskModel.query.get_or_404(task_id)
    db.session.delete(task)
    db.session.commit()
    return '', 204


# 获取任务类型
@bp.route('/task_types', methods=['GET'])
@jwt_required(refresh=True)
def get_task_types():
    task_types = TaskTypeModel.query.all()
    return jsonify([{'id': task_type.id, 'name': task_type.name} for task_type in task_types])


# 获取所有流程
@bp.route('/flows', methods=['GET'])
@jwt_required(refresh=True)
def get_flows():
    flows = FlowModel.query.all()
    return jsonify([{'id': flow.id, 'name': flow.name} for flow in flows])


# 创建流程
@bp.route('/flows', methods=['POST'])
@jwt_required(refresh=True)
def create_flow():
    data = request.get_json()
    new_flow = FlowModel(name=data['name'], task_id=data['task_id'])
    db.session.add(new_flow)
    db.session.commit()
    return jsonify({'id': new_flow.id, 'name': new_flow.name}), 201


# 更新流程
@bp.route('/flows/<int:flow_id>', methods=['PUT'])
@jwt_required(refresh=True)
def update_flow(flow_id):
    flow = FlowModel.query.get_or_404(flow_id)
    data = request.get_json()
    flow.name = data.get('name', flow.name)
    db.session.commit()
    return jsonify({'id': flow.id, 'name': flow.name})


# 删除流程
@bp.route('/flows/<int:flow_id>', methods=['DELETE'])
@jwt_required(refresh=True)
def delete_flow(flow_id):
    flow = FlowModel.query.get_or_404(flow_id)
    db.session.delete(flow)
    db.session.commit()
    return '', 204