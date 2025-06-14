import time
import sqlite3
import os
import sys
import logging
import schedule
import atexit

# local imports
from src.nopasanada import nopasanada
from src.server import server
from src.monitor import monitor

# reduce Flask output to command line
logging.getLogger("werkzeug").disabled = True


class Environment:

    def __init__(self):
        self.email_password = os.environ("ZOHO-1-PWD")


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


def run_at_exit(dash, db):
    # ensure dashboard shows disconnected when code ends
    dash.log(general_status=("Desconectado", 3))
    time.sleep(3)
    # close db connection
    db.conn.close()


def main():

    # start environment information
    # env = Environment()

    # connect to database
    db = Database(dev=False)

    # run dashboard in background (port 7000)
    dash = monitor.Dashboard(db)
    if "NOMON" not in sys.argv:
        dash.run_in_background()

    # code to run after exiting program
    atexit.register(run_at_exit, dash, db)

    # run user UI in background (port 5000)
    ui = server.UI(db=db, dash=dash)
    if "NOUI" not in sys.argv:
        ui.run_in_background()

    if "NOW" in sys.argv:
        nopasanada(dash, db, cmds=["update", "comms"])

    if "SEND" in sys.argv:
        nopasanada(dash, db, cmds=["update", "comms", "send"])

    while True:
        time.sleep(10)

    return

    # set up scheduler: dashboard updates
    schedule.every().second.do(dash.update_remaining_time, dash)
    schedule.every(15).minutes.do(dash.update_db_stats, dash, db)

    # set up scheduler: three updates (no messages/alerts) + one update (and messages/alerts)
    _update = "update-threads" if "THREAD" in sys.argv else "update"
    schedule.every().day.at("18:15").do(
        nopasanada, dash=dash, db=db, cmds=[_update, "comms"]
    ).tag("update")

    # run stats update for dashboard before scheduling begins
    dash.update_db_stats(dash, db)

    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == "__main__":
    main()
    time.sleep(1800)
