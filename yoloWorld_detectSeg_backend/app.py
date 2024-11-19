import logging

import sqlalchemy
from flask_cors import CORS
from flask_session import Session

import config
import argparse
import os

from flask import Flask, g, session
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager

from extensions import *

from database_models import *
from blueprints.auth_bp import bp as auth_bp
from blueprints.server_bp import bp as server_bp
from blueprints.user_manage_bp import bp as user_manage_bp
from blueprints.infer_bp import bp as infer_bp
from blueprints.infer_local_bp import bp as infer_local_bp
from blueprints.task_type_manage_bp import bp as task_type_manage_bp
from blueprints.task_manage_bp import bp as task_manage_bp
from blueprints.flow_manage_bp import bp as flow_manage_bp
from blueprints.weight_manage_bp import bp as weight_manage_bp
from blueprints.release_manage_bp import bp as release_manage_bp
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
repo_dir = os.getcwd()
weights_path = 'weights/yolov5-3.1/TACO_yolov5s_300_epochs.pt'
model_load_path = os.path.join(repo_dir, weights_path)
weights_name = 'yolov5-3.1'
# os.environ['FLASK_DEBUG'] = '0'
app = Flask(__name__)
app.config.from_object(config)
# 配置 Redis 作为会话存储
# 使用文件系统作为会话存储
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = './flask_sessions'
app.config['SESSION_PERMANENT'] = False  # 浏览器关闭时会话失效
app.config['SESSION_USE_SIGNER'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = 0  # 设置为0可以保证关闭浏览器立即失效

# 初始化 Flask-Session
Session(app)

db.init_app(app)
jwt = JWTManager(app)
mail.init_app(app)
'''
flask db init
flask db migrate
flask db upgrade
'''
migrate = Migrate(app, db)

app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(server_bp, url_prefix='/server')
app.register_blueprint(user_manage_bp, url_prefix='/user-manage')
app.register_blueprint(task_type_manage_bp, url_prefix='/task_type-manage')
app.register_blueprint(task_manage_bp, url_prefix='/task-manage')
app.register_blueprint(flow_manage_bp, url_prefix='/flow-manage')
app.register_blueprint(weight_manage_bp, url_prefix='/weight-manage')
app.register_blueprint(release_manage_bp, url_prefix='/release-manage')
app.register_blueprint(infer_bp, url_prefix='/infer')
app.register_blueprint(infer_local_bp, url_prefix='/infer_local')
CORS(app, supports_credentials=True)

@app.before_request
def cleanup_expired_sessions():
    session_folder = app.config['SESSION_FILE_DIR']
    for filename in os.listdir(session_folder):
        file_path = os.path.join(session_folder, filename)
        if os.path.isfile(file_path):
            try:
                # 删除过期的会话文件
                os.remove(file_path)
            except Exception as e:
                print(f"Error deleting session file {file_path}: {e}")


def test_database_connection():
    with app.app_context():
        with db.engine.connect() as conn:
            res = conn.execute(sqlalchemy.text('select 1'))
            if res.fetchone()[0] == 1:
                logging.info('Database connection successful')
            else:
                logging.error('Database connection failed')


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Flask app exposing yolov5 models")
    parser.add_argument("--port", default=5555, type=int, help="port number")
    args = parser.parse_args()

    # webapp启动后加载默认调用权重
    test_database_connection()
    logging.info('项目已启动')
    app.run(host="127.0.0.1", port=args.port, debug=False)
