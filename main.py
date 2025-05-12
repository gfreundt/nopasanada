import sqlite3
import os
from src.nopasanada import main


class Database:

    def __init__(self, dev):
        self.start(dev=dev)
        self.load_members()

    def start(self, dev=True):
        """Connect to database. Use development database by default."""

        # production
        SQLDATABASE = os.path.join("data", "members.db")
        if dev:
            # development
            SQLDATABASE = os.path.join("data", "dev", "members.db")
            # SQLDATABASE = os.path.join(r"\\192.168.68.105", "Downloads", "members.db")

        self.conn = sqlite3.connect(SQLDATABASE, check_same_thread=False)
        self.cursor = self.conn.cursor()

    def load_members(self):
        self.cursor.execute("SELECT * FROM members")
        self.users = self.cursor.fetchall()


if __name__ == "__main__":
    db = Database(dev=True)
    main(db)
