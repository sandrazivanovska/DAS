import os
from flask import Flask, jsonify, request
from filters.issuer_filter import IssuerFilter
from filters.date_check_filter import DateCheckFilter
from filters.data_fetch_filter import DataFetchFilter
import sqlite3

app = Flask(__name__)

DB_PATH = os.path.join(os.path.dirname(__file__), '../stock_data.db')


def insert_data_to_database(data):

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    for record in data:
        if len(record) != 10:
            print(f"Record with incorrect number of fields: {record}")
            continue

    cursor.executemany('''
        INSERT OR IGNORE INTO stock_data (
            Издавач, "Цена на последна трансакција", "Мак.", "Мин.", "Просечна цена", "%пром.", "Количина",
            "Промет во БЕСТ во денари", "Вкупен промет во денари", Датум
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', data)

    conn.commit()
    conn.close()


@app.route('/scrape', methods=['POST'])
async def scrape():

    try:
        filters = [
            IssuerFilter(),
            DateCheckFilter(),
            DataFetchFilter()
        ]

        data_list = []

        for filter_obj in filters:
            if isinstance(filter_obj, DataFetchFilter):
                data_list = await filter_obj.process(data_list)
            else:
                data_list = filter_obj.process(data_list)

        insert_data_to_database(data_list)

        return jsonify({"status": "success", "message": "Data scraped and stored successfully!"})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/issuers', methods=['GET'])
def get_issuers():

    try:
        issuers = IssuerFilter().get_issuers()
        return jsonify({"status": "success", "data": issuers})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5010, debug=True)

