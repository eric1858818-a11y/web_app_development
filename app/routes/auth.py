from flask import Blueprint, render_template, request, redirect, url_for, flash, session

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """
    處理使用者註冊。
    GET: 渲染註冊表單。
    POST: 接收註冊資料，驗證與儲存後重導至登入。
    """
    pass

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    處理使用者登入。
    GET: 渲染登入表單。
    POST: 驗證帳號密碼，成功後紀錄 session 並重導至總覽。
    """
    pass

@auth_bp.route('/logout')
def logout():
    """
    處理使用者登出。
    清除 session 並重導至登入畫面。
    """
    pass
