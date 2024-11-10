import sqlite3

db_path = 'stock_data.db'

def init_database():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS stock_data (
            Издавач TEXT,
            "Цена на последна трансакција" REAL,
            "Мак." REAL,
            "Мин." REAL,
            "Просечна цена" REAL,
            "%пром." REAL,
            "Количина" INTEGER,
            "Промет во БЕСТ во денари" REAL,
            "Вкупен промет во денари" REAL, 
            Датум TEXT,
            PRIMARY KEY (Издавач, Датум)
        )
    ''')
    conn.commit()
    conn.close()
