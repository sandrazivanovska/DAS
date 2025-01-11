import sqlite3
import os
import threading

class DatabaseConnection:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super(DatabaseConnection, cls).__new__(cls)
                    cls._instance._connection = None
        return cls._instance

    def connect(self):
        if not self._connection:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            db_path = os.path.join(base_dir, '../stock_data.db')
            try:
                self._connection = sqlite3.connect(db_path, check_same_thread=False)
                self._connection.row_factory = sqlite3.Row
                return self._connection
            except sqlite3.Error as e:
                print(f"Database connection failed: {e}")
                raise
        return self._connection

    def close(self):
        if self._connection:
            self._connection.close()
            self._connection = None
