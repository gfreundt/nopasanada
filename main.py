import time
import sqlite3
import sys
import logging
import schedule
import atexit

# local imports
from src.nopasanada import nopasanada
from src.server import server
from src.monitor import monitor
from src.utils.constants import DB_LOCAL_PATH, DB_NETWORK_PATH


# reduce Flask output to command line
logging.getLogger("werkzeug").disabled = True


class Database:

    def __init__(self, dev):
        self.start(dev=dev)
        self.load_members()

    def start(self, dev=True):
        """Connect to database. Network database preferred. Fallback is local database."""

        # attempt tp connect to network production database, default to local if not possible
        try:
            self.conn = sqlite3.connect(DB_NETWORK_PATH, check_same_thread=False)
            print("Network Database Connected")
        except sqlite3.Error:
            if dev:
                self.conn = sqlite3.connect(DB_LOCAL_PATH, check_same_thread=False)
                print("LOCAL Database Connected")
            else:
                raise "Cannot Connect to Network DB"

        # set query responses to sqlite row object
        self.conn.row_factory = sqlite3.Row

        # create cursor object
        self.cursor = self.conn.cursor()

    def load_members(self):
        self.cursor.execute("SELECT * FROM members")
        self.users = self.cursor.fetchall()


def run_at_exit(dash, db):
    print("Running on Empty")
    # ensure dashboard shows disconnected when code ends
    dash.logging(general_status=("Desconectado", 3))
    time.sleep(3)
    # close db connection
    db.conn.close()


def main():

    # connect to database
    db = Database(dev=False)

    # print update data and end
    if "DATA" in sys.argv:
        nopasanada(dash=None, db=db, cmds=[])
        return

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

    if "PLUS" in sys.argv:
        nopasanada(dash, db, cmds=["update-threads", "comms"])

    if "SEND" in sys.argv:
        nopasanada(dash, db, cmds=["update", "comms", "send"])

    while True:
        # print([logging.getLogger(name) for name in logging.root.manager.loggerDict])
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
