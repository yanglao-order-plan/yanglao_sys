from platform import release

from sqlalchemy import inspect

from extensions import db
from datetime import datetime


class UserModel(db.Model):
    __tablename__ = 'user'
    __bind_key__ = 'local'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='用户id')
    username = db.Column(db.String(100), nullable=False, comment='用户名')
    password = db.Column(db.String(500), nullable=False, comment='密码')
    email = db.Column(db.String(100), nullable=False, unique=True, comment='邮箱')
    join_time = db.Column(db.DateTime, default=datetime.now, comment='加入时间')
    status = db.Column(db.Boolean, default=True, comment='是否启用')
    # ForeignKey 默认注册为普通用户
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'), default=2, comment='用户角色')
    # Relationship
    roles = db.relationship('RoleModel', backref=db.backref('users', lazy='dynamic'))

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'createTime': self.join_time.strftime('%Y-%m-%d %H:%M:%S'),
            'status': self.status,
            'roles': self.roles.name,
        }


class RoleModel(db.Model):
    __tablename__ = 'role'
    __bind_key__ = 'local'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='角色id')
    name = db.Column(db.String(100), nullable=False, comment='角色名称')
    desc = db.Column(db.String(100), nullable=False, comment='角色描述')


class CaptchaModel(db.Model):
    __tablename__ = 'captcha'
    __bind_key__ = 'local'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String(100), nullable=True, comment='验证邮箱')
    captcha = db.Column(db.String(100), nullable=False, comment='验证码')
    create_time = db.Column(db.DateTime, default=datetime.now, comment='创建时间')
    is_used = db.Column(db.Boolean, default=False, comment='是否使用')


class DatasetModel(db.Model):
    __tablename__ = 'dataset'
    __bind_key__ = 'local'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='数据集id')
    name = db.Column(db.String(100), nullable=False, comment='数据集名称')
    class_num = db.Column(db.Integer, nullable=False, comment='类别数量')
    total_num = db.Column(db.Integer, nullable=False, comment='总数量')
    train_num = db.Column(db.Integer, nullable=False, comment='训练集数量')
    val_num = db.Column(db.Integer, nullable=False, comment='验证集数量')
    test_exist = db.Column(db.Boolean, default=True, nullable=False, comment='是否存在测试集')
    test_num = db.Column(db.Integer, nullable=True, comment='测试集数量')


# TaskType Model
class TaskTypeModel(db.Model):
    __tablename__ = 'task_type'
    __bind_key__ = 'local'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='任务类型ID')
    name = db.Column(db.String(100), nullable=False, comment='任务类型名称')
    tasks = db.relationship('TaskModel', backref='task_type', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'taskType': self.name,
        }


# Task Model
class TaskModel(db.Model):
    __tablename__ = 'task'
    __bind_key__ = 'local'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='任务ID')
    name = db.Column(db.String(50), nullable=False, comment='任务名称')
    type_id = db.Column(db.Integer, db.ForeignKey('task_type.id'), nullable=True, comment='任务类型ID')
    flows = db.relationship('FlowModel', backref='task', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'task': self.name,
            'taskType': self.task_type.name,
            'typeId': self.type_id,
        }


# Flow Model
class FlowModel(db.Model):
    __tablename__ = 'flow'
    __bind_key__ = 'local'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='流程ID')
    name = db.Column(db.String(100), nullable=False, comment='流程名称')
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'), nullable=False, comment='任务ID')
    releases = db.relationship('ReleaseModel', backref='flow', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'flow': self.name,
            'task': self.task.name,
            'taskId': self.task_id,
            'taskType': self.task.task_type.name,
            'typeId': self.task.task_type.id,
        }

