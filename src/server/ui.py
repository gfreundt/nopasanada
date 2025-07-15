from datetime import datetime as dt
from datetime import timedelta as td
import uuid
from random import randrange
from string import ascii_uppercase
from flask import redirect, render_template, request, flash

from src.comms import send_code_message


def acerca(self):
    return render_template("acerca.html")


def logout(self):
    if self.session.get("user"):
        self.logging(
            usuario=f"Logout {self.session['user']['CodMember']} | {self.session['user']['NombreCompleto']} | {self.session['user']['DocNum']} | {self.session['user']['Correo']}"
        )
        self.session.clear()
    return redirect("log")


# root endpoint
def root(self):
    return redirect("log")


# login endpoint
def log(self):

    # if user already logged in, skip login
    if "user" in self.session:
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
            self.session["user"] = load_member(
                db=self.db, correo=form_response["correo"].lower()
            )
            # update last login information
            self.db.cursor.executescript(
                f"""    UPDATE members SET LastLoginDatetime = '{dt.now().strftime("%Y-%m-%d %H:%M:%S")}' WHERE Correo = '{self.session['user']['Correo']}';
                        UPDATE members SET CountFailedLogins = 0 WHERE Correo = '{self.session['user']['Correo']}'
                 """
            )
            # log activity
            self.logging(
                usuario=f"Login {self.session['user']['CodMember']} | {self.session['user']['NombreCompleto']} | {self.session['user']['DocNum']} | {self.session['user']['Correo']}"
            )
            return redirect("mic")
        else:
            # add one to failed login counter
            self.db.cursor.execute(
                f"UPDATE members SET CountFailedLogins = CountFailedLogins + 1 WHERE Correo = '{form_response['correo']}'"
            )
            # log activity
            self.logging(
                usuario=f"Unsuccesful Login ({form_response['correo']} | {form_response['password']})"
            )

    # render form for user to fill (first time or with errors)
    if "password" in form_response:
        form_response["password"] = ""
    return render_template("log.html", user=form_response, errors=errors)


# registration endpoints
def reg(self):

    # if user already logged in, skip registration
    if "user" in self.session:
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
            self.session["registration_attempt"] = form_response

            # generate validation code (TODO: replace with email)
            self.session["codigo_generado"] = "".join(
                [ascii_uppercase[randrange(0, len(ascii_uppercase))] for _ in range(4)]
            )
            print("-------- REG ---------->", self.session["codigo_generado"])
            send_code_message.send_code(
                codigo=self.session["codigo_generado"],
                correo=self.session["registration_attempt"]["correo"],
                nombre=self.session["registration_attempt"]["nombre"],
            )

            self.logging(
                usuario=f"Nuevo Registro. Correo enviado. {form_response['correo']}."
            )

            return redirect("reg-2")

    # render form for user to fill (first time or returned with errors)
    return render_template("reg.html", user=form_response, errors=errors)


def reg2(self):

    if "registration_attempt" not in self.session:
        return redirect("reg")

    # empty data for first time
    form_response = {}
    errors = {}

    # validating form response
    if request.method == "POST":
        form_response = dict(request.form)
        errors = self.validacion.reg(
            form_response, codigo=self.session["codigo_generado"], page=2
        )

        # no errors
        if not any(errors.values()):

            # define all values to be included in database
            nom = self.session["registration_attempt"]["nombre"]
            cod = "NPN-" + str(uuid.uuid4())[-6:].upper()
            dni = self.session["registration_attempt"]["dni"]
            cel = self.session["registration_attempt"]["celular"]
            cor = self.session["registration_attempt"]["correo"]
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
            self.logging(
                usuario=f"Nuevo Registro Completo. {rec} | {cod} | {nom} | {dni} | {cel} | {cor} | {dat} | {pwd}"
            )

            # clear self.session data (back to login) and reload db to include new record
            self.session.clear()
            self.db.load_members()

            # log in recently created user and success message
            self.session["user"] = load_member(db=self.db, correo=cor)
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
            self.session["recovery_attempt"] = form_response

            # generate validation code
            self.session["codigo_generado"] = "".join(
                [ascii_uppercase[randrange(0, len(ascii_uppercase))] for _ in range(4)]
            )
            print("-------- REC ---------->", self.session["codigo_generado"])
            self.db.cursor.execute(
                f"SELECT NombreCompleto FROM members WHERE Correo = '{self.session["recovery_attempt"]["correo"]}'"
            )
            send_code_message.send_code(
                codigo=self.session["codigo_generado"],
                correo=self.session["recovery_attempt"]["correo"],
                nombre=self.db.cursor.fetchone()["NombreCompleto"],
            )

            self.logging(
                usuario=f"Recuperacion. Correo enviado. {form_response["correo"]}."
            )

            return redirect("rec-2")

    # render form for user to fill (first time or returned with errors)
    return render_template("rec.html", user=form_response, errors=errors)


def rec2(self):

    if "recovery_attempt" not in self.session:
        return redirect("rec")

    # empty data for first time
    form_response = {}
    errors = {}

    # validating form response
    if request.method == "POST":
        form_response = dict(request.form)
        errors = self.validacion.rec(
            form_response, codigo=self.session["codigo_generado"], page=2
        )

        # no errors
        if not any(errors.values()):

            # define all values to be included in database
            cor = self.session["recovery_attempt"]["correo"]
            pwd = request.form["password1"]
            self.db.cursor.execute(
                f"UPDATE members SET Password = '{pwd}' WHERE Correo = '{cor}'"
            )
            self.db.conn.commit()
            self.logging(usuario="Recuperacion ok.")

            # clear self.session data (back to login) and reload db to include new record
            self.session.clear()
            self.db.load_members()

            return render_template("rec-3.html")

        else:

            self.logging(usuario="Recuperacion ERROR.")

    # render form for user to fill (first time or returned with errors)
    if "password1" in form_response:
        form_response["password1"] = ""
        form_response["password2"] = ""
    return render_template("rec-2.html", user=form_response, errors=errors)


