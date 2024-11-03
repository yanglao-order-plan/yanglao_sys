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

bp = Blueprint('flow', __name__, url_prefix='/flow-manage')


@bp.route('/list', methods=['GET'])
@jwt_required(refresh=True)
def get_flows():
    page = int(request.args.get('currentPage', 1))  # 获取页码，默认为第一页
    per_page = int(request.args.get('size', 10))  # 获取每页显示的数据量，默认为 10 条
    flow = request.args.get('flow', '').strip()  # 获取任务类型名称
    task = request.args.get('task', '').strip()  # 获取任务类型名称
    taskType = request.args.get('taskType', '').strip()  # 获取任务类型名称
    # 构造查询语句
    query = FlowModel.query  # 使用 TaskTypeModel 模型进行查询
    if flow:  # 如果流程名称不为空
        query = query.filter(FlowModel.name.ilike(f'%{flow}%'))
    query = query.join(TaskModel)
    if task:  # 如果任务名称不为空
        query = query.filter(TaskModel.name.ilike(f'%{task}%'))
    query = query.join(TaskTypeModel)
    if taskType:  # 如果任务类型不为空
        query = query.filter(TaskTypeModel.name.ilike(f'%{taskType}%'))
    if page == 1 and per_page == -1:  # 检查是否为获取全部数据的请求
        flows = query.all()  # 获取全部数据
        total = len(flows)  # 计算总数据量
    else:
        # 分页查询
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)  # 使用 paginate() 方法进行分页查询，不抛出异常
        flows = pagination.items  # 获取当前页的数据
        total = pagination.total  # 获取总数据量
    # 构造返回数据
    data = {
        'list': [flow.to_dict() for flow in flows],  # 将当前页的所有任务类型数据转换为字典形式，并存储在列表中
        'total': total,  # 总数据量
    }
    return response(code=0, data=data, message='获取任务类型列表成功')


@bp.route('/add', methods=['POST'])
@jwt_required(refresh=True)
def add_flow():
    name = request.json.get('name', '').strip()
    taskId =int(request.json.get('taskId', 0))
    if not name or not taskId:
        return response(code=1, message='添加失败，缺少必要参数')
    flow = FlowModel.query.filter_by(name=name).first()
    if flow is not None:
        return response(code=1, message='添加失败，工作流已存在')
    task = TaskModel.query.get(taskId)
    if task is None:
        return response(code=1, message='添加失败，任务不存在')
    flow = FlowModel(name=name, task_id=taskId)
    db.session.add(flow)
    db.session.commit()
    return response(code=0, message='添加工作流成功')


@bp.route('/delete/<int:flow_id>', methods=['DELETE'])
@jwt_required(refresh=True)
def delete_flow(flow_id):
    flow = FlowModel.query.get(flow_id)
    if flow is None:
        return response(code=1, message='删除失败，工作流不存在')
    db.session.delete(flow)
    db.session.commit()
    return response(code=0, message='删除工作流成功')


@bp.route('/update', methods=['PUT'])
@jwt_required(refresh=True)
def update_flow():
    id = int(request.json.get('id', ''))
    name = request.json.get('name', '').strip()
    taskId = int(request.json.get('taskId', 0))
    print(taskId)
    if not id or not name or not taskId:
        return response(code=1, message='修改失败，缺少必要参数')
    flow = FlowModel.query.get(id)
    flow.name = name
    flow.task_id = taskId
    db.session.commit()
    return response(code=0, message='修改工作流成功')