# Release Model
class ReleaseModel(db.Model):
    __tablename__ = 'release'
    __bind_key__ = 'local'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='版本ID')
    name = db.Column(db.String(100), nullable=False, comment='版本名称')
    show_name = db.Column(db.String(100), nullable=False, comment='显示名称')
    flow_id = db.Column(db.Integer, db.ForeignKey('flow.id'), nullable=False, comment='流程ID')   # 级联删除
    release_weights = db.relationship('ModelModel', backref='release', lazy=True, cascade='all, delete')
    release_args = db.relationship('ArgumentModel', backref='release', lazy=True, cascade='all, delete')

    def __init__(self, name, show_name, flow_id):
        self.name = name
        self.show_name = show_name
        self.flow_id = flow_id
        self._weights = None
        self._flow = None
        self._to_weights = None
        self._to_params = None
        self._to_hypers = None
        self._hypers = None
        self._params = None

    def to_dict(self):
        return {
            'id': self.id,
            'release': self.name,
            'releaseName': self.show_name,
            'flow': self.flow.name,
            'flowId': self.flow_id,
            'task': self.flow.task.name,
            'taskId': self.flow.task_id,
            'taskType': self.flow.task.task_type.name,
            'typeId': self.flow.task.type_id,
        }

    def check_weight(self, weight):
        for release_weight in self.release_weights:
            if release_weight.weight_id == weight.id:
                return True
        return False

    @property
    def to_config(self):
        if not hasattr(self, '_flow'):
            self._flow = FlowModel.query.get(self.flow_id)
        config = {
            'type': self._flow.name,
            'name': self.name,
            'display_name': self.show_name,
        }
        config.update(self.params)
        return config

    @property
    def to_weights(self):
        if not hasattr(self, '_to_weights'):
            self._to_weights = []
            for release_weight in self.release_weights:
                self._to_weights.append(release_weight.weight)
        return self._to_weights

    @property
    def weights(self):
        if not hasattr(self, '_weights'):
            self._weights = {}
            for release_weight in self.release_weights:
                if release_weight.name not in self._weights:
                    self._weights[release_weight.name] = []
                self.weights[release_weight.name].append(release_weight.weight_id)
        return self._weights

    @property
    def to_params(self):
        if not hasattr(self, '_to_params'):
            self._to_params = []
            for release_arg in self.release_args:
                if not release_arg.dynamic:
                    self._to_params.append(release_arg.arg)
        return self._to_params

    @property
    def params(self):
        if not hasattr(self, '_params'):
            self._params = {}
            for release_arg in self.release_args:
                if not release_arg.dynamic:
                    self._params[release_arg.name] = release_arg.arg['argDefault'] \
                        if 'argDefault' in release_arg.arg else None
        return self._params

    @property
    def to_hypers(self):
        if not hasattr(self, '_to_hypers'):
            self._to_hypers = []
            for release_arg in self.release_args:
                if release_arg.dynamic:
                    self._to_hypers.append(release_arg.arg)
        return self._to_hypers

    @property
    def hypers(self):
        if not hasattr(self, '_hypers'):
            self._hypers = {}
            for release_param in self.release_args:
                if release_param.dynamic:
                    self._hypers[release_param.name] = release_param.arg['argDefault'] \
                        if 'argDefault' in release_param.arg else None
        return self._hypers


class WeightModel(db.Model):
    __tablename__ = 'weight'
    __bind_key__ = 'local'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='权重id')
    name = db.Column(db.String(100), nullable=False, comment='权重名称')
    local_path = db.Column(db.Text, nullable=True, comment='本地保存路径')
    online_url = db.Column(db.Text, nullable=True, comment='在线访问地址')
    enable = db.Column(db.Boolean, default=False, nullable=False, comment='是否启用')
    dataset_id = db.Column(db.Integer, db.ForeignKey('dataset.id'), nullable=True)
    dataset = db.relationship('DatasetModel', backref=db.backref('weight'))

    @property
    def to_dict(self):
        return {
            'weightName': self.name,
            'weightEnable': self.enable,
        }

    def to_dict_detail(self):
        return {
            'id': self.id,
            'weight': self.name,
            'localPath': self.local_path,
            'onlineUrl': self.online_url,
            'enable': self.enable,
        }

    @property
    def to_config(self):
        return {
            'local': self.local_path,
            'online': self.online_url,
        }


# ReleaseWeight Model (Junction table for release and weight)
class ModelModel(db.Model):
    __tablename__ = 'model'
    __bind_key__ = 'local'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='版本关联权重ID')
    release_id = db.Column(db.Integer, db.ForeignKey('release.id'), nullable=False,
                           comment='版本ID')
    weight_id = db.Column(db.Integer, db.ForeignKey('weight.id'), nullable=False,
                          comment='权重ID')
    name = db.Column(db.String(100), nullable=False, comment='关键字')

    # Relationships
    def __init__(self, release_id, weight_id, name):
        self.release_id = release_id
        self.weight_id = weight_id
        self.name = name
        self._weight = None

    @property
    def weight(self):
        if not hasattr(self, '_weight'):
            self._weight = WeightModel.query.get(self.weight_id).to_dict
            self._weight['weightKey'] = self.name
        return self._weight

    @weight.setter
    def weight(self, value):
        self._weight = value

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'weight': self.weight['weightName'],
            'weightId': self.weight_id
        }


