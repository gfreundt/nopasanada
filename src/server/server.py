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
from src.utils.utils import get_local_ip
from src.comms import send_code_message
from src.utils.constants import NETWORK_PATH


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
        self.app = Flask(
            __name__,
            template_folder=os.path.join(NETWORK_PATH, "templates"),
            static_folder=os.path.join(NETWORK_PATH, "static"),
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
            return redirect("mic")

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
                self.dash.logging(
                    usuario=f"Login {session['user']['CodMember']} | {session['user']['NombreCompleto']} | {session['user']['DocNum']} | {session['user']['Correo']}"
                )
                return redirect("mic")
            else:
                self.dash.logging(
                    usuario=f"Unsuccesful Login ({form_response['correo']} | {form_response['password']})"
                )

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
                print("-------- REG ---------->", session["codigo_generado"])
                send_code_message.send_code(
                    codigo=session["codigo_generado"],
                    correo=session["registration_attempt"]["correo"],
                    nombre=session["registration_attempt"]["nombre"],
                )

                self.dash.logging(
                    usuario=f"Nuevo Registro. Correo enviado. {form_response['correo']}."
                )

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

                # write new record in members table and create record in last update table
                self.db.cursor.execute(
                    f"INSERT INTO members VALUES ({rec},'{cod}','{nom}','DNI','{dni}','{cel}','{cor}',0,0,'{dat}',0,'{pwd}',0)"
                )
                # create blank record and add new member ID
                self.db.cursor.execute("INSERT INTO membersLastUpdate DEFAULT VALUES")
                self.db.cursor.execute(
                    f"UPDATE membersLastUpdate SET IdMember_FK = {rec} WHERE IdMember_FK IS NULL"
                )
                self.db.conn.commit()
                self.dash.logging(
                    usuario=f"Nuevo Registro Completo. {rec} | {cod} | {nom} | {dni} | {cel} | {cor} | {dat} | {pwd}"
                )

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
                print("-------- REC ---------->", session["codigo_generado"])
                self.db.cursor.execute(
                    f"SELECT NombreCompleto FROM members WHERE Correo = '{session["recovery_attempt"]["correo"]}'"
                )
                send_code_message.send_code(
                    codigo=session["codigo_generado"],
                    correo=session["recovery_attempt"]["correo"],
                    nombre=self.db.cursor.fetchone()["NombreCompleto"],
                )

                self.dash.logging(
                    usuario=f"Recuperacion. Correo enviado. {form_response["correo"]}."
                )

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
                self.dash.logging(usuario="Recuperacion ok.")

                # clear session data (back to login) and reload db to include new record
                session.clear()
                self.db.load_members()

                return render_template("rec-3.html")

            else:

                self.dash.logging(usuario="Recuperacion ERROR.")

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

        # extract user data
        self.db.cursor.execute(
            f"SELECT * FROM members WHERE IdMember = {session['user']['IdMember']}"
        )
        user = self.db.cursor.fetchone()
        self.db.cursor.execute(
            f"SELECT * FROM placas WHERE IdMember_FK = {session['user']['IdMember']}"
        )
        placas = [i["Placa"] for i in self.db.cursor.fetchall()]

        # get next message date
        self.db.cursor.execute(
            f"SELECT FechaEnvio FROM mensajes WHERE IdMember_FK = {session['user']['IdMember']} ORDER BY FechaEnvio DESC"
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

        # empty data for first time
        errors = {}

        if request.method == "GET":
            pass

        # validating form response
        elif request.method == "POST":
            form_response = dict(request.form)

            # check if there were changes to account
            errors = self.validacion.mic(form_response)
            changes_made = self.validacion.mic_changes(
                user=user, placas=placas, post=form_response
            )

            # update template data
            user = (
                session["user"]["IdMember"],
                form_response["codigo"],
                form_response["nombre"],
                session["user"]["DocTipo"],
                form_response["dni"],
                form_response["celular"],
                form_response["correo"],
            )
            placas = (
                form_response["placa1"],
                form_response["placa2"],
                form_response["placa3"],
            )

            # remove account - copy member to another table, erase from main one and unattach placa
            if "eliminar" in form_response:

                cmd = f""" INSERT INTO membersPast SELECT * FROM members WHERE IdMember = {session['user']['IdMember']};
                           DELETE FROM members WHERE IdMember = {session['user']['IdMember']};
                           UPDATE placas SET IdMember_FK = 0 WHERE IdMember_FK = {session['user']['IdMember']}
                        """
                self.db.cursor.executescript(cmd)

                self.dash.logging(
                    usuario=f"Eliminado {session['user']['CodMember']} | {session['user']['NombreCompleto']} | {session['user']['DocNum']} | {session['user']['Correo']}"
                )
                return redirect("logout")

            # no errors
            if not any(errors.values()):

                if not changes_made:
                    # no processing
                    flash("No se realizaron cambios. ", "warning")

                else:
                    # update member information
                    self.db.cursor.execute(
                        f"""    UPDATE members SET
                                NombreCompleto = '{form_response["nombre"]}',
                                DocNum = '{form_response["dni"]}',
                                Celular = '{form_response["celular"]}',
                                ForceMsg = '{1 if "Placas" in changes_made else 0}'
                                WHERE IdMember = {session['user']['IdMember']}"""
                    )

                    # update constraseña if changed
                    if "Contraseña" in changes_made:
                        self.db.cursor.execute(
                            f"""    UPDATE members SET Password = '{form_response["contra2"]}'
                                    WHERE IdMember = {session['user']['IdMember']}"""
                        )

                    _ph = "2020-01-01"  # default placeholder value for date of last scrape for new placas

                    # erase foreign key linking placa to member
                    self.db.cursor.execute(
                        f"UPDATE placas SET IdMember_FK = 0 WHERE IdMember_FK = {session['user']['IdMember']}"
                    )

                    # loop all non-empty placas and link foreign key to member if placa exists or create new placa record
                    for placa in [i for i in placas if i]:

                        self.db.cursor.execute(
                            f"SELECT * FROM placas WHERE Placa = '{placa.upper()}'"
                        )
                        if len(self.db.cursor.fetchall()) > 0:
                            # placa already exists in the database, assign foreign key to member
                            self.db.cursor.execute(
                                f"UPDATE placas SET IdMember_FK = {session['user']['IdMember']} WHERE Placa = '{placa}'"
                            )
                        else:
                            # create new record
                            self.db.cursor.execute(
                                "SELECT IdPlaca FROM placas ORDER BY IdPlaca DESC"
                            )
                            rec = int(self.db.cursor.fetchone()["IdPlaca"]) + 1
                            self.db.cursor.execute(
                                f"INSERT INTO placas VALUES ({rec}, {session['user']['IdMember']}, '{placa}', '{_ph}', '{_ph}', '{_ph}', '{_ph}', '{_ph}')"
                            )

                    self.db.conn.commit()
                    flash(changes_made, "success")
                    self.dash.logging(
                        usuario=f"Actualizado {session['user']['CodMember']} | {session['user']['NombreCompleto']} | {session['user']['DocNum']} | {session['user']['Correo']}"
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
        self.dash.logging(
            usuario=f"Logout {session['user']['CodMember']} | {session['user']['NombreCompleto']} | {session['user']['DocNum']} | {session['user']['Correo']}"
        )
        session.clear()
        return redirect("log")

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
