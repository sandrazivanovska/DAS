from datetime import datetime, timedelta
import sqlite3
from .abstract_filter import Filter

db_path = 'stock_data.db'

class DateCheckFilter(Filter):
    def process(self, data_list):
        return [self.check_last_date(issuer) for issuer in data_list]

    def check_last_date(self, issuer):
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Use "Датум" instead of "Date" in the query to match the database schema
        cursor.execute("SELECT MAX(Датум) FROM stock_data WHERE Издавач = ?", (issuer,))
        last_date = cursor.fetchone()[0]
        conn.close()

        if last_date:
            last_date = datetime.strptime(last_date, "%Y-%m-%d").date()
        else:
            last_date = datetime.today().date() - timedelta(days=3651)

        return (issuer, last_date)
