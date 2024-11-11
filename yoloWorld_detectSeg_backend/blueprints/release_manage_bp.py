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

bp = Blueprint('release', __name__, url_prefix='/release-manage')


@bp.route('/list', methods=['GET'])
@jwt_required(refresh=True)
def get_releases():
    releases_all = ReleaseModel.query.all()
    releases_ents = {release.id: release.name for release in releases_all}
    page = int(request.args.get('currentPage', 1))  # 获取页码，默认为第一页
    per_page = int(request.args.get('size', 10))  # 获取每页显示的数据量，默认为 10 条
    release = request.args.get('release', '').strip()  # 获取任务类型名称
    releaseName = request.args.get('releaseName', '').strip()  # 获取任务类型名称
    flow = request.args.get('flow', '').strip()  # 获取任务类型名称
    task = request.args.get('task', '').strip()  # 获取任务类型名称
    taskType = request.args.get('taskType', '').strip()  # 获取任务类型名称
    # 构造查询语句
    query = ReleaseModel.query  # 使用 TaskTypeModel 模型进行查询
    if release:  # 如果流程名称不为空
        query = query.filter(ReleaseModel.name.ilike(f'%{release}%'))
    if releaseName:  # 如果流程名称不为空
        query = query.filter(ReleaseModel.show_name.ilike(f'%{releaseName}%'))
    query = query.join(FlowModel)
    if flow:  # 如果流程名称不为空
        query = query.filter(FlowModel.name.ilike(f'%{flow}%'))
    query = query.join(TaskModel)
    if task:  # 如果任务名称不为空
        query = query.filter(TaskModel.name.ilike(f'%{task}%'))
    query = query.join(TaskTypeModel)
    if taskType:  # 如果任务类型不为空
        query = query.filter(TaskTypeModel.name.ilike(f'%{taskType}%'))
    if page == 1 and per_page == -1:  # 检查是否为获取全部数据的请求
        releases = releases_all  # 获取全部数据
        total = len(releases)  # 计算总数据量
    else:
        # 分页查询
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)  # 使用 paginate() 方法进行分页查询，不抛出异常
        releases = pagination.items  # 获取当前页的数据
        total = pagination.total  # 获取总数据量
    # 构造返回数据
    data = {
        'list': [release.to_dict() for release in releases],  # 将当前页的所有任务类型数据转换为字典形式，并存储在列表中
        'whole': releases_ents,
        'total': total,  # 总数据量
    }
    return response(code=0, data=data, message='获取工作流版本成功')

@bp.route('/all', methods=['GET'])
@jwt_required(refresh=True)
def get_all_releases():
    query = ReleaseModel.query  # 使用 TaskTypeModel 模型进行查询
    releases_ids = [id[0] for id in query.with_entities(ReleaseModel.id).all()]
    return response(code=0, data=releases_ids, message='获取全部工作流版本成功')

@bp.route('/add', methods=['POST'])
@jwt_required(refresh=True)
def add_release():
    name = request.json.get('name', '').strip()
    showName = request.json.get('showName', '').strip()
    flowId =int(request.json.get('flowId', 0))
    if not name or not flowId:
        return response(code=1, message='添加失败，缺少必要参数')
    release = ReleaseModel.query.filter_by(name=name).first()
    if release is not None:
        return response(code=1, message='添加失败，版本已存在')
    flow = FlowModel.query.get(flowId)
    if flow is None:
        return response(code=1, message='添加失败，工作流不存在')
    release = ReleaseModel(name=name, show_name=showName, flow_id=flowId)
    db.session.add(release)
    db.session.commit()
    return response(code=0, message='添加版本成功')


@bp.route('/delete/<int:release_id>', methods=['DELETE'])
@jwt_required(refresh=True)
def delete_flow(release_id):
    release = ReleaseModel.query.get(release_id)
    if release is None:
        return response(code=1, message='删除失败，版本不存在')
    db.session.delete(release)
    db.session.commit()
    return response(code=0, message='删除版本成功')


@bp.route('/update', methods=['PUT'])
@jwt_required(refresh=True)
def update_flow():
    id = int(request.json.get('id', ''))
    name = request.json.get('name', '').strip()
    taskId = int(request.json.get('taskId', 0))
    if not id or not name or not taskId:
        return response(code=1, message='修改失败，缺少必要参数')
    flow = FlowModel.query.get(id)
    flow.name = name
    flow.task_id = taskId
    db.session.commit()
    return response(code=0, message='修改工作流成功')


@bp.route('/model_list', methods=['POST'])
@jwt_required(refresh=True)
def get_models():
    # 构造查询语句
    release_id =int(request.json.get('releaseId', 0))
    query = ModelModel.query.filter(ModelModel.release_id == release_id)
    models = query.all()  # 获取全部数据
    total = query.count()  # 获取总数据量
    # 构造返回数据
    data = {
        'list': [model.to_dict() for model in models],  # 将当前页的所有任务类型数据转换为字典形式，并存储在列表中
        'total': total,  # 总数据量
    }
    return response(code=0, data=data, message='获取版本模型配置成功')


