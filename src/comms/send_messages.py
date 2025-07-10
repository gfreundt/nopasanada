import os
from datetime import datetime as dt
from bs4 import BeautifulSoup
from src.utils.email import Email
from src.utils.constants import NETWORK_PATH


def send(db, dash, max=9999):

    CARD = 11

    # select all the emails in outbound folder and cap list to max amount to send
    html_files = [
        i for i in os.listdir(os.path.join(NETWORK_PATH, "outbound")) if ".html" in i
    ][:max]

    # log first action
    dash.logging(general_status=("Activo", 1))
    dash.logging(
        card=CARD,
        title=f"Comunicaciones [{len(html_files)}]",
        status=1,
        progress=0,
        text="Inicializando",
        lastUpdate="Actualizado:",
    )

    # activate send account
    email = Email(
        from_account="info@nopasanadape.com", password=os.environ["ZOHO-1-PWD"]
    )

    counter = 0
    # iterate on all html files in outbound folder
    for html_file in html_files:

        # open files and find all relevant elements
        with open(
            os.path.join(NETWORK_PATH, "outbound", html_file), "r", encoding="utf-8"
        ) as file:
            data = file.read()
            soup = BeautifulSoup(data, features="lxml")

        # load all meta information into variable
        msg = {i.get("name"): i.get("content") for i in soup.find_all("meta")}

        # parse message types and convert to list
        if msg.get("msgTypes"):
            msg["msgTypes"] = [i for i in msg["msgTypes"][1:-1].split(",")]
        else:
            msg["msgTypes"] = []

        # parse attachment paths and convert to list
        if msg.get("attachment"):
            msg["attachments"] = [
                i.get("content")
                for i in soup.find_all("meta")
                if i.get("name") == "attachment"
            ]
        msg.update({"html_content": data})

        # log action
        dash.logging(card=CARD, text=f"Enviando: {msg["to"]}")

        # activate mail API and send all
        response = email.send_email(msg)

        # update dashboard with progress and last update timestamp
        dash.logging(
            card=CARD,
            progress=int((counter / len(html_files)) * 100),
            lastUpdate=dt.now(),
        )

        # register message sent in mensajes table (if email sent correctly)
        if response:
            db.cursor.execute(
                f"INSERT INTO mensajes (IdMember_FK, FechaEnvio, HashCode) VALUES ({msg['idMember']},'{msg['timestamp']}','{msg['hashcode']}')"
            )

            # get IdMensaje for record
            db.cursor.execute(
                f"SELECT * FROM mensajes WHERE HashCode = '{msg['hashcode']}'"
            )
            _idmensaje = db.cursor.fetchone()["IdMensaje"]

            # register all message types included in message in mensajeContenidos table
            for msg_type in msg["msgTypes"]:
                db.cursor.execute(
                    f"INSERT INTO mensajeContenidos VALUES ({_idmensaje}, {msg_type})"
                )

            # erase message from outbound folder
            os.remove(os.path.join(NETWORK_PATH, "outbound", html_file))
            dash.logging(action=f"[ SEND ] | {msg['to']}")

        else:
            print(f"ERROR sending email to {msg['to']}.")

        counter += 1

    db.conn.commit()

    # log last action
    dash.logging(
        card=CARD,
        title="Comunicaciones",
        progress=100,
        status=3,
        text="Inactivo",
        lastUpdate=dt.now(),
    )
