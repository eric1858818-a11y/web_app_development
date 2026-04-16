from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from datetime import date, datetime
from sqlalchemy import func, extract
from app.models.schemas import db, Transaction, Account, Budget
from app.routes.auth import login_required

expense_bp = Blueprint('expense', __name__)

@expense_bp.route('/')
@expense_bp.route('/dashboard')
@login_required
def dashboard():
    """
    顯示總覽儀表板。
    讀取首頁所需統整數據、近期開銷，渲染 dashboard.html。
    """
    user_id = session['user_id']
    today = date.today()

    # 當月收入
    monthly_income = db.session.query(func.coalesce(func.sum(Transaction.amount), 0)).filter(
        Transaction.user_id == user_id,
        Transaction.type == 'income',
        extract('year', Transaction.date) == today.year,
        extract('month', Transaction.date) == today.month
    ).scalar()

    # 當月支出
    monthly_expense = db.session.query(func.coalesce(func.sum(Transaction.amount), 0)).filter(
        Transaction.user_id == user_id,
        Transaction.type == 'expense',
        extract('year', Transaction.date) == today.year,
        extract('month', Transaction.date) == today.month
    ).scalar()

    # 總資產
    total_balance = db.session.query(func.coalesce(func.sum(Account.balance), 0)).filter(
        Account.user_id == user_id
    ).scalar()

    # 最近 10 筆紀錄
    recent_transactions = Transaction.query.filter_by(user_id=user_id).order_by(
        Transaction.date.desc(), Transaction.id.desc()
    ).limit(10).all()

    return render_template('expense/dashboard.html',
                           monthly_income=monthly_income,
                           monthly_expense=monthly_expense,
                           total_balance=total_balance,
                           recent_transactions=recent_transactions)


@expense_bp.route('/expense/add', methods=['GET', 'POST'])
@login_required
def add_expense():
    """
    處理新增消費紀錄。
    GET: 渲染記帳表單 (附帶帳戶列表)。
    POST: 儲存新紀錄並自動扣除或增加關聯帳戶的金額。
    """
    user_id = session['user_id']
    accounts = Account.query.filter_by(user_id=user_id).all()

    if request.method == 'POST':
        try:
            amount = float(request.form.get('amount', 0))
            category = request.form.get('category', '').strip()
            tx_type = request.form.get('type', 'expense')
            tx_date = request.form.get('date', str(date.today()))
            account_id = int(request.form.get('account_id', 0))
            to_account_id = request.form.get('to_account_id', '') or None
            description = request.form.get('description', '').strip()

            if amount <= 0 or not category:
                flash('請填寫正確的金額與類別。', 'danger')
                return render_template('expense/form.html', accounts=accounts, today=date.today())

            if to_account_id:
                to_account_id = int(to_account_id)

            # 建立交易
            Transaction.create(
                user_id=user_id,
                account_id=account_id,
                to_account_id=to_account_id,
                category=category,
                amount=amount,
                type=tx_type,
                date=datetime.strptime(tx_date, '%Y-%m-%d').date(),
                description=description
            )

            # 更新帳戶餘額
            account = Account.get_by_id(account_id)
            if tx_type == 'expense':
                account.update(balance=account.balance - amount)
            elif tx_type == 'income':
                account.update(balance=account.balance + amount)
            elif tx_type == 'transfer' and to_account_id:
                to_account = Account.get_by_id(to_account_id)
                account.update(balance=account.balance - amount)
                to_account.update(balance=to_account.balance + amount)

            flash('紀錄新增成功！', 'success')
            return redirect(url_for('expense.dashboard'))

        except Exception as e:
            flash(f'新增失敗：{str(e)}', 'danger')

    return render_template('expense/form.html', accounts=accounts, today=date.today(), transaction=None)


@expense_bp.route('/expense/history')
@login_required
def expense_history():
    """
    顯示歷史紀錄。
    支援透過 GET 參數進行月份篩選。
    """
    user_id = session['user_id']
    selected_month = request.args.get('month', '')

    query = Transaction.query.filter_by(user_id=user_id)

    if selected_month:
        try:
            year, month = map(int, selected_month.split('-'))
            query = query.filter(
                extract('year', Transaction.date) == year,
                extract('month', Transaction.date) == month
            )
        except ValueError:
            pass

    transactions = query.order_by(Transaction.date.desc(), Transaction.id.desc()).all()

    return render_template('expense/history.html',
                           transactions=transactions,
                           selected_month=selected_month)


