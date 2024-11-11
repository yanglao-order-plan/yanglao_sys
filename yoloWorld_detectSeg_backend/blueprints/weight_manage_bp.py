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

bp = Blueprint('weight', __name__, url_prefix='/weight-manage')


@bp.route('/list', methods=['GET'])
@jwt_required(refresh=True)
def get_weights():
    # 构造查询语句
    weightName = request.args.get('weight', '').strip()  # 获取权重名称
    weightEnable = request.args.get('enable', '').strip()  # 获取权重是否启用
    page = int(request.args.get('currentPage', 1))  # 获取页码，默认为第一页
    per_page = int(request.args.get('size', 10))  # 获取每页显示的数据量，默认为 10 条
    query = WeightModel.query  # 使用 TaskTypeModel 模型进行查询
    if weightName:  # 如果任务类型不为空
        query = query.filter(WeightModel.name.ilike(f'%{weightName}%'))  # 使用 ilike() 方法查询所有包含 taskType 的记录
    if weightEnable:
        query = query.filter(WeightModel.enable == weightEnable)  # 使用 ilike() 方法查询所有包含 taskType 的记录
    if page == 1 and per_page == -1:  # 检查是否为获取全部数据的请求
        weights = query.all()  # 获取全部数据
        total = len(weights)  # 计算总数据量
    else:
        # 分页查询
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)  # 使用 paginate() 方法进行分页查询，不抛出异常
        weights = pagination.items  # 获取当前页的数据
        total = pagination.total  # 获取总数据量
    # 构造返回数据
    data = {
        'list': [weight.to_dict_detail() for weight in weights],  # 转换为字典形式
        'total': total,  # 总数据量
    }
    return response(code=0, data=data, message='获取权重列表成功')


@bp.route('/add', methods=['POST'])
@jwt_required(refresh=True)
def add_weight():
    name = request.json.get('name', '').strip()
    local_path = request.json.get('localPath', '').strip()
    online_url = request.json.get('onlineUrl', '').strip()
    enable = request.json.get('enable', False)

    if not name:
        return response(code=1, message='添加失败，缺少权重名称')

    weight = WeightModel(name=name, local_path=local_path, online_url=online_url, enable=enable)
    db.session.add(weight)
    db.session.commit()
    return response(code=0, message='添加权重成功')


@bp.route('/delete/<int:weight_id>', methods=['DELETE'])
@jwt_required(refresh=True)
def delete_weight(weight_id):
    weight = WeightModel.query.get(weight_id)
    if weight is None:
        return response(code=1, message='删除失败，权重不存在')
    db.session.delete(weight)
    db.session.commit()
    return response(code=0, message='删除权重成功')


@bp.route('/update', methods=['PUT'])
@jwt_required(refresh=True)
def update_weight():
    id = int(request.json.get('id', ''))
    name = request.json.get('name', '').strip()
    local_path = request.json.get('localPath', '').strip()
    online_url = request.json.get('onlineUrl', '').strip()
    enable = request.json.get('enable', False)

    if not id or not name:
        return response(code=1, message='修改失败，缺少必要参数')

    weight = WeightModel.query.get(id)
    if weight is None:
        return response(code=1, message='修改失败，权重不存在')

    weight.name = name
    weight.local_path = local_path
    weight.online_url = online_url
    weight.enable = enable
    db.session.commit()
    return response(code=0, message='修改权重成功')