class ArgumentModel(db.Model):
    __tablename__ = 'argument'
    __bind_key__ = 'local'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='版本关联参数ID')
    name = db.Column(db.String(100), nullable=False, comment='参数名称')
    type = db.Column(db.String(100), nullable=True, comment='参数类型')
    default = db.Column(db.JSON, nullable=True, comment='默认值')
    config = db.Column(db.JSON, nullable=True, comment='参数配置')
    dynamic = db.Column(db.Boolean, default=False, nullable=False, comment='是否为动态参数')
    release_id = db.Column(db.Integer, db.ForeignKey('release.id'), nullable=False, comment='版本ID')

    def __init__(self, name, type, default, config, dynamic, release_id):
        self.name = name
        self.type = type
        self.default = default
        self.config = config
        self.dynamic = dynamic
        self.release_id = release_id
        self._arg = None

    @property
    def arg(self):
        if not hasattr(self, '_arg'):
            prefix = 'arg'
            self._arg = {
                f'{prefix}Name': self.name,
                f'{prefix}Type': self.type,
                f'{prefix}Default': self.default,
                f'{prefix}Config': self.config
            }
        return self._arg

    @arg.setter
    def arg(self, value):
        self._arg = value

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'type': self.type,
            'default': self.default,
            'config': self.config,
            'dynamic': self.dynamic,
        }

class ServiceModel(db.Model):
    __tablename__ = 'service'
    __bind_key__ = 'remote'
    id = db.Column(db.Integer, primary_key=True, name='service_id')
    name = db.Column(db.String(100), nullable=False, name='service_name')
    unit = db.Column(db.String(100), nullable=False)
    unit_price = db.Column(db.Float, nullable=False)
    status = db.Column(db.Integer, nullable=False, name='service_status')
    # 服务相关工单的元数据要求
    start_img_min = db.Column(db.Integer, nullable=False)
    start_img_max = db.Column(db.Integer, nullable=False)
    start_img_num = (start_img_min, start_img_max)
    service_img_min = db.Column(db.Integer, nullable=False)
    service_img_max = db.Column(db.Integer, nullable=False)
    service_img_num = (service_img_min, service_img_max)
    end_img_min = db.Column(db.Integer, nullable=False)
    end_img_max = db.Column(db.Integer, nullable=False)
    end_img_num = (end_img_min, end_img_max)
    least_service_duration = db.Column(db.Integer, nullable=False)
    service_frequency_day = db.Column(db.Integer, nullable=False)

    def to_dict(self, keys=None):
        kwargs = {c.key: getattr(self, c.key) for c in inspect(self).mapper.column_attrs}
        kwargs['start_img_num'] = (self.start_img_min, self.start_img_max)
        kwargs['middle_img_num'] = (self.service_img_min, self.service_img_max)
        kwargs['end_img_num'] = (self.end_img_min, self.end_img_max)
        del kwargs['start_img_min']
        del kwargs['start_img_max']
        del kwargs['service_img_min']
        del kwargs['service_img_max']
        del kwargs['end_img_min']
        del kwargs['end_img_max']
        if keys is dict:
            for key in kwargs.keys():
                if key not in keys:
                    kwargs.pop(key)
        return kwargs

class WorkOrderModel(db.Model):
    __tablename__ = 'work_order'
    __bind_key__ = 'remote'
    id = db.Column(db.Integer, primary_key=True, name='order_id')
    no = db.Column(db.String(100), name='cext1')
    status = db.Column(db.Integer, name='order_status')
    service_object = db.Column(db.String(100))  # 服务对象姓名，没用
    project_type = db.Column(db.String(100))
    # 工单时间
    start_time = db.Column(db.String(100))
    end_time = db.Column(db.String(100))
    create_time = db.Column(db.String(100))
    handle_time = db.Column(db.String(100))
    pay_time = db.Column(db.String(100))
    # 服务地址
    order_area_code = db.Column(db.String(100))
    order_area_name = db.Column(db.String(1000))
    # 服务主客体信息
    service_id = db.Column(db.Integer, db.ForeignKey('service.service_id'))
    member_id = db.Column(db.Integer, db.ForeignKey('member.member_id'))
    handler = db.Column(db.Integer, db.ForeignKey('employee.emp_id'))
    to_user = db.Column(db.Integer, db.ForeignKey('employee.emp_id'))

    def to_dict(self, keys=None):
        kwargs = {c.key: getattr(self, c.key) for c in inspect(self).mapper.column_attrs}
        if keys is dict:
            for key in kwargs.keys():
                if key not in keys:
                    kwargs.pop(key)
        return kwargs

