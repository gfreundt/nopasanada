from datetime import datetime as dt
from datetime import timedelta as td
import time
import sqlite3
import os
import sys
from src.nopasanada import nopasanada
from src.server import server
from src.monitor import monitor

import time
import logging

logging.getLogger("werkzeug").disabled = True


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


class Scheduler:

    def __init__(self, interval):
        self.INTERVAL = interval
        self.last_run_time = dt.now() - td(days=10)

    def format_timedelta(self, delta):
        hours, remainder = divmod(delta.total_seconds(), 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"

    def seconds_to_next_run(self):
        _nr = self.last_run_time + td(minutes=self.INTERVAL) - dt.now()
        return _nr.total_seconds()


if __name__ == "__main__":

    # connect to database
    db = Database(dev=False)

    # run dashboard in background (port 7000)
    dash = monitor.Dashboard(db)
    if "NOMON" not in sys.argv:
        dash.run_in_background()

    # run user UI in background (port 5000)
    ui = server.UI(db=db, dash=dash)
    if "NOUI" not in sys.argv:
        ui.run_in_background()

    # set up scheduler with 240 minute intervals (4 hours)
    schedule = Scheduler(interval=1)

    while True:
        nr = schedule.seconds_to_next_run()
        dash.log(general_status=(f"- {schedule.format_timedelta(td(seconds=nr))}", 1))

        if nr < 0:
            if "NOMAIN" not in sys.argv:
                print(f"**********Activate {dt.now()} ")
                nopasanada(db=db, dash=dash)
                schedule.last_run_time = dt.now()
        time.sleep(0.9)
