from flask import Flask, render_template, request, redirect, session
from random import randrange
from string import ascii_uppercase
from datetime import datetime as dt
from datetime import timedelta as td
import uuid

from server.validation import FormValidate
from server.data_extraction import UserData
from members.db_utils import Database
from utils import revisar_symlinks

# TODO: fix last two to show correct format
# TODO: add soat image
# TODO: add vencimiento DNI
# TODO: cards for reportes
# TODO: send email code
# TODO: add header "under construction" to navbar

from pprint import pprint


# initialize Flask app
app = Flask(__name__)
app.config["SECRET_KEY"] = "sdlkfjsdlojf3r49tgf8"
app.config["TEMPLATES_AUTO_RELOAD"] = True


# root endpoint
@app.route("/")
def root():
    return redirect("log")


# login endpoint
@app.route("/log", methods=["GET", "POST"])
def log():

    # if user already logged in, skip login
    if "user" in session:
        return redirect("reportes")

    # empty data for first time
    form_response = {}
    errors = {}

    # validating form response
    if request.method == "POST":
        form_response = dict(request.form)
        errors = validacion.log(form_response, db=db)
        if not errors:
            # gather user data header
            session["user"] = users.get_header(correo=form_response["correo"])
            return redirect("mic")

    # render form for user to fill (first time or with errors)
    if "password" in form_response:
        form_response["password"] = ""
    return render_template("log.html", user=form_response, errors=errors)


# registration endpoints
@app.route("/reg", methods=["GET", "POST"])
def reg():

    # if user already logged in, skip registration
    if "user" in session:
        return redirect("reportes")

    # empty data for first time
    form_response = {}
    errors = {}

    # validating form response
    if request.method == "POST":
        form_response = dict(request.form)
        errors = validacion.reg(form_response, page=1)

        # no errors
        if not any(errors.values()):
            # keep data for second part of registration
            session["registration_attempt"] = form_response

            # generate validation code (TODO: replace with email)
            session["codigo_generado"] = "".join(
                [ascii_uppercase[randrange(0, len(ascii_uppercase))] for _ in range(4)]
            )
            print("@@@@@", session["codigo_generado"])

            return redirect("reg-2")

    # render form for user to fill (first time or returned with errors)
    return render_template("reg.html", user=form_response, errors=errors)


@app.route("/reg-2", methods=["GET", "POST"])
def reg2():

    if "registration_attempt" not in session:
        return redirect("reg")

    # empty data for first time
    form_response = {}
    errors = {}

    # validating form response
    if request.method == "POST":
        form_response = dict(request.form)
        errors = validacion.reg(
            form_response, codigo=session["codigo_generado"], page=2
        )

        # no errors
        if not any(errors.values()):

            # define all values to be included in database
            nom = session["registration_attempt"]["nombre"]
            cod = "SAP-" + str(uuid.uuid4())[-6:].upper()
            dni = session["registration_attempt"]["dni"]
            cel = session["registration_attempt"]["celular"]
            cor = session["registration_attempt"]["correo"]
            pwd = request.form["password1"]
            dat = dt.now().strftime("%Y-%m-%d %H:%M:%S")

            # get last record of table
            db.cursor.execute(f"SELECT IdMember FROM members ORDER BY IdMember DESC")
            rec = int(db.cursor.fetchone()[0]) + 1
            ph = "2020-01-01"

            # write new record in members table and create record in last update table
            db.cursor.execute(
                f"INSERT INTO members VALUES ({rec},'{cod}','{nom}','DNI','{dni}','{cel}','{cor}',0,0,'{dat}',0,'{pwd}')"
            )
            db.cursor.execute(
                f"INSERT INTO membersLastUpdate VALUES ({rec},'{ph}','{ph}',{ph},'{ph}','{ph}','{ph}','{ph}')"
            )
            db.conn.commit()

            # clear session data (back to login) and reload db to include new record
            session.clear()
            db.load_members()

            # log in recently created user and

            session["user"] = users.get_header(correo=cor)
            return redirect("mic")

    # render form for user to fill (first time or returned with errors)
    if "password1" in form_response:
        form_response["password1"] = ""
        form_response["password2"] = ""
    return render_template("reg-2.html", user=form_response, errors=errors)


