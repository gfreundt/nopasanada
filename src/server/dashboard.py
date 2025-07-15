from flask import redirect, render_template, jsonify, url_for
import requests
from datetime import datetime as dt
from copy import deepcopy as copy

# local imports
from src.nopasanada import nopasanada


# endpoints
def dash(self):
    return render_template("dashboard.html", data=self.data)


def get_data(self):
    with self.data_lock:
        return jsonify(self.data)


def registros(self):
    nopasanada(dash=None, db=self.db, cmds=["data"])
    return redirect(url_for("dashboard"))


def launch_gather_comm(self):
    nopasanada(self, self.db, cmds=["update-threads", "comms"])
    return redirect(url_for("dashboard"))


def launch_gather_send(self):
    nopasanada(self, self.db, cmds=["update-threads", "comms", "send"])
    return redirect(url_for("dashboard"))


def launch_gather_only_send(self):
    nopasanada(self, self.db, cmds=["send"])
    return redirect(url_for("dashboard"))


# functions
def logging(self, kwargs):

    if "general_status" in kwargs:
        self.data["top_right"]["content"] = kwargs["general_status"][0]
        self.data["top_right"]["status"] = kwargs["general_status"][1]
        # write to permanent log in database
        cmd = f"INSERT INTO log VALUES ('STATUS', '{kwargs["general_status"][0]}', '{dt.now():%Y-%m-%d %H:%M:%S}')"
        self.db.cursor.execute(cmd)
    if "action" in kwargs:
        _ft = f"<b>{dt.now():%Y-%m-%d %H:%M:%S} ></b>{kwargs["action"]}"
        self.data["bottom_right"].append(_ft)
        if len(self.data["bottom_right"]) > 15:
            self.data["bottom_right"].pop(0)
        # write to permanent log in database
        cmd = f"INSERT INTO log VALUES ('SISTEMA', '{kwargs["action"]}', '{dt.now():%Y-%m-%d %H:%M:%S}')"
        self.db.cursor.execute(cmd)
    if "card" in kwargs:
        for field in kwargs:
            if field == "card":
                continue
            self.data["cards"][kwargs["card"]][field] = kwargs[field]
    if "usuario" in kwargs:
        _ft = f"<b>{dt.now():%Y-%m-%d %H:%M:%S} ></b>{kwargs["usuario"]}"
        self.data["bottom_left"].append(_ft)
        if len(self.data["bottom_left"]) > 30:
            self.data["bottom_left"].pop(0)
        # write to permanent log in database
        print(
            f"INSERT INTO log VALUES ('USUARIO', '{kwargs["usuario"]}', '{dt.now():%Y-%m-%d %H:%M:%S}')"
        )
        cmd = f"INSERT INTO log VALUES ('USUARIO', '{kwargs["usuario"]}', '{dt.now():%Y-%m-%d %H:%M:%S}')"
        self.db.cursor.execute(cmd)
        self.db.conn.commit()

    # any time there is an action, update kpis
    update_kpis(self)


def set_initial_data(self):
    empty_card = {
        "title": "No Asignado",
        "progress": 0,
        "msg": [],
        "status": 0,
        "text": "Inactivo",
        "lastUpdate": "Pendiente",
    }
    self.data = {
        "top_left": "No Pasa Nada Dashboard",
        "top_right": {"content": "Inicializando...", "status": 0},
        "cards": [copy(empty_card) for _ in range(12)],
        "bottom_left": [],
        "bottom_right": [],
    }


# def update_remaining_time(self):
#     delta = schedule.next_run("update") - dt.now()
#     hours, remainder = divmod(int(delta.total_seconds()), 3600)
#     minutes, seconds = divmod(remainder, 60)
#     self.log(general_status=(f"- {hours:02} : {minutes:02} : {seconds:02}", 1))


def update_kpis(self):
    # get number of users
    self.db.cursor.execute("SELECT COUNT( ) FROM members")
    self.data.update({"kpi_members": self.db.cursor.fetchone()[0]})

    # get number of placas
    self.db.cursor.execute("SELECT COUNT( ) FROM placas")
    self.data.update({"kpi_placas": self.db.cursor.fetchone()[0]})

    # get balance left in truecaptcha
    try:
        url = r"https://api.apiTruecaptcha.org/one/hello?method=get_all_user_data&userid=gabfre%40gmail.com&apikey=UEJgzM79VWFZh6MpOJgh"
        r = requests.get(url)
        self.data.update(
            {"kpi_truecaptcha_balance": r.json()["data"]["get_user_info"][4]["value"]}
        )
    except ConnectionError:
        self.data.update({"truecaptcha_balance": "N/A"})
