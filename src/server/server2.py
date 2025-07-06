from flask import Flask, render_template, request, session
import threading
import os
import requests

# local imports
from src.server.validation import FormValidate
from src.server.data_extraction import UserData
from src.utils.utils import get_local_ip
from src.utils.constants import (
    NETWORK_PATH,
    ZOHO_MAIL_API_CLIENT_ID,
    ZOHO_MAIL_API_CLIENT_SECRET,
)
from src.server.settings import set_routes, set_config
from src.server import dashboard, ui


class Server:

    def __init__(self, db):

        self.db = db
        self.validacion = FormValidate(db=self.db)
        self.users = UserData(db=self.db)
        self.data_lock = threading.Lock()

        # initialize Flask app object, set configuration and define routes
        self.app = Flask(
            __name__,
            template_folder=os.path.join(NETWORK_PATH, "templates"),
            static_folder=os.path.join(NETWORK_PATH, "static"),
        )
        self.session = session
        set_config(self)
        set_routes(self)

        # dashboard start
        dashboard.set_initial_data(self)
        dashboard.update_kpis(self)

    def redir(self):
        """OAuth2 endpoint for Zoho Mail"""
        all_params = request.args.to_dict()
        print(
            f"Code: {all_params['code']}, Location: {all_params['location']}, Server: {all_params['accounts-server']}"
        )
        authorization_code = all_params["code"]
        client_id = ZOHO_MAIL_API_CLIENT_ID
        client_secret = ZOHO_MAIL_API_CLIENT_SECRET
        redirect_uri = "https://www.nopasanadape.com/redir"
        scope = "ZohoMail.accounts.READ"

        url = f"https://accounts.zoho.com/oauth/v2/token?code={authorization_code}&grant_type=authorization_code&client_id={client_id}&client_secret={client_secret}&redirect_uri={redirect_uri}&scope={scope}"

        response = requests.post(url)
        print("Status code:", response.status_code)
        print("Response body:", response.text)
        self.zoho_mail_token = response.text

        return render_template("redirect.html")

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
    def logout(self):
        return ui.logout(self)

    # dashboard endpoints
    def dash(self):
        return dashboard.dash(self)

    def get_data(self):
        return dashboard.get_data(self)

    def launch_gather_comm(self):
        return dashboard.launch_gather_comm(self)

    def launch_gather_send(self):
        return dashboard.launch_gather_send(self)

    def launch_gather_only_send(self):
        return dashboard.launch_gather_only_send(self)

    # dashboard functions
    def logging(self, **kwargs):
        dashboard.logging(self, kwargs)

    # starting server
    def run(self):
        print(f" > SERVER RUNNING ON: http://{get_local_ip()}:5000")
        self.app.run(
            debug=False,
            threaded=True,
            host="0.0.0.0",
            port=5000,
        )

    def run_in_background(self):
        flask_thread = threading.Thread(target=self.run, daemon=True)
        flask_thread.start()
        return flask_thread
