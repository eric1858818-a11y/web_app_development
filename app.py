import os
from app import create_app
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

# 建立 Flask 應用程式實例
app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
