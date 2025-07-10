import os
from jinja2 import Environment, FileSystemLoader
import uuid
import sqlite3


def craft():
    NETWORK_PATH = os.path.join(r"\\192.168.68.110", "d", "pythonCode", "nopasanada")

    conn = sqlite3.connect(
        os.path.join(NETWORK_PATH, "data", "members.db"), check_same_thread=False
    )
    db_cursor = conn.cursor()

    # load HTML templates
    environment = Environment(loader=FileSystemLoader("templates/"))
    template = environment.get_template("invitacion_a_landing.html")

    messages = []

    # loop all members that required a message
    db_cursor.execute("SELECT NombreCompleto, Correo, CodMember, Password FROM members")
    for member in db_cursor.fetchall():
        email_id = f"{member[2]}|{str(uuid.uuid4())[-12:]}"
        messages.append(
            compose_message(
                nombre=member[0],
                correo=member[1],
                email_id=email_id,
                template=template,
                subject="Bienvenido a la Web de No Pasa Nada PE",
                pwd=member[3],
            )
        )

    # save crafted messages as HTML in outbound folder
    for message in messages:
        _file_path = os.path.join(
            NETWORK_PATH, "outbound", f"message_{str(uuid.uuid4())[-6:]}.html"
        )
        with open(_file_path, "w", encoding="utf-8") as file:
            file.write(message)


def compose_message(nombre, correo, email_id, template, subject, pwd):

    _info = {
        "nombre": nombre,
        "password": pwd,
        "to": correo,
        "bcc": "gabfre@gmail.com",
        "hashcode": email_id,
        "subject": subject,
    }

    return template.render(_info)


craft()
