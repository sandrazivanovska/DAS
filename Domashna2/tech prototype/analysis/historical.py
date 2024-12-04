# analysis/historical.py

from datetime import datetime

def get_historical_data(conn, stock_name, start_date, end_date):
    data = conn.execute('''
        SELECT Датум, "Цена на последна трансакција", "Мак.", "Мин.", "Просечна цена", "%пром.", "Количина", "Промет во БЕСТ во денари", "Вкупен промет во денари"
        FROM stock_data
        WHERE Издавач = ? AND Датум BETWEEN ? AND ?
        ORDER BY Датум
    ''', (stock_name, start_date, end_date)).fetchall()

    return data
