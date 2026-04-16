from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class BaseModel:
    """提供基本的 CRUD 功能（包含錯誤處理機制）"""
    
    @classmethod
    def create(cls, **kwargs):
        """
        新增一筆記錄
        :param kwargs: 表單或請求中對應模型各欄位的值
        :return: 新建立的模型實例
        """
        try:
            obj = cls(**kwargs)
            db.session.add(obj)
            db.session.commit()
            return obj
        except Exception as e:
            db.session.rollback()
            raise e

    @classmethod
    def get_by_id(cls, item_id):
        """
        取得單筆記錄
        :param item_id: 資料的主鍵 ID
        :return: 模型實例 (找不到時為 None)
        """
        try:
            return db.session.get(cls, item_id)
        except Exception as e:
            raise e

    @classmethod
    def get_all(cls):
        """
        取得所有記錄
        :return: 包含所有記錄的列表
        """
        try:
            return cls.query.all()
        except Exception as e:
            raise e

    def update(self, **kwargs):
        """
        更新記錄
        :param kwargs: 欲更改的欄位與對應新值
        """
        try:
            for key, value in kwargs.items():
                if hasattr(self, key):
                    setattr(self, key, value)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise e

    def delete(self):
        """
        刪除記錄
        """
        try:
            db.session.delete(self)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise e

class User(BaseModel, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    accounts = db.relationship('Account', backref='user', lazy=True, cascade="all, delete-orphan")
    transactions = db.relationship('Transaction', backref='user', lazy=True, cascade="all, delete-orphan")
    budgets = db.relationship('Budget', backref='user', lazy=True, cascade="all, delete-orphan")

class Account(BaseModel, db.Model):
    __tablename__ = 'accounts'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(50), nullable=False)
    balance = db.Column(db.Float, default=0.0, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Transaction(BaseModel, db.Model):
    __tablename__ = 'transactions'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    account_id = db.Column(db.Integer, db.ForeignKey('accounts.id'), nullable=False)
    to_account_id = db.Column(db.Integer, db.ForeignKey('accounts.id'), nullable=True) # For transfers
    category = db.Column(db.String(50), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    type = db.Column(db.String(10), nullable=False) # 'expense', 'income', 'transfer'
    date = db.Column(db.Date, nullable=False)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    account = db.relationship('Account', foreign_keys=[account_id], backref='transactions_from', lazy=True)
    to_account = db.relationship('Account', foreign_keys=[to_account_id], backref='transactions_to', lazy=True)

class Budget(BaseModel, db.Model):
    __tablename__ = 'budgets'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    month = db.Column(db.String(7), nullable=False) # Format: YYYY-MM
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
