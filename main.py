import sqlite3
import os, sys
from src.nopasanada import main
from src.server import server
from src.monitor import monitor

import time


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

    # connect to database
    db = Database(dev=False)

    # run dashboard in background (port 7000)
    dash = monitor.Dashboard(db)
    if not "NOMON" in sys.argv:
        dash.run_in_background()

    # run user UI in background (port 5000)
    ui = server.UI(db=db, dash=dash)
    if not "NOUI" in sys.argv:
        ui.run_in_background()

    # run main code in foreground
    if not "NOMAIN" in sys.argv:
        main(db=db, dash=dash)

    quit()

    while True:
        print("<----- Looping ------->")
        time.sleep(20)
