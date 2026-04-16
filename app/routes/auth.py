from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from functools import wraps
import bcrypt
from app.models.schemas import db, User, Account

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

def login_required(f):
    """裝飾器：檢查使用者是否已登入，未登入則重導至登入頁。"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('請先登入。', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """
    處理使用者註冊。
    GET: 渲染註冊表單。
    POST: 接收註冊資料，驗證與儲存後重導至登入。
    """
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        # 驗證
        if not username or not password:
            flash('帳號和密碼為必填欄位。', 'danger')
            return render_template('auth/register.html')
        if password != confirm_password:
            flash('兩次密碼輸入不一致。', 'danger')
            return render_template('auth/register.html')
        if User.query.filter_by(username=username).first():
            flash('此帳號已被註冊。', 'danger')
            return render_template('auth/register.html')

        # 建立使用者
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        user = User.create(username=username, password_hash=password_hash)

        # 自動建立一個「現金」帳戶
        Account.create(user_id=user.id, name='現金', balance=0.0)

        flash('註冊成功！請登入。', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    處理使用者登入。
    GET: 渲染登入表單。
    POST: 驗證帳號密碼，成功後紀錄 session 並重導至總覽。
    """
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        user = User.query.filter_by(username=username).first()
        if user and bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
            session['user_id'] = user.id
            flash(f'歡迎回來，{user.username}！', 'success')
            return redirect(url_for('expense.dashboard'))
        else:
            flash('帳號或密碼錯誤。', 'danger')
            return render_template('auth/login.html')

    return render_template('auth/login.html')

@auth_bp.route('/logout')
def logout():
    """
    處理使用者登出。
    清除 session 並重導至登入畫面。
    """
    session.clear()
    flash('您已成功登出。', 'info')
    return redirect(url_for('auth.login'))
