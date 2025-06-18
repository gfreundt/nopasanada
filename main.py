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


class Context:

    def __init__(self):
        self.email_password = os.environ["ZOHO-1-PWD"]
        self.test = False


class Database:

    def __init__(self, dev):
        self.start(dev=dev)
        self.load_members()

    def start(self, dev=True):
        """Connect to database. Network database preferred. Fallback is local database."""

        SQLDB_LOCAL = os.path.join("data", "members.db")
        SQLDB_NETWORK = os.path.join(
            r"\\192.168.68.110\d\pythonCode\nopasanada\data\members.db"
        )

        # attempt tp connect to network production database, default to local if not possible
        try:
            self.conn = sqlite3.connect(SQLDB_NETWORK, check_same_thread=False)
            print("Network Database Connected")
        except sqlite3.Error:
            self.conn = sqlite3.connect(SQLDB_LOCAL, check_same_thread=False)
            print("LOCAL Database Connected")

        # create cursor object
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
    context = Context()

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
