from flask import Flask
from .models.schemas import db

def create_app(config_object=None):
    app = Flask(__name__)
    
    # 基礎設定
    app.config['SECRET_KEY'] = 'dev_fallback_secret'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    if config_object:
        app.config.from_object(config_object)
        
    # 初始化資料庫
    db.init_app(app)
    
    with app.app_context():
        # 自動建立所有 tables
        db.create_all()

    # 註冊 Blueprints
    from .routes.auth import auth_bp
    from .routes.expense import expense_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(expense_bp)

    return app