# password recovery endpoints
@app.route("/rec", methods=["GET", "POST"])
def rec():

    # empty data for first time
    form_response = {}
    errors = {}

    # validating form response
    if request.method == "POST":
        form_response = dict(request.form)
        errors = validacion.rec(form_response, page=1)

        # no errors
        if not any(errors.values()):
            # keep data for second part of recovery
            session["recovery_attempt"] = form_response

            # generate validation code
            session["codigo_generado"] = "".join(
                [ascii_uppercase[randrange(0, len(ascii_uppercase))] for _ in range(4)]
            )
            print("@@@@@", session["codigo_generado"])

            return redirect("rec-2")

    # render form for user to fill (first time or returned with errors)
    return render_template("rec.html", user=form_response, errors=errors)


@app.route("/rec-2", methods=["GET", "POST"])
def rec2():

    if "recovery_attempt" not in session:
        return redirect("rec")

    # empty data for first time
    form_response = {}
    errors = {}

    # validating form response
    if request.method == "POST":
        form_response = dict(request.form)
        errors = validacion.rec(
            form_response, codigo=session["codigo_generado"], page=2
        )

        # no errors
        if not any(errors.values()):

            # define all values to be included in database
            cor = session["recovery_attempt"]["correo"]
            pwd = request.form["password1"]
            db.cursor.execute(
                f"UPDATE members SET Password = '{pwd}' WHERE Correo = '{cor}'"
            )
            db.conn.commit()

            # clear session data (back to login) and reload db to include new record
            session.clear()
            db.reload_db()

            return render_template("rec-3.html")

    # render form for user to fill (first time or returned with errors)
    if "password1" in form_response:
        form_response["password1"] = ""
        form_response["password2"] = ""
    return render_template("rec-2.html", user=form_response, errors=errors)


# dashboard endpoints
@app.route("/reportes", methods=["GET", "POST"])
def reportes():

    # user not logged in, go to login page
    if not session["user"]:
        return render_template("log.html")

    # if rendering page for first time, gather reports and no selection made
    if request.method == "GET":
        session["data"] = users.get_reports(user=session["user"])
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


# my account endpoint (NAVBAR)
@app.route("/mic", methods=["GET", "POST"])
def mic():

    # user not logged in, got to login page
    if "user" not in session:
        return redirect("log")

    # empty data for first time
    form_response = {}
    errors = {}

    # validating form response
    if request.method == "POST":
        form_response = dict(request.form)
        errors = validacion.mic(form_response)

        # no errors
        if not any(errors.values()):

            # process updated placas
            db.cursor.execute(
                f"DELETE FROM placas WHERE IdMember_FK = {session['user'][0]}"
            )
            db.cursor.execute(f"SELECT IdPlaca FROM placas ORDER BY IdPlaca DESC")
            rec = int(db.cursor.fetchone()[0])
            ph = "2020-01-01"  #
            for placa in (
                form_response["placa1"],
                form_response["placa2"],
                form_response["placa3"],
            ):
                if placa:
                    rec += 1
                    db.cursor.execute(
                        f"INSERT INTO placas VALUES ({rec}, {session['user'][0]}, '{placa}', '{ph}', '{ph}', '{ph}', '{ph}', '{ph}')"
                    )
            rec += 1

            # TODO: process updated communication options

            db.conn.commit()

            return render_template("mic-2.html")

    # render form for user to edit (first time or returned with errors)
    db.cursor.execute(f"SELECT * FROM placas WHERE IdMember_FK = {session['user'][0]}")
    placas = [i[2] for i in db.cursor.fetchall()]
    db.cursor.execute(
        f"SELECT Fecha FROM mensajes WHERE IdMember_FK = {session['user'][0]} ORDER BY Fecha DESC"
    )
    _fecha = db.cursor.fetchone()
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
        "opt_in_mensajes": True,
        "Soat": True,
        "Brevete": True,
        "RevTec": False,
        "Dni": False,
        "opt_in_alertas1": True,
        "Sutran": False,
        "Sat": True,
        "Mtc": False,
        "opt_in_alertas2": False,
    }
    return render_template(
        "mic.html", user=form_response, placas=placas, comm=comm, errors=errors
    )


# home endpoint (NAVBAR)
@app.route("/home")
def home():
    return redirect("log")


# logout endpoint (NAVBAR)
@app.route("/logout")
def logout():
    session.clear()
    return redirect("log")


if __name__ == "__main__":
    revisar_symlinks()
    db = Database(dev=False)
    users = UserData(db=db)
    validacion = FormValidate(db=db)
    app.run(debug=True)
