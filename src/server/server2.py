from flask import Flask, request, session
import threading
import os

# local imports
from src.server.validation import FormValidate
from src.utils.utils import get_local_ip
from src.utils.constants import NETWORK_PATH, DASHBOARD_URL
from src.server import settings
from src.server import dashboard, ui, redir


class Server:

    def __init__(self, db):

        self.db = db
        self.validacion = FormValidate(db=self.db)
        self.data_lock = threading.Lock()

        # initialize Flask app object, set configuration and define routes
        self.app = Flask(
            __name__,
            template_folder=os.path.join(NETWORK_PATH, "templates"),
            static_folder=os.path.join(NETWORK_PATH, "static"),
        )
        self.session = session

        # set app configurations
        settings.set_config(self)

        # define endpoints
        settings.set_routes(self)

        # dashboard start
        dashboard.set_initial_data(self)
        dashboard.update_kpis(self)

    # starting server
    def run(self):
        print(f" > DASHBOARD RUNNING ON: http://{get_local_ip()}:5000/{DASHBOARD_URL}")
        self.app.run(
            debug=False,
            threaded=True,
            port=5000,
            host="0.0.0.0",
        )

    def run_in_background(self):
        flask_thread = threading.Thread(target=self.run, daemon=True)
        flask_thread.start()
        return flask_thread

    # redirect endpoint
    def redir(self):
        self.all_params = request.args.to_dict()
        redir.get_oauth2_token(self)

    # root endpoint
    def root(self):
        return ui.root(self)

    # login endpoint
    def log(self):
        return ui.log(self)

    # registration endpoints
    def reg(self):
        return ui.reg(self)

    def reg2(self):
        return ui.reg2(self)

    # password recovery endpoints
    def rec(self):
        return ui.rec(self)

    def rec2(self):
        return ui.rec2(self)

    # dashboard endpoints
    def reportes(self):
        return ui.reportes(self)

    # mi cuenta endpoint (NAVBAR)
    def mic(self):
        return ui.mic(self)

    # logout endpoint (NAVBAR)
    def acerca(self):
        return ui.acerca(self)

    # logout endpoint (NAVBAR)
    def logout(self):
        return ui.logout(self)

    # dashboard endpoints
    def dash(self):
        return dashboard.dash(self)

    def get_data(self):
        return dashboard.get_data(self)

    def registros(self):
        return dashboard.registros(self)

    def launch_gather_comm(self):
        return dashboard.launch_gather_comm(self)

    def launch_gather_send(self):
        return dashboard.launch_gather_send(self)

    def launch_gather_only_send(self):
        return dashboard.launch_gather_only_send(self)

    # dashboard functions
    def logging(self, **kwargs):
        dashboard.logging(self, kwargs)
