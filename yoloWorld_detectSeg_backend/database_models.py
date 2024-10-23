from extensions import db
from datetime import datetime


class UserModel(db.Model):
    __tablename__ = 'user'
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
            'roles': self.roles.role_name,
        }


class RoleModel(db.Model):
    __tablename__ = 'role'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='角色id')
    name = db.Column(db.String(100), nullable=False, comment='角色名称')
    desc = db.Column(db.String(100), nullable=False, comment='角色描述')


class CaptchaModel(db.Model):
    __tablename__ = 'captcha'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String(100), nullable=True, comment='验证邮箱')
    captcha = db.Column(db.String(100), nullable=False, comment='验证码')
    create_time = db.Column(db.DateTime, default=datetime.now, comment='创建时间')
    is_used = db.Column(db.Boolean, default=False, comment='是否使用')


class DatasetModel(db.Model):
    __tablename__ = 'dataset'
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
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='任务类型ID')
    name = db.Column(db.String(100), nullable=False, comment='任务类型名称')
    # Add more fields as needed
    # Relationship: 反向关联到 TaskModel，通过外键 type_id 建立的关联
    tasks = db.relationship('TaskModel', backref='task_type', lazy=True)

# Task Model
class TaskModel(db.Model):
    __tablename__ = 'task'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='任务ID')
    name = db.Column(db.String(50), nullable=False, comment='任务名称')
    type_id = db.Column(db.Integer, db.ForeignKey('task_type.id'), nullable=True, comment='任务类型ID')
    # Relationship
    flows = db.relationship('FlowModel', backref='task', lazy=True)

    def to_dict(self):
        return {
            'name': self.name,
        }

# Flow Model
class FlowModel(db.Model):
    __tablename__ = 'flow'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='流程ID')
    name = db.Column(db.String(100), nullable=False, comment='流程名称')
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'), nullable=False, comment='任务ID')
    # Relationship
    releases = db.relationship('ReleaseModel', backref='flow', lazy=True)

    def to_dict(self):
        return {
            'name': self.name,
            'releases': [release.to_dict() for release in self.releases],
        }
    def to_config(self):
        return {
            'type': self.name,
            'releases': [release.to_dict() for release in self.releases],
        }

# Release Model
class ReleaseModel(db.Model):
    __tablename__ = 'release'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='版本ID')
    name = db.Column(db.String(100), nullable=False, comment='版本名称')
    show_name = db.Column(db.String(100), nullable=False, comment='显示名称')
    flow_id = db.Column(db.Integer, db.ForeignKey('flow.id'), nullable=False, comment='流程ID')
    keys = db.Column(db.JSON, nullable=False, comment='关键字组')
    params = db.Column(db.JSON, nullable=False, comment='固定参数组')
    # Relationship
    release_weights = db.relationship('ReleaseWeightModel', backref='release', lazy=True)

    def check_weight(self, weight):
        for release_weight in self.release_weights:
            if release_weight.weight_id == weight.id:
                return True
        return False

    def to_dict(self):
        return {
            'name': self.name,
            'show_name': self.show_name,
        }

    def to_weights(self):
        weights = []
        for release_weight in self.release_weights:
            weight = release_weight.weight
            cfg = weight.to_dict()
            cfg['weightKey'] = release_weight.key
            weights.append(cfg)
        return weights

    def to_params(self):
        params = []
        for key, value in self.params.items():
            params.append({
                'paramName': key,
                'paramValue': value,
            })
        return params

    def to_config(self):
        if not hasattr(self, '_flow'):
            self._flow = FlowModel.query.get(self.flow_id)
        config = {
            'type': self._flow.name,
            'name': self.name,
            'display_name': self.show_name,
        }
        config.update(self.params)
        config.update({key: {} for key in self.keys})
        return config

# ReleaseWeight Model (Junction table for release and weight)
class ReleaseWeightModel(db.Model):
    __tablename__ = 'release_weight'
    release_id = db.Column(db.Integer, db.ForeignKey('release.id'), primary_key=True, nullable=False, comment='版本ID')
    weight_id = db.Column(db.Integer, db.ForeignKey('weight.id'), primary_key=True, nullable=False, comment='权重ID')
    key = db.Column(db.String(100), nullable=False, comment='关键字')
    # Relationships
    # _release = db.relationship('ReleaseModel', backref=db.backref('release_weight', lazy=True))
    # _weight = db.relationship('WeightModel', backref=db.backref('release_weight', lazy=True))

class WeightModel(db.Model):
    __tablename__ = 'weight'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='权重id')
    name = db.Column(db.String(100), nullable=False, comment='权重名称')
    local_path = db.Column(db.Text, nullable=True, comment='本地保存路径')
    online_url = db.Column(db.Text, nullable=True, comment='在线访问地址')
    enable = db.Column(db.Boolean, default=False, nullable=False, comment='是否启用')
    # ForeignKey
    dataset_id = db.Column(db.Integer, db.ForeignKey('dataset.id'), nullable=True)
    # Relationship
    dataset = db.relationship('DatasetModel', backref=db.backref('weight'))
    release_weights = db.relationship('ReleaseWeightModel', backref='weight', lazy=True)

    def to_dict(self):
        return {
            'weightName': self.name,
            'weightEnable': self.enable,
        }

    def to_config(self):
        return {
            'local': self.local_path,
            'online': self.online_url,
        }

class ResultModel(db.Model):
    __tablename__ = 'result'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='推理结果id')
    img_path = db.Column(db.String(100), nullable=False, comment='原始图片名称')
    data = db.Column(db.Text, nullable=False, comment='结果数据')
    plot_path = db.Column(db.String(100), nullable=False, comment='结果图片名称')
    start_time = db.Column(db.DateTime, default=datetime.now, comment='开始时间')
    end_time = db.Column(db.DateTime, default=datetime.now, comment='结束时间')
    hyper = db.Column(db.JSON, nullable=True, comment='动态超参数')
    # ForeignKey
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    release_id = db.Column(db.Integer, db.ForeignKey('release.id'))
    # Relationship
    user = db.relationship('UserModel', backref=db.backref('result'))
    release = db.relationship('ReleaseModel', backref=db.backref('result'))
