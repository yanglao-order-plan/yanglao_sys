from flask import Blueprint, request
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

bp = Blueprint('task', __name__, url_prefix='/task-manage')


@bp.route('/list', methods=['GET'])
@jwt_required(refresh=True)
def get_tasks():
    page = int(request.args.get('currentPage', 1))  # 获取页码，默认为第一页
    per_page = int(request.args.get('size', 10))  # 获取每页显示的数据量，默认为 10 条
    taskType = request.args.get('taskType', '').strip()  # 获取任务类型名称
    task = request.args.get('task', '').strip()  # 获取任务类型名称
    # 构造查询语句
    query = TaskModel.query  # 使用 TaskTypeModel 模型进行查询
    if task:  # 如果任务不为空
        query = query.filter(TaskModel.name.ilike(f'%{task}%'))
    if taskType:  # 如果任务类型不为空
        query = query.join(TaskTypeModel).filter(TaskTypeModel.name.ilike(f'%{taskType}%'))
    if page == 1 and per_page == -1:  # 检查是否为获取全部数据的请求
        tasks = query.all()  # 获取全部数据
        total = len(tasks)  # 计算总数据量
    else:
        # 分页查询
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)  # 使用 paginate() 方法进行分页查询，不抛出异常
        tasks = pagination.items  # 获取当前页的数据
        total = pagination.total  # 获取总数据量
    # 构造返回数据
    data = {
        'list': [task.to_dict() for task in tasks],  # 将当前页的所有任务类型数据转换为字典形式，并存储在列表中
        'total': total,  # 总数据量
    }
    return response(code=0, data=data, message='获取任务列表成功')


@bp.route('/add', methods=['POST'])
@jwt_required(refresh=True)
def add_task():
    name = request.json.get('name', '').strip()
    typeId =int(request.json.get('typeId', ''))
    if not name or not typeId:
        return response(code=1, message='添加失败，缺少必要参数')
    task = TaskModel.query.filter_by(name=name).first()
    if task is not None:
        return response(code=1, message='添加失败，任务已存在')
    task_type = TaskTypeModel.query.get(typeId)
    if task_type is None:
        return response(code=1, message='添加失败，任务类型不存在')
    task = TaskModel(name=name, type_id=typeId)
    db.session.add(task)
    db.session.commit()
    return response(code=0, message='添加任务成功')


@bp.route('/delete/<int:task_id>', methods=['DELETE'])
@jwt_required(refresh=True)
def delete_task(task_id):
    task = TaskModel.query.get(task_id)
    if task is None:
        return response(code=1, message='删除失败，任务不存在')
    db.session.delete(task)
    db.session.commit()
    return response(code=0, message='删除任务成功')


@bp.route('/update', methods=['PUT'])
@jwt_required(refresh=True)
def update_task():
    id = int(request.json.get('id', ''))
    name = request.json.get('name', '').strip()
    typeId = int(request.json.get('typeId', ''))
    if not id or not name or not typeId:
        return response(code=1, message='修改失败，缺少必要参数')
    task = TaskModel.query.get(id)
    task.name = name
    task.type_id = typeId
    db.session.commit()
    return response(code=0, message='修改任务类型成功')
