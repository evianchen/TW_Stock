import mysql.connector

# 資料庫設定
db_settings = {
    'host': '127.0.0.1',  # 主機名稱
    'port': 3306,
    'user': 'root',  # 帳號
    'password': 'eddie970319',  # 密碼
    'database': 'tw_stock'
}

connection = mysql.connector.connect(**db_settings)
cursor = connection.cursor()
