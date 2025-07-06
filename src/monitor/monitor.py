from flask import Flask, render_template, jsonify, redirect, request
import threading
from copy import deepcopy as copy
import os
from datetime import datetime as dt
import requests
import schedule
from src.utils.utils import get_local_ip
from src.nopasanada import nopasanada
from src.utils.constants import NETWORK_PATH


class Dashboard:
    def __init__(self, db):
        self.app = Flask(
            __name__,
            template_folder=os.path.join(NETWORK_PATH, "templates"),
            static_folder=os.path.join(NETWORK_PATH, "static"),
        )
        self.data_lock = threading.Lock()
        self.db = db

        # Define routes
        self.app.add_url_rule("/", "dashboard", self.dashboard)
        self.app.add_url_rule("/data", "get_data", self.get_data)
        self.app.add_url_rule(
            "/crear_mensajes",
            endpoint="crear_mensajes",
            view_func=self.launch_gather_comm,
            methods=["POST"],
        )
        self.app.add_url_rule(
            "/enviar_mensajes",
            endpoint="enviar_mensajes",
            view_func=self.launch_gather_send,
            methods=["POST"],
        )
        self.app.add_url_rule(
            "/solo_enviar_mensajes",
            endpoint="solo_enviar_mensajes",
            view_func=self.launch_gather_only_send,
            methods=["POST"],
        )
        self.app.add_url_rule(
            "/redirect",
            endpoint="redirect",
            view_func=self.redirect,
            methods=["POST", "GET"],
        )

        self.set_initial_data()
        self.update_kpis()

    def logging(self, **kwargs):

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

        # any time there is an action, update kpis
        self.update_kpis()

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

    def update_remaining_time(self):
        delta = schedule.next_run("update") - dt.now()
        hours, remainder = divmod(int(delta.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        self.log(general_status=(f"- {hours:02} : {minutes:02} : {seconds:02}", 1))

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
                {
                    "kpi_truecaptcha_balance": r.json()["data"]["get_user_info"][4][
                        "value"
                    ]
                }
            )
        except ConnectionError:
            self.data.update({"truecaptcha_balance": "N/A"})

    def get_data(self):
        with self.data_lock:
            return jsonify(self.data)

    def launch_gather_comm(self):
        nopasanada(self, self.db, cmds=["update-threads", "comms"])
        return redirect("/")

    def launch_gather_send(self):
        nopasanada(self, self.db, cmds=["update-threads", "comms", "send"])
        return redirect("/")

    def launch_gather_only_send(self):
        nopasanada(self, self.db, cmds=["send"])
        return redirect("/")

    def redirect(self):
        """OAuth for Zoho Mail"""
        all_params = request.args.to_dict()
        print(
            f"Code: {all_params['code']}, Location: {all_params['location']}, Server: {all_params['accounts-server']}"
        )
        authorization_code = all_params["code"]
        client_id = "1000.400ELE5I2WU72H931RQI8HTIY2Y30E"
        client_secret = "fe41ea63cc1c667091b32b1068660cf0b44fffd823"
        redirect_uri = "https://www.nopasanadape.com"
        scope = "ZohoMail.accounts.READ"

        url = f"https://accounts.zoho.com/oauth/v2/token?code={authorization_code}&grant_type=authorization_code&client_id={client_id}&client_secret={client_secret}&redirect_uri={redirect_uri}&scope={scope}"

        response = requests.post(url)
        print("Status code:", response.status_code)
        print("Response body:", response.text)

        return render_template("redirect.html")

    def dashboard(self):
        return render_template("dashboard.html", data=self.data)

    def run(self):
        print(f"MONITOR RUNNING ON: http://{get_local_ip()}:7000")
        self.app.run(debug=False, threaded=True, host="0.0.0.0", port=7000)

    def run_in_background(self):
        flask_thread = threading.Thread(target=self.run, daemon=True)
        flask_thread.start()
        return flask_thread


if __name__ == "__main__":
    app_instance = Dashboard(db=None)
    app_instance.run()
