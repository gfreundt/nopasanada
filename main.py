from datetime import datetime as dt
import time
import sqlite3
import os
import sys
import logging
import schedule
import requests

# local imports
from src.nopasanada import nopasanada
from src.server import server
from src.monitor import monitor

# reduce Flask output to command line
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


def update_remaining_time(dash):
    delta = schedule.next_run("update") - dt.now()
    hours, remainder = divmod(int(delta.total_seconds()), 3600)
    minutes, seconds = divmod(remainder, 60)
    dash.log(general_status=(f"- {hours:02} : {minutes:02} : {seconds:02}", 1))


def update_db_stats(dash, db):
    # get number of users
    db.cursor.execute("SELECT COUNT( ) FROM members")
    response = {"users": db.cursor.fetchone()[0]}

    # get number of placas
    db.cursor.execute("SELECT COUNT( ) FROM placas")
    response.update({"placas": db.cursor.fetchone()[0]})

    # get balance left in truecaptcha
    try:
        url = r"https://api.apiTruecaptcha.org/one/hello?method=get_all_user_data&userid=gabfre%40gmail.com&apikey=UEJgzM79VWFZh6MpOJgh"
        r = requests.get(url)
        response.update(
            {"truecaptcha_balance": r.json()["data"]["get_user_info"][4]["value"]}
        )
    except ConnectionError:
        response.update({"truecaptcha_balance": "N/A"})

    # update dashboard
    dash.log(kpis=response)


def main():

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

    if "NOW" in sys.argv:
        nopasanada(dash, db, cmds=["update", "comms"])

    if "SEND" in sys.argv:
        nopasanada(dash, db, cmds=["update", "comms", "send"])
        return

    # set up scheduler: dashboard updates
    schedule.every().second.do(update_remaining_time, dash)
    schedule.every(15).minutes.do(update_db_stats, dash, db)

    # set up scheduler: three updates (no messages/alerts) + one update (and messages/alerts)
    _update = "update-threads" if "THREAD" in sys.argv else "update"
    schedule.every().day.at("18:15").do(
        nopasanada, dash=dash, db=db, cmds=[_update, "comms"]
    ).tag("update")

    # run stats update for dashboard before scheduling begins
    update_db_stats(dash, db)

    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == "__main__":
    main()
