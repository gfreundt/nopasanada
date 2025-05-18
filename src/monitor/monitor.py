from flask import Flask, render_template, jsonify
import threading
from copy import deepcopy as copy
from pprint import pprint
import os
from datetime import datetime as dt


class Dashboard:
    def __init__(self, db):
        BASE_PATH = os.path.abspath(
            "d:/pythonCode/nopasanada"
        )  # os.path.abspath(os.curdir)
        self.app = Flask(
            __name__,
            template_folder=os.path.join(BASE_PATH, "templates"),
            static_folder=os.path.join(BASE_PATH, "static"),
        )
        self.data_lock = threading.Lock()
        self.db = db

        # Define routes
        self.app.add_url_rule("/", "dashboard", self.dashboard)
        self.app.add_url_rule("/data", "get_data", self.get_data)

        self.set_initial_data()

    def log(self, **kwargs):

        if "general_status" in kwargs:
            self.data["top_right"]["content"] = kwargs["general_status"][0]
            self.data["top_right"]["status"] = kwargs["general_status"][1]
        if "action" in kwargs:
            _ft = f"<b>{dt.now():%Y-%m-%d %H:%M:%S} ></b>{kwargs["action"]}"
            self.data["bottom_right"].append(_ft)
            if len(self.data["bottom_right"]) > 30:
                self.data["bottom_right"].pop(0)
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

    def dashboard(self):
        return render_template("dashboard.html", data=self.data)

    def get_data(self):
        with self.data_lock:
            return jsonify(self.data)

    def run(self):
        self.app.run(debug=False, threaded=True, host="0.0.0.0", port=7000)

    def run_in_background(self):
        flask_thread = threading.Thread(target=self.run, daemon=True)
        flask_thread.start()
        return flask_thread


if __name__ == "__main__":
    app_instance = Dashboard(db=None)
    app_instance.run()