class MemberModel(db.Model):
    __tablename__ = 'member'
    __bind_key__ = 'remote'
    id = db.Column(db.Integer, primary_key=True, name='member_id')
    # 身份信息
    name = db.Column(db.String(100), name='real_name')
    gender = db.Column(db.Integer)
    # 地址信息
    area_code = db.Column(db.String(100))
    area_name = db.Column(db.String(1000))
    phone_no = db.Column(db.String(100))
    # 其他信息
    member_type = db.Column(db.Integer)
    user_id = db.Column(db.Integer)
    emp_id = db.Column(db.Integer)
    status = db.Column(db.Integer)
    member_tag = db.Column(db.String(100))
    is_disabled = db.Column(db.String(100), name='is_disabl')

    def to_dict(self, keys=None):
        kwargs = {c.key: getattr(self, c.key) for c in inspect(self).mapper.column_attrs}
        if keys is dict:
            for key in kwargs.keys():
                if key not in keys:
                    kwargs.pop(key)
        return kwargs

class EmployeeModel(db.Model):
    __tablename__ = 'employee'
    __bind_key__ = 'remote'
    id = db.Column(db.Integer, primary_key=True, name='emp_id')
    # 身份信息
    name = db.Column(db.String(100), name='real_name')
    sex = db.Column(db.Integer)
    identity_card = db.Column(db.String(1000))
    # 地址信息
    area_code = db.Column(db.String(100))
    area_name = db.Column(db.String(1000))
    phone_no = db.Column(db.String(100))
    # 照片信息
    document_photo = db.Column(db.String(1000))
    front_card = db.Column(db.String(1000))
    reverse_card = db.Column(db.String(1000))
    me_photo = db.Column(db.String(1000))
    # 状态信息
    status = db.Column(db.String(100))

    def to_dict(self, keys=None):
        kwargs = {c.key: getattr(self, c.key) for c in inspect(self).mapper.column_attrs}
        if keys is dict:
            for key in kwargs.keys():
                if key not in keys:
                    kwargs.pop(key)
        return kwargs

class ServiceLogModel(db.Model):
    __tablename__ = 'service_log'
    __bind_key__ = 'remote'
    id = db.Column(db.Integer, primary_key=True, name='cid')
    # 开始信息
    start_content = db.Column(db.String(100))
    start_img = db.Column(db.String(1000))
    start_location = db.Column(db.String(1000))
    start_time = db.Column(db.String(100))
    start_lat = db.Column(db.String(100))
    start_lgt = db.Column(db.String(100))
    start_coordinate = (start_lat, start_lgt)
    # 中间信息
    service_content = db.Column(db.String(100))
    img_url = db.Column(db.String(1000))
    location = db.Column(db.String(1000))
    create_time = db.Column(db.String(100))
    lat = db.Column(db.String(100))
    lgt = db.Column(db.String(100))
    coordinate = (lat, lgt)
    # 结束信息
    end_content = db.Column(db.String(100))
    end_img = db.Column(db.String(1000))
    end_location = db.Column(db.String(1000))
    end_time = db.Column(db.String(100))
    end_lat = db.Column(db.String(100))
    end_lgt = db.Column(db.String(100))
    end_coordinate = (end_lat, end_lgt)
    # 服务主客体信息
    order_id = db.Column(db.Integer, name='order_id')

    def to_dict(self, keys=None):
        kwargs = {c.key: getattr(self, c.key) for c in inspect(self).mapper.column_attrs}
        kwargs['middle_content'] = kwargs['service_content']
        del kwargs['service_content']
        kwargs['middle_img'] = kwargs['img_url']
        del kwargs['img_url']
        kwargs['middle_location'] = kwargs['location']
        del kwargs['location']
        kwargs['middle_coordinate'] = (self.lat, self.lgt)
        kwargs['start_coordinate'] = (self.start_lat, self.start_lgt)
        kwargs['end_coordinate'] = (self.end_lat, self.end_lgt)

        if keys is dict:
            for key in kwargs.keys():
                if key not in keys:
                    kwargs.pop(key)

        return kwargs

class ExecuteModel(db.Model):
    __tablename__ = 'execute'
    id=db.Column(db.Integer, primary_key=True)
    service_id = db.Column(db.Integer, db.ForeignKey('order.service_id'), nullable=False)
    image_stage = db.Column(db.String(255))
    flow_id = db.Column(db.Integer,nullable=False)