@expense_bp.route('/expense/edit/<int:item_id>', methods=['GET', 'POST'])
@login_required
def edit_expense(item_id):
    """
    編輯特定記帳紀錄。
    GET: 讀取指定項目並渲染表單。
    POST: 計算差額、修正帳戶餘額，最後更新該紀錄。
    """
    user_id = session['user_id']
    transaction = Transaction.query.filter_by(id=item_id, user_id=user_id).first()

    if not transaction:
        flash('找不到該筆紀錄。', 'danger')
        return redirect(url_for('expense.expense_history'))

    accounts = Account.query.filter_by(user_id=user_id).all()

    if request.method == 'POST':
        try:
            old_amount = transaction.amount
            old_type = transaction.type
            old_account_id = transaction.account_id
            old_to_account_id = transaction.to_account_id

            new_amount = float(request.form.get('amount', 0))
            new_category = request.form.get('category', '').strip()
            new_type = request.form.get('type', 'expense')
            new_date = request.form.get('date', str(date.today()))
            new_account_id = int(request.form.get('account_id', 0))
            new_to_account_id = request.form.get('to_account_id', '') or None
            new_description = request.form.get('description', '').strip()

            if new_to_account_id:
                new_to_account_id = int(new_to_account_id)

            # 還原舊的帳戶餘額
            old_account = Account.get_by_id(old_account_id)
            if old_type == 'expense':
                old_account.update(balance=old_account.balance + old_amount)
            elif old_type == 'income':
                old_account.update(balance=old_account.balance - old_amount)
            elif old_type == 'transfer' and old_to_account_id:
                old_to = Account.get_by_id(old_to_account_id)
                old_account.update(balance=old_account.balance + old_amount)
                old_to.update(balance=old_to.balance - old_amount)

            # 套用新的帳戶餘額
            new_account = Account.get_by_id(new_account_id)
            if new_type == 'expense':
                new_account.update(balance=new_account.balance - new_amount)
            elif new_type == 'income':
                new_account.update(balance=new_account.balance + new_amount)
            elif new_type == 'transfer' and new_to_account_id:
                new_to = Account.get_by_id(new_to_account_id)
                new_account.update(balance=new_account.balance - new_amount)
                new_to.update(balance=new_to.balance + new_amount)

            # 更新交易紀錄
            transaction.update(
                amount=new_amount,
                category=new_category,
                type=new_type,
                date=datetime.strptime(new_date, '%Y-%m-%d').date(),
                account_id=new_account_id,
                to_account_id=new_to_account_id,
                description=new_description
            )

            flash('紀錄更新成功！', 'success')
            return redirect(url_for('expense.expense_history'))

        except Exception as e:
            flash(f'更新失敗：{str(e)}', 'danger')

    return render_template('expense/form.html', accounts=accounts, transaction=transaction, today=date.today())


@expense_bp.route('/expense/delete/<int:item_id>', methods=['POST'])
@login_required
def delete_expense(item_id):
    """
    刪除特定記帳紀錄。
    還原被扣除/增加的帳戶餘額，並將該紀錄從 DB 移除。
    """
    user_id = session['user_id']
    transaction = Transaction.query.filter_by(id=item_id, user_id=user_id).first()

    if not transaction:
        flash('找不到該筆紀錄。', 'danger')
        return redirect(url_for('expense.expense_history'))

    try:
        # 還原帳戶餘額
        account = Account.get_by_id(transaction.account_id)
        if transaction.type == 'expense':
            account.update(balance=account.balance + transaction.amount)
        elif transaction.type == 'income':
            account.update(balance=account.balance - transaction.amount)
        elif transaction.type == 'transfer' and transaction.to_account_id:
            to_account = Account.get_by_id(transaction.to_account_id)
            account.update(balance=account.balance + transaction.amount)
            to_account.update(balance=to_account.balance - transaction.amount)

        transaction.delete()
        flash('紀錄已刪除。', 'success')
    except Exception as e:
        flash(f'刪除失敗：{str(e)}', 'danger')

    return redirect(url_for('expense.expense_history'))


