import sqlite3
import pandas as pd
import os

import sqlite3
import pandas as pd
import os


def fetch_data(stock_symbol, start_date, end_date):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(base_dir, '../../..', 'stock_data.db')
    conn = sqlite3.connect(db_path)

    query = '''
    SELECT Датум, "Цена на последна трансакција", "Мак.", "Мин.", Количина
    FROM stock_data
    WHERE Издавач = ? AND Датум BETWEEN ? AND ?
    ORDER BY Датум ASC
    '''

    df = pd.read_sql_query(query, conn, params=(stock_symbol, start_date, end_date))
    conn.close()

    df['Датум'] = pd.to_datetime(df['Датум'])
    df.set_index('Датум', inplace=True)

    for col in ['Цена на последна трансакција', 'Мак.', 'Мин.']:
        df[col] = df[col].str.replace('.', '', regex=False).str.replace(',', '.', regex=False).astype(float)

    return df.sort_index()

