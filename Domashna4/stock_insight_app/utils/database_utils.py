import sqlite3
import os

def get_current_price_from_db(stock_name):
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../stock_data.db')
    conn = sqlite3.connect(db_path)
    try:
        query = '''
            SELECT "Цена на последна трансакција"
            FROM stock_data
            WHERE Издавач = ?
            ORDER BY Датум DESC
            LIMIT 1
        '''
        result = conn.execute(query, (stock_name,)).fetchone()
        if result:
            raw_price = result[0]
            try:
                normalized_price = float(raw_price.replace('.', '').replace(',', '.'))
                return normalized_price
            except ValueError:
                raise ValueError(f"Invalid price format in database: {raw_price}")
    finally:
        conn.close()
    return None