@expense_bp.route('/report')
@login_required
def report():
    """
    顯示統計分析報表頁面。
    產生區間內的收支趨勢與圓餅圖數據。
    """
    user_id = session['user_id']

    # 支出類別分佈 (當月)
    today = date.today()
    category_rows = db.session.query(
        Transaction.category,
        func.sum(Transaction.amount)
    ).filter(
        Transaction.user_id == user_id,
        Transaction.type == 'expense',
        extract('year', Transaction.date) == today.year,
        extract('month', Transaction.date) == today.month
    ).group_by(Transaction.category).all()

    category_data = {
        'labels': [r[0] for r in category_rows],
        'values': [float(r[1]) for r in category_rows]
    }

    # 近 6 個月收支趨勢
    trend_labels = []
    trend_income = []
    trend_expense = []
    for i in range(5, -1, -1):
        m = today.month - i
        y = today.year
        while m <= 0:
            m += 12
            y -= 1
        label = f'{y}-{m:02d}'
        trend_labels.append(label)

        inc = db.session.query(func.coalesce(func.sum(Transaction.amount), 0)).filter(
            Transaction.user_id == user_id,
            Transaction.type == 'income',
            extract('year', Transaction.date) == y,
            extract('month', Transaction.date) == m
        ).scalar()
        exp = db.session.query(func.coalesce(func.sum(Transaction.amount), 0)).filter(
            Transaction.user_id == user_id,
            Transaction.type == 'expense',
            extract('year', Transaction.date) == y,
            extract('month', Transaction.date) == m
        ).scalar()
        trend_income.append(float(inc))
        trend_expense.append(float(exp))

    trend_data = {
        'labels': trend_labels,
        'income': trend_income,
        'expense': trend_expense
    }

    return render_template('expense/report.html',
                           category_data=category_data,
                           trend_data=trend_data)


@expense_bp.route('/account')
@login_required
def list_accounts():
    """列出所有資金帳戶及各帳戶餘額。"""
    user_id = session['user_id']
    accounts = Account.query.filter_by(user_id=user_id).all()
    total_balance = sum(a.balance for a in accounts)
    return render_template('expense/account.html', accounts=accounts, total_balance=total_balance)


@expense_bp.route('/account/add', methods=['POST'])
@login_required
def add_account():
    """新增資金帳戶。"""
    user_id = session['user_id']
    name = request.form.get('name', '').strip()
    balance = float(request.form.get('balance', 0))

    if not name:
        flash('請輸入帳戶名稱。', 'danger')
    else:
        try:
            Account.create(user_id=user_id, name=name, balance=balance)
            flash(f'帳戶「{name}」已建立！', 'success')
        except Exception as e:
            flash(f'建立失敗：{str(e)}', 'danger')

    return redirect(url_for('expense.list_accounts'))


@expense_bp.route('/budget')
@login_required
def view_budget():
    """檢視預算設定及當月超支狀況。"""
    user_id = session['user_id']
    today = date.today()
    current_month = today.strftime('%Y-%m')

    budgets = Budget.query.filter_by(user_id=user_id, month=current_month).all()

    # 計算每個類別的本月已支出
    budget_list = []
    for b in budgets:
        if b.category == 'All':
            spent = db.session.query(func.coalesce(func.sum(Transaction.amount), 0)).filter(
                Transaction.user_id == user_id,
                Transaction.type == 'expense',
                extract('year', Transaction.date) == today.year,
                extract('month', Transaction.date) == today.month
            ).scalar()
        else:
            spent = db.session.query(func.coalesce(func.sum(Transaction.amount), 0)).filter(
                Transaction.user_id == user_id,
                Transaction.type == 'expense',
                Transaction.category == b.category,
                extract('year', Transaction.date) == today.year,
                extract('month', Transaction.date) == today.month
            ).scalar()
        budget_list.append({
            'category': b.category,
            'amount': b.amount,
            'spent': float(spent)
        })

    return render_template('expense/budget.html',
                           budgets=budget_list,
                           current_month=current_month)


@expense_bp.route('/budget/update', methods=['POST'])
@login_required
def update_budget():
    """更新預算設定。"""
    user_id = session['user_id']
    category = request.form.get('category', '').strip()
    amount = float(request.form.get('amount', 0))
    month = request.form.get('month', date.today().strftime('%Y-%m'))

    if not category or amount <= 0:
        flash('請填寫正確的類別與金額。', 'danger')
        return redirect(url_for('expense.view_budget'))

    try:
        existing = Budget.query.filter_by(user_id=user_id, category=category, month=month).first()
        if existing:
            existing.update(amount=amount)
            flash(f'預算「{category}」已更新！', 'success')
        else:
            Budget.create(user_id=user_id, category=category, amount=amount, month=month)
            flash(f'預算「{category}」已建立！', 'success')
    except Exception as e:
        flash(f'儲存失敗：{str(e)}', 'danger')

    return redirect(url_for('expense.view_budget'))