@bp.route('/model_add', methods=['POST'])
@jwt_required(refresh=True)
def add_model():
    name = request.json.get('name', '').strip()
    weightId = int(request.json.get('weightId', 0))
    releaseId =int(request.json.get('releaseId', 0))
    if not name or weightId == 0 or releaseId == 0:
        return response(code=1, message='添加失败，缺少必要参数')
    release = ReleaseModel.query.get(releaseId)
    if release is None:
        return response(code=1, message='添加失败，版本不存在')
    weight = WeightModel.query.get(weightId)
    if weight is None:
        return response(code=1, message='添加失败，权重不存在')
    model = ModelModel(name=name, weight_id=weightId, release_id=releaseId)
    db.session.add(model)
    db.session.commit()
    return response(code=0, message='添加模型成功')


@bp.route('/model_delete/<int:model_id>', methods=['DELETE'])
@jwt_required(refresh=True)
def delete_model(model_id):
    model = ModelModel.query.get(model_id)
    if model is None:
        return response(code=1, message='删除失败，模型不存在')
    db.session.delete(model)
    db.session.commit()
    return response(code=0, message='删除模型成功')


@bp.route('/model_update', methods=['PUT'])
@jwt_required(refresh=True)
def update_model():
    id = int(request.json.get('id', ''))
    name = request.json.get('name', '').strip()
    weightId = int(request.json.get('weightId', 0))
    releaseId = int(request.json.get('releaseId', 0))
    if not id or not name or not weightId or not releaseId:
        return response(code=1, message='修改失败，缺少必要参数')
    model = ModelModel.query.get(id)
    model.name = name
    model.weight_id = weightId
    model.release_id = releaseId
    db.session.commit()
    return response(code=0, message='修改模型成功')


@bp.route('/argument_list', methods=['POST'])
@jwt_required(refresh=True)
def get_arguments():
    # 构造查询语句
    release_id =int(request.json.get('releaseId', 0))
    query = ArgumentModel.query.filter(ArgumentModel.release_id == release_id)
    arguments = query.all()  # 获取全部数据
    total = query.count()  # 获取总数据量
    # 构造返回数据
    data = {
        'list': [argument.to_dict() for argument in arguments],  # 将当前页的所有任务类型数据转换为字典形式，并存储在列表中
        'total': total,  # 总数据量
    }
    return response(code=0, data=data, message='获取版本参数配置成功')


@bp.route('/argument_add', methods=['POST'])
@jwt_required(refresh=True)
def add_argument():
    name = request.json.get('name', '').strip()
    type = request.json.get('type', '').strip()
    default = request.json.get('default', {})
    config = request.json.get('config', {})
    dynamic = int(request.json.get('dynamic', -1))
    releaseId = int(request.json.get('releaseId', 0))
    if not name or not type or dynamic == -1 or releaseId == 0:
        return response(code=1, message='添加失败，缺少必要参数')
    release = ReleaseModel.query.get(releaseId)
    if release is None:
        return response(code=1, message='添加失败，版本不存在')
    if not default:
        default = None
    if not config:
        config = None
    argument = ArgumentModel(name=name, type=type, default=default,
                             config=config, dynamic=dynamic, release_id=releaseId)
    db.session.add(argument)
    db.session.commit()
    return response(code=0, message='添加参数成功')


@bp.route('/argument_delete/<int:argument_id>', methods=['DELETE'])
@jwt_required(refresh=True)
def delete_argument(argument_id):
    argument = ArgumentModel.query.get(argument_id)
    if argument is None:
        return response(code=1, message='删除失败，参数不存在')
    db.session.delete(argument)
    db.session.commit()
    return response(code=0, message='删除参数成功')

@bp.route('/argument_update', methods=['PUT'])
@jwt_required(refresh=True)
def update_argument():
    id = int(request.json.get('id', ''))
    name = request.json.get('name', '').strip()
    type = request.json.get('type', '').strip()
    default = request.json.get('default', None)
    config = request.json.get('config', None)
    dynamic = int(request.json.get('dynamic', -1))
    if not name or not type or dynamic == -1:
        return response(code=1, message='修改失败，缺少必要参数')

    argument = ArgumentModel.query.get(id)
    if argument is None:
        return response(code=1, message='修改失败，参数不存在')

    argument.name = name
    argument.type = type
    argument.default = default
    argument.config = config
    argument.dynamic = dynamic
    argument.dynamic = dynamic
    # db.session.update(argument)
    db.session.commit()
    return response(code=0, message='修改参数成功')