# dashboard endpoints
def reportes(self):

    # user not logged in, go to login page
    if not self.session["user"]:
        return render_template("log.html")

    # if rendering page for first time, gather reports and no selection made
    if request.method == "GET":
        self.session["data"] = self.users.get_reports(user=self.session["user"])
        self.session["selection"] = ""

    # if report has been selected
    elif request.method == "POST":
        self.session["selection"] = request.form["selection"]

    data = self.session["data"]

    return render_template(
        "rep.html",
        data=data,
        user=data["user"],
        selection=self.session["selection"],
    )


# mi cuenta endpoint (NAVBAR)
def mic(self):

    # user not logged in, got to login page
    if "user" not in self.session:
        return redirect("log")

    # extract user data
    self.db.cursor.execute(
        f"SELECT * FROM members WHERE IdMember = {self.session['user']['IdMember']}"
    )
    user = self.db.cursor.fetchone()
    self.db.cursor.execute(
        f"SELECT * FROM placas WHERE IdMember_FK = {self.session['user']['IdMember']}"
    )
    placas = [i["Placa"] for i in self.db.cursor.fetchall()]

    # get next message date
    self.db.cursor.execute(
        f"SELECT FechaEnvio FROM mensajes WHERE IdMember_FK = {self.session['user']['IdMember']} ORDER BY FechaEnvio DESC"
    )
    _fecha = self.db.cursor.fetchone()
    _siguiente_mensaje = (
        (
            max(
                dt.strptime(_fecha[0], "%Y-%m-%d %H:%M:%S") + td(days=30),
                dt.now() + td(days=1),
            ).strftime("%Y-%m-%d")
        )
        if _fecha
        else (dt.now() + td(days=1)).strftime("%Y-%m-%d %H:%M:%S")
    )

    _dias_faltantes = (
        dt.strptime(_fecha[0], "%Y-%m-%d %H:%M:%S") - dt.now() + td(days=30)
    ).days
    sgte_boletin = {"fecha": _siguiente_mensaje, "dias": _dias_faltantes}

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
            self.session["user"]["IdMember"],
            form_response["codigo"],
            form_response["nombre"],
            self.session["user"]["DocTipo"],
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

            cmd = f""" INSERT INTO membersPast SELECT * FROM members WHERE IdMember = {self.session['user']['IdMember']};
                        DELETE FROM members WHERE IdMember = {self.session['user']['IdMember']};
                        UPDATE placas SET IdMember_FK = 0 WHERE IdMember_FK = {self.session['user']['IdMember']}
                    """
            self.db.cursor.executescript(cmd)

            self.logging(
                usuario=f"Eliminado {self.session['user']['CodMember']} | {self.session['user']['NombreCompleto']} | {self.session['user']['DocNum']} | {self.session['user']['Correo']}"
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
                            WHERE IdMember = {self.session['user']['IdMember']}"""
                )

                # update constraseña if changed
                if "Contraseña" in changes_made:
                    self.db.cursor.execute(
                        f"""    UPDATE members SET Password = '{form_response["contra2"]}'
                                WHERE IdMember = {self.session['user']['IdMember']}"""
                    )

                _ph = "2020-01-01"  # default placeholder value for date of last scrape for new placas

                # erase foreign key linking placa to member
                self.db.cursor.execute(
                    f"UPDATE placas SET IdMember_FK = 0 WHERE IdMember_FK = {self.session['user']['IdMember']}"
                )

                # loop all non-empty placas and link foreign key to member if placa exists or create new placa record
                for placa in [i for i in placas if i]:

                    self.db.cursor.execute(
                        f"SELECT * FROM placas WHERE Placa = '{placa.upper()}'"
                    )
                    if len(self.db.cursor.fetchall()) > 0:
                        # placa already exists in the database, assign foreign key to member
                        self.db.cursor.execute(
                            f"UPDATE placas SET IdMember_FK = {self.session['user']['IdMember']} WHERE Placa = '{placa}'"
                        )
                    else:
                        # create new record
                        self.db.cursor.execute(
                            "SELECT IdPlaca FROM placas ORDER BY IdPlaca DESC"
                        )
                        rec = int(self.db.cursor.fetchone()["IdPlaca"]) + 1
                        self.db.cursor.execute(
                            f"INSERT INTO placas VALUES ({rec}, {self.session['user']['IdMember']}, '{placa}', '{_ph}', '{_ph}', '{_ph}', '{_ph}', '{_ph}')"
                        )

                self.db.conn.commit()
                flash(changes_made, "success")
                self.logging(
                    usuario=f"Actualizado {self.session['user']['CodMember']} | {self.session['user']['NombreCompleto']} | {self.session['user']['DocNum']} | {self.session['user']['Correo']}"
                )

    return render_template(
        "mic.html",
        user=user,
        placas=placas,
        sgte_boletin=sgte_boletin,
        errors=errors,
    )


def load_member(db, correo):
    # gathering user data header
    db.cursor.execute(f"SELECT * FROM members WHERE Correo = '{correo}'")
    user = db.cursor.fetchone()
    print({user.keys()[n]: user[n] for n in range(13)})
    return {user.keys()[n]: user[n] for n in range(13)}
