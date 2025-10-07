# logingest/src/database/connection.py
import os
from typing import Optional, Dict, Any, Generator
from contextlib import contextmanager
import psycopg2
from psycopg2.extras import DictCursor
from psycopg2 import OperationalError

class DatabaseConnection:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self._connection = None

    @property
    def connection(self):
        if self._connection is None or self._connection.closed:
            self._connection = self._create_connection()
        return self._connection

    def _create_connection(self):
        try:
            return psycopg2.connect(
                dbname=self.config['DB_NAME'],
                user=self.config['DB_USER'],
                password=self.config['DB_PASSWORD'],
                host=self.config.get('DB_HOST', 'localhost'),
                port=self.config.get('DB_PORT', 5432),
                connect_timeout=5
            )
        except OperationalError as e:
            raise ConnectionError(f"Failed to connect to database: {e}")

    @contextmanager
    def get_cursor(self) -> Generator[DictCursor, None, None]:
        conn = None
        cursor = None
        try:
            conn = self.connection
            cursor = conn.cursor(cursor_factory=DictCursor)
            yield cursor
            conn.commit()
        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if cursor:
                cursor.close()

    def close(self):
        if self._connection and not self._connection.closed:
            self._connection.close()