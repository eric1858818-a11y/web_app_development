# 路由與頁面設計文件 (Routes)

## 1. 路由總覽表格

| 功能模組 | HTTP 方法 | URL 路徑 | 對應模板 | 說明 |
| --- | --- | --- | --- | --- |
| **Auth** | GET | `/auth/register` | `auth/register.html` | 顯示註冊表單 |
| **Auth** | POST | `/auth/register` | — | 接收註冊資料，寫入 DB，重導至登入 |
| **Auth** | GET | `/auth/login` | `auth/login.html` | 顯示登入表單 |
| **Auth** | POST | `/auth/login` | — | 驗證登入資料，成功後重導至首頁 |
| **Auth** | GET | `/auth/logout` | — | 登出並清除 Session，重導至登入頁 |
| **Expense** | GET | `/` 或 `/dashboard` | `expense/dashboard.html` | 顯示總覽數據與圖表 |
| **Expense** | GET | `/expense/add` | `expense/form.html` | 顯示記帳表單 (新增) |
| **Expense** | POST | `/expense/add` | — | 接收記帳表單並寫入 DB |
| **Expense** | GET | `/expense/history` | `expense/history.html` | 顯示歷史紀錄列表 |
| **Expense** | GET | `/expense/edit/<id>`| `expense/form.html` | 顯示記帳表單 (編輯) |
| **Expense** | POST | `/expense/edit/<id>`| — | 接收編輯表單，更新該筆紀錄 |
| **Expense** | POST | `/expense/delete/<id>`| — | 刪除該筆紀錄並重導 |
| **Report** | GET | `/report` | `expense/report.html` | 顯示統計分析報表 |
| **Account** | GET | `/account` | `expense/account.html` | 顯示資金帳戶列表與餘額 |
| **Account** | GET | `/account/add` | `expense/account_form.html` | 顯示新增帳戶表單 |
| **Account** | POST | `/account/add` | — | 接收帳戶表單並寫入 DB |
| **Budget** | GET | `/budget` | `expense/budget.html` | 顯示預算設定與狀態 |
| **Budget** | POST | `/budget/update` | — | 更新預算資料並寫入 DB |

---

## 2. 每個路由的詳細說明

### Auth 模組 (`auth.py`)

*   **GET `/auth/register`**
    *   **輸入**：無
    *   **處理邏輯**：無特殊邏輯
    *   **輸出**：渲染 `auth/register.html`
*   **POST `/auth/register`**
    *   **輸入**：表單欄位 `username`, `password`, `confirm_password`
    *   **處理邏輯**：驗證輸入、檢查帳號是否重複、雜湊密碼、建立 `User` 與基礎 `Account` (如現金)
    *   **錯誤處理**：帳號重複或密碼不符時回傳錯誤訊息並重新渲染註冊表
    *   **輸出**：重導至 `/auth/login`
*   **GET `/auth/login`**
    *   **輸入**：無
    *   **處理邏輯**：無特殊邏輯
    *   **輸出**：渲染 `auth/login.html`
*   **POST `/auth/login`**
    *   **輸入**：表單欄位 `username`, `password`
    *   **處理邏輯**：比對帳號與密碼雜湊，通過後將 user_id 寫入 session
    *   **錯誤處理**：驗證失敗則重新渲染並顯示錯誤提示
    *   **輸出**：成功後重導至 `/dashboard`
*   **GET `/auth/logout`**
    *   **輸入**：無
    *   **處理邏輯**：清除 session 中的 user_id
    *   **輸出**：重導至 `/auth/login`

### Expense 核心模組 (`expense.py`)

*(所有 Expense 模組路由均需登入驗證)*

*   **GET `/dashboard` (與 `/`)**
    *   **輸入**：Session 中的 user_id
    *   **處理邏輯**：計算當月總收入、總支出、可動用餘額，提取近期記帳項目與圖表資料
    *   **輸出**：渲染 `expense/dashboard.html`
*   **GET `/expense/add`**
    *   **輸入**：無
    *   **處理邏輯**：讀取使用者的 `Account` 列表供下拉選單使用
    *   **輸出**：渲染 `expense/form.html`
*   **POST `/expense/add`**
    *   **輸入**：`amount`, `category`, `account_id`, `type`, `date`, `description`, (如果為轉帳則需 `to_account_id`)
    *   **處理邏輯**：驗證輸入、建立 `Transaction` 紀錄。依照 type 更新 `Account` 的 balance。
    *   **錯誤處理**：欄位缺漏則帶有錯誤訊息回傳原表單
    *   **輸出**：重導回 `/dashboard` 或 `/expense/history`
*   **GET `/expense/history`**
    *   **輸入**：查詢參數 (Query String) 提供年月篩選 (例如 `?month=2023-10`)
    *   **處理邏輯**：撈取符合時間段的所有 `Transaction`，並支援分頁
    *   **輸出**：渲染 `expense/history.html`
*   **GET `/expense/edit/<id>`**
    *   **輸入**：URL 參數 `id`
    *   **處理邏輯**：檢查紀錄是否屬於當前使用者，讀取資料傳給視圖
    *   **錯誤處理**：若不存在或權限不足則 404/403
    *   **輸出**：渲染 `expense/form.html` (帶入既有資料)
*   **POST `/expense/edit/<id>`**
    *   **處理邏輯**：計算與舊紀錄差額，還原並更新 `Account` 餘額，最終更新 `Transaction`
    *   **輸出**：重導回 `/expense/history`
*   **POST `/expense/delete/<id>`**
    *   **處理邏輯**：刪除前將原本扣除或增加的餘額還原至 `Account`，再刪除 `Transaction`
    *   **輸出**：重導回 `/expense/history`
*   **GET `/report`**
    *   **處理邏輯**：撈取特定區間的收支比例、分類支出總和等圖表所需資料
    *   **輸出**：渲染 `expense/report.html`
*   **GET `/account`**
    *   **處理邏輯**：列出使用者所有 `Account` 及目前餘額總額
    *   **輸出**：渲染 `expense/account.html`
*   **POST `/account/add` (及 GET)**
    *   **處理邏輯**：建立新的資金帳戶，初始金額等
    *   **輸出**：重導至 `/account`
*   **GET `/budget`**
    *   **處理邏輯**：讀取當月 `Budget`，比對當月各分類的 `Transaction`，計算超支狀況
    *   **輸出**：渲染 `expense/budget.html`
*   **POST `/budget/update`**
    *   **處理邏輯**：接收表單更改各分類的預算上限
    *   **輸出**：重導至 `/budget`

---

## 3. Jinja2 模板清單

所有版面均繼承自 `base.html`，以保持共同導覽列。

*   `templates/base.html`: 基礎外部模板 (導航、通用 CSS/JS)
*   `templates/auth/`
    *   `register.html`: 註冊頁面
    *   `login.html`: 登入頁面
*   `templates/expense/`
    *   `dashboard.html`: 儀表板頁面
    *   `form.html`: 共用於新增與編輯記帳項目的表單
    *   `history.html`: 歷史紀錄列表頁面
    *   `report.html`: 圖表分析頁面
    *   `account.html`: 資金帳戶清單頁面
    *   `account_form.html`: 新增資金帳戶頁面
    *   `budget.html`: 預算設定與顯示進度頁面
