from flask import Blueprint, request, jsonify
from sqlalchemy.testing.plugin.plugin_base import logging
from werkzeug.security import generate_password_hash
from flask_jwt_extended import jwt_required

from extensions import db
from models import UserModel, RoleModel, DatasetModel, TaskModel, FlowModel, ReleaseModel, WeightModel, ResultModel
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


# Create Dataset
@bp.route('/dataset', methods=['POST'])
@jwt_required()
def create_dataset():
    data = request.get_json()
    try:
        new_dataset = DatasetModel(
            name=data['name'],
            class_num=data['class_num'],
            total_num=data['total_num'],
            train_num=data['train_num'],
            val_num=data['val_num'],
            test_exist=data.get('test_exist', True),
            test_num=data.get('test_num', 0)
        )
        db.session.add(new_dataset)
        db.session.commit()
        return response(0, 'Dataset created successfully', {'dataset_id': new_dataset.id})
    except Exception as e:
        logging.error(f"Error creating dataset: {e}")
        return response(1, 'Failed to create dataset')

# Get Dataset
@bp.route('/dataset/<int:dataset_id>', methods=['GET'])
@jwt_required()
def get_dataset(dataset_id):
    dataset = DatasetModel.query.get_or_404(dataset_id)
    return response(0, 'Dataset fetched successfully', dataset.to_dict())

# Update Dataset
@bp.route('/dataset/<int:dataset_id>', methods=['PUT'])
@jwt_required()
def update_dataset(dataset_id):
    data = request.get_json()
    dataset = DatasetModel.query.get_or_404(dataset_id)
    try:
        if 'name' in data:
            dataset.name = data['name']
        if 'class_num' in data:
            dataset.class_num = data['class_num']
        if 'total_num' in data:
            dataset.total_num = data['total_num']
        if 'train_num' in data:
            dataset.train_num = data['train_num']
        if 'val_num' in data:
            dataset.val_num = data['val_num']
        if 'test_exist' in data:
            dataset.test_exist = data['test_exist']
        if 'test_num' in data:
            dataset.test_num = data['test_num']
        db.session.commit()
        return response(0, 'Dataset updated successfully', dataset.to_dict())
    except Exception as e:
        print_error(f"Error updating dataset: {e}")
        return response(1, 'Failed to update dataset')

# Delete Dataset
@bp.route('/dataset/<int:dataset_id>', methods=['DELETE'])
@jwt_required()
def delete_dataset(dataset_id):
    dataset = DatasetModel.query.get_or_404(dataset_id)
    try:
        db.session.delete(dataset)
        db.session.commit()
        return response(0, 'Dataset deleted successfully')
    except Exception as e:
        print_error(f"Error deleting dataset: {e}")
        return response(1, 'Failed to delete dataset')

# Create Task
@bp.route('/task', methods=['POST'])
@jwt_required()
def create_task():
    data = request.get_json()
    try:
        new_task = TaskModel(
            name=data['name'],
            type_id=data.get('type_id')
        )
        db.session.add(new_task)
        db.session.commit()
        return response(0, 'Task created successfully', new_task.to_dict())
    except Exception as e:
        print_error(f"Error creating task: {e}")
        return response(1, 'Failed to create task')

# Get Task
@bp.route('/task/<int:task_id>', methods=['GET'])
@jwt_required()
def get_task(task_id):
    task = TaskModel.query.get_or_404(task_id)
    return response(0, 'Task fetched successfully', task.to_dict())

# Update Task
@bp.route('/task/<int:task_id>', methods=['PUT'])
@jwt_required()
def update_task(task_id):
    data = request.get_json()
    task = TaskModel.query.get_or_404(task_id)
    try:
        if 'name' in data:
            task.name = data['name']
        if 'type_id' in data:
            task.type_id = data['type_id']
        db.session.commit()
        return response(0, 'Task updated successfully', task.to_dict())
    except Exception as e:
        print_error(f"Error updating task: {e}")
        return response(1, 'Failed to update task')

# Delete Task
@bp.route('/task/<int:task_id>', methods=['DELETE'])
@jwt_required()
def delete_task(task_id):
    task = TaskModel.query.get_or_404(task_id)
    try:
        db.session.delete(task)
        db.session.commit()
        return response(0, 'Task deleted successfully')
    except Exception as e:
        print_error(f"Error deleting task: {e}")
        return response(1, 'Failed to delete task')
