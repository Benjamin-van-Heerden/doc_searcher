import sqlite3
from cfg import IO_CONFIG


class DBCursor:
    def __enter__(self) -> sqlite3.Cursor:
        self.conn = sqlite3.connect(IO_CONFIG.db_path)
        self.conn.row_factory = sqlite3.Row
        self.cur = self.conn.cursor()
        return self.cur

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.conn.commit()
        self.conn.close()
