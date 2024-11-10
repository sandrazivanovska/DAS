import sqlite3
from init_database import init_database
from filters.issuer_filter import IssuerFilter
from filters.date_check_filter import DateCheckFilter
from filters.data_fetch_filter import DataFetchFilter
from utils.timer import start_timer, end_timer
import asyncio

db_path = 'stock_data.db'

def insert_data_to_database(data):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    for record in data:
        if len(record) != 10:
            print(f"Record with incorrect number of fields: {record}")
            continue

    cursor.executemany('''
        INSERT OR IGNORE INTO stock_data (
            Издавач, "Цена на последна трансакција", "Мак.", "Мин.", "Просечна цена", "%пром.", "Количина", "Промет во БЕСТ во денари", "Вкупен промет во денари", Датум
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', data)

    conn.commit()
    conn.close()

async def main():
    init_database()

    filters = [
        IssuerFilter(),
        DateCheckFilter(),
        DataFetchFilter()
    ]

    start_time = start_timer()

    data_list = []

    for filter_obj in filters:
        if isinstance(filter_obj, DataFetchFilter):
            data_list = await filter_obj.process(data_list)
        else:
            data_list = filter_obj.process(data_list)

    insert_data_to_database(data_list)

    execution_time = end_timer(start_time)
    print(f"Total execution time: {execution_time:.2f} seconds")

if __name__ == "__main__":
    asyncio.run(main())
