from flask import Blueprint, render_template, request, redirect, url_for, flash, session

expense_bp = Blueprint('expense', __name__)

@expense_bp.route('/')
@expense_bp.route('/dashboard')
def dashboard():
    """
    顯示總覽儀表板。
    讀取首頁所需統整數據、近期開銷，渲染 dashboard.html。
    """
    pass

@expense_bp.route('/expense/add', methods=['GET', 'POST'])
def add_expense():
    """
    處理新增消費紀錄。
    GET: 渲染記帳表單 (附帶帳戶列表)。
    POST: 儲存新紀錄並自動扣除或增加關聯帳戶的金額。
    """
    pass

@expense_bp.route('/expense/history')
def expense_history():
    """
    顯示歷史紀錄。
    支援透過 GET 參數進行月份與分類的篩選。
    """
    pass

@expense_bp.route('/expense/edit/<int:item_id>', methods=['GET', 'POST'])
def edit_expense(item_id):
    """
    編輯特定記帳紀錄。
    GET: 讀取指定項目並渲染表單。
    POST: 計算差額、修正帳戶餘額，最後更新該紀錄。
    """
    pass

@expense_bp.route('/expense/delete/<int:item_id>', methods=['POST'])
def delete_expense(item_id):
    """
    刪除特定記帳紀錄。
    還原被扣除/增加的帳戶餘額，並將該紀錄標示刪除或從 DB 徹底移除。
    """
    pass

@expense_bp.route('/report')
def report():
    """
    顯示統計分析報表頁面。
    產生區間內的收支趨勢與圓餅圖數據。
    """
    pass

@expense_bp.route('/account')
def list_accounts():
    """
    列出所有資金帳戶及各帳戶餘額。
    """
    pass

@expense_bp.route('/account/add', methods=['GET', 'POST'])
def add_account():
    """
    新增資金帳戶。
    GET: 顯示新增帳戶表單。
    POST: 寫入新帳戶與初始餘額。
    """
    pass

@expense_bp.route('/budget')
def view_budget():
    """
    檢視預算設定及當月超支狀況。
    """
    pass

@expense_bp.route('/budget/update', methods=['POST'])
def update_budget():
    """
    更新預算設定。
    接收表單的各分類上限額度並存入資料庫。
    """
    pass
