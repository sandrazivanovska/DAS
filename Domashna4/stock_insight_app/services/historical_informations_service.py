from Domashna4.stock_insight_app.model.db_singleton import DatabaseConnection

def fetch_historical_data(stock_name, start_date, end_date):
    """
    Fetch historical data for a given stock from the database.
    """
    db = DatabaseConnection().connect()
    query = '''
        SELECT Датум, "Цена на последна трансакција", "Мак.", "Мин.", "Просечна цена", "%пром.", "Количина", "Промет во БЕСТ во денари", "Вкупен промет во денари"
        FROM stock_data
        WHERE Издавач = ? AND Датум BETWEEN ? AND ?
        ORDER BY Датум
    '''
    data = db.execute(query, (stock_name, start_date, end_date)).fetchall()

    if not data:
        return [], {}

    # Пример за обработка на податоци
    chart_data = {
        "dates": [row["Датум"] for row in data],
        "last_prices": [
            float(row["Цена на последна трансакција"].replace('.', '').replace(',', '.'))
            for row in data
        ],
        "max_prices": [
            float(row["Мак."].replace('.', '').replace(',', '.'))
            for row in data
        ],
        "min_prices": [
            float(row["Мин."].replace('.', '').replace(',', '.'))
            for row in data
        ],
    }

    return data, chart_data
