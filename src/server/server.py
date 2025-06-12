from flask import Flask, render_template, request, redirect, session, flash
from random import randrange
from string import ascii_uppercase
from datetime import datetime as dt
from datetime import timedelta as td
import uuid
import threading
import os

from src.server.validation import FormValidate
from src.server.data_extraction import UserData
from ..utils import revisar_symlinks


# TODO: fix last two to show correct format
# TODO: add soat image
# TODO: add vencimiento DNI
# TODO: cards for reportes
# TODO: send email code
# TODO: add header "under construction" to navbar

from pprint import pprint


class UI:

    def __init__(self, db, dash):

        self.db = db
        self.dash = dash
        self.validacion = FormValidate(db=self.db)
        self.users = UserData(db=self.db)

        # initialize Flask app
        BASE_PATH = os.path.abspath(os.curdir)
        self.app = Flask(
            __name__,
            template_folder=os.path.join(BASE_PATH, "templates"),
            static_folder=os.path.join(BASE_PATH, "static"),
        )
        self.app.config["SECRET_KEY"] = "sdlkfjsdlojf3r49tgf8"
        self.app.config["TEMPLATES_AUTO_RELOAD"] = True

        # Define routes
        self.app.add_url_rule("/", "root", self.root)
        self.app.add_url_rule("/log", "log", self.log, methods=["GET", "POST"])
        self.app.add_url_rule("/reg", "reg", self.reg, methods=["GET", "POST"])
        self.app.add_url_rule("/reg-2", "reg-2", self.reg2, methods=["GET", "POST"])
        self.app.add_url_rule("/rec", "rec", self.rec, methods=["GET", "POST"])
        self.app.add_url_rule("/rec-2", "rec-2", self.rec2, methods=["GET", "POST"])
        self.app.add_url_rule(
            "/reportes", "reportes", self.reportes, methods=["GET", "POST"]
        )
        self.app.add_url_rule("/mic", "mic", self.mic, methods=["GET", "POST"])
        self.app.add_url_rule("/logout", "logout", self.logout)

    # root endpoint
    def root(self):
        return redirect("log")

    # login endpoint
    def log(self):

        # if user already logged in, skip login
        if "user" in session:
            return redirect("reportes")

        # empty data for first time
        form_response = {}
        errors = {}

        # validating form response
        if request.method == "POST":
            form_response = dict(request.form)
            errors = self.validacion.log(form_response, db=self.db)
            if not errors:
                # gather user data header
                session["user"] = self.users.get_header(correo=form_response["correo"])
                self.dash.log(usuario=f"Login {session['user'][:4]}")
                return redirect("mic")
            else:
                self.dash.log(usuario=f"Unsuccesful Login")

        # render form for user to fill (first time or with errors)
        if "password" in form_response:
            form_response["password"] = ""
        return render_template("log.html", user=form_response, errors=errors)

    # registration endpoints
    def reg(self):

        # if user already logged in, skip registration
        if "user" in session:
            return redirect("reportes")

        # empty data for first time
        form_response = {}
        errors = {}

        # validating form response
        if request.method == "POST":
            form_response = dict(request.form)
            errors = self.validacion.reg(form_response, page=1)

            # no errors
            if not any(errors.values()):
                # keep data for second part of registration
                session["registration_attempt"] = form_response

                # generate validation code (TODO: replace with email)
                session["codigo_generado"] = "".join(
                    [
                        ascii_uppercase[randrange(0, len(ascii_uppercase))]
                        for _ in range(4)
                    ]
                )
                print("@@@@@", session["codigo_generado"])

                return redirect("reg-2")

        # render form for user to fill (first time or returned with errors)
        return render_template("reg.html", user=form_response, errors=errors)

    def reg2(self):

        if "registration_attempt" not in session:
            return redirect("reg")

        # empty data for first time
        form_response = {}
        errors = {}

        # validating form response
        if request.method == "POST":
            form_response = dict(request.form)
            errors = self.validacion.reg(
                form_response, codigo=session["codigo_generado"], page=2
            )

            # no errors
            if not any(errors.values()):

                # define all values to be included in database
                nom = session["registration_attempt"]["nombre"]
                cod = "NPN-" + str(uuid.uuid4())[-6:].upper()
                dni = session["registration_attempt"]["dni"]
                cel = session["registration_attempt"]["celular"]
                cor = session["registration_attempt"]["correo"]
                pwd = request.form["password1"]
                dat = dt.now().strftime("%Y-%m-%d %H:%M:%S")

                # get last record of table
                self.db.cursor.execute(
                    "SELECT IdMember FROM members ORDER BY IdMember DESC"
                )
                rec = int(self.db.cursor.fetchone()[0]) + 1
                ph = "2020-01-01"

                # write new record in members table and create record in last update table
                self.db.cursor.execute(
                    f"INSERT INTO members VALUES ({rec},'{cod}','{nom}','DNI','{dni}','{cel}','{cor}',0,0,'{dat}',0,'{pwd}')"
                )
                self.db.cursor.execute(
                    f"INSERT INTO membersLastUpdate VALUES ({rec},'{ph}','{ph}',{ph},'{ph}','{ph}','{ph}','{ph}')"
                )
                self.db.conn.commit()

                # clear session data (back to login) and reload db to include new record
                session.clear()
                self.db.load_members()

                # log in recently created user and success message
                session["user"] = self.users.get_header(correo=cor)
                return render_template("reg-3.html")

        # render form for user to fill (first time or returned with errors)
        if "password1" in form_response:
            form_response["password1"] = ""
            form_response["password2"] = ""
        return render_template("reg-2.html", user=form_response, errors=errors)

    # password recovery endpoints
    def rec(self):

        # empty data for first time
        form_response = {}
        errors = {}

        # validating form response
        if request.method == "POST":
            form_response = dict(request.form)
            errors = self.validacion.rec(form_response, page=1)

            # no errors
            if not any(errors.values()):
                # keep data for second part of recovery
                session["recovery_attempt"] = form_response

                # generate validation code
                session["codigo_generado"] = "".join(
                    [
                        ascii_uppercase[randrange(0, len(ascii_uppercase))]
                        for _ in range(4)
                    ]
                )
                print("@@@@@", session["codigo_generado"])

                return redirect("rec-2")

        # render form for user to fill (first time or returned with errors)
        return render_template("rec.html", user=form_response, errors=errors)

    def rec2(self):

        if "recovery_attempt" not in session:
            return redirect("rec")

        # empty data for first time
        form_response = {}
        errors = {}

        # validating form response
        if request.method == "POST":
            form_response = dict(request.form)
            errors = self.validacion.rec(
                form_response, codigo=session["codigo_generado"], page=2
            )

            # no errors
            if not any(errors.values()):

                # define all values to be included in database
                cor = session["recovery_attempt"]["correo"]
                pwd = request.form["password1"]
                self.db.cursor.execute(
                    f"UPDATE members SET Password = '{pwd}' WHERE Correo = '{cor}'"
                )
                self.db.conn.commit()

                # clear session data (back to login) and reload db to include new record
                session.clear()
                self.db.load_members()

                return render_template("rec-3.html")

        # render form for user to fill (first time or returned with errors)
        if "password1" in form_response:
            form_response["password1"] = ""
            form_response["password2"] = ""
        return render_template("rec-2.html", user=form_response, errors=errors)

    # dashboard endpoints
    def reportes(self):

        # user not logged in, go to login page
        if not session["user"]:
            return render_template("log.html")

        # if rendering page for first time, gather reports and no selection made
        if request.method == "GET":
            session["data"] = self.users.get_reports(user=session["user"])
            session["selection"] = ""

        # if report has been selected
        elif request.method == "POST":
            session["selection"] = request.form["selection"]

        data = session["data"]

        pprint(data)

        return render_template(
            "rep.html",
            data=data,
            user=data["user"],
            selection=session["selection"],
        )

    # mi cuenta endpoint (NAVBAR)
    def mic(self):

        # user not logged in, got to login page
        if "user" not in session:
            return redirect("log")

        # extract user placas
        self.db.cursor.execute(
            f"SELECT * FROM placas WHERE IdMember_FK = {session['user'][0]}"
        )
        placas = [i[2] for i in self.db.cursor.fetchall()]

        # empty data for first time
        form_response = {}
        errors = {}

        # validating form response
        if request.method == "POST":
            form_response = dict(request.form)

            # remove account
            if "eliminar" in form_response:

                # TODO: confirmation

                cmd = f"""  DELETE FROM members WHERE IdMember = {session['user'][0]};
                            DELETE FROM placas WHERE IdMember_FK = {session['user'][0]}"""

                self.db.cursor.executescript(cmd)

                return redirect("logout")

            # update account
            errors = self.validacion.mic(form_response)
            changes_made = self.validacion.mic_changes(
                user=session["user"], placas=placas, post=form_response
            )

            # no errors and changes made to any field
            if not any(errors.values()):

                if not changes_made:
                    # no processing
                    flash("No se realizaron cambios", "warning")

                else:

                    # update member information
                    self.db.cursor.execute(
                        f"""    UPDATE members SET NombreCompleto = '{form_response["nombre"]}',
                                DocNum = '{form_response["dni"]}', Celular = '{form_response["celular"]}'
                                WHERE IdMember = {session['user'][0]}"""
                    )

                    _ph = "2020-01-01"  # default placeholder value for date of last scrape

                    # erase foreign key linking placa to member
                    self.db.cursor.execute(
                        f"UPDATE placas SET IdMember_FK = 0 WHERE IdMember_FK = {session['user'][0]}"
                    )

                    _vps = [
                        i
                        for i in (
                            form_response["placa1"],
                            form_response["placa2"],
                            form_response["placa3"],
                        )
                        if i
                    ]

                    # loop all non-empty placas and link foreign key to member if placa exists or create new placa record
                    for placa in _vps:

                        self.db.cursor.execute(
                            f"SELECT * FROM placas WHERE Placa = '{placa}'"
                        )
                        if len(self.db.cursor.fetchall()) > 0:
                            # placa already exists in the database, assign foreign key to member
                            self.db.cursor.execute(
                                f"UPDATE placas SET IdMember_FK = {session['user'][0]} WHERE Placa = '{placa}'"
                            )
                        else:
                            # create new record
                            self.db.cursor.execute(
                                "SELECT IdPlaca FROM placas ORDER BY IdPlaca DESC"
                            )
                            rec = int(self.db.cursor.fetchone()[0]) + 1
                            self.db.cursor.execute(
                                f"INSERT INTO placas VALUES ({rec}, {session['user'][0]}, '{placa}', '{_ph}', '{_ph}', '{_ph}', '{_ph}', '{_ph}')"
                            )

                    self.db.conn.commit()
                    flash("Informacion actualizada correctamente", "success")

            return redirect("mic")

        # render form for user to edit (first time or returned with errors)

        self.db.cursor.execute(
            f"SELECT FechaEnvio FROM mensajes WHERE IdMember_FK = {session['user'][0]} ORDER BY FechaEnvio DESC"
        )
        _fecha = self.db.cursor.fetchone()
        siguiente_mensaje = (
            (
                max(
                    dt.strptime(_fecha[0], "%Y-%m-%d %H:%M:%S") + td(days=30),
                    dt.now() + td(days=1),
                ).strftime("%Y-%m-%d")
            )
            if _fecha
            else (dt.now() + td(days=1)).strftime("%Y-%m-%d %H:%M:%S")
        )
        comm = {
            "siguiente_mensaje": siguiente_mensaje,
        }

        if not form_response:
            user = session["user"]
        else:
            user = (
                session["user"][0],
                form_response["codigo"],
                form_response["nombre"],
                session["user"][3],
                form_response["dni"],
                form_response["celular"],
                form_response["correo"],
                session["user"][7],
                session["user"][8],
                session["user"][9],
            )

        return render_template(
            "mic.html",
            user=user,
            placas=placas,
            comm=comm,
            errors=errors,
        )

    # logout endpoint (NAVBAR)
    def logout(self):
        session.clear()
        return redirect("log")

    def run(self):
        self.app.run(debug=False, threaded=True, host="0.0.0.0", port=5000)

    def run_in_background(self):
        flask_thread = threading.Thread(target=self.run, daemon=True)
        flask_thread.start()
        return flask_thread
