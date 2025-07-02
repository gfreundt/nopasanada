import os
from bs4 import BeautifulSoup
from src.utils.email import Email
from datetime import datetime as dt


def send(db, dash, max=9999):

    CARD = 11

    # select all the emails in outbound folder
    html_files = [i for i in os.listdir(os.path.join("outbound")) if ".html" in i]

    # log first action
    dash.log(general_status=("Activo", 1))
    dash.log(
        card=CARD,
        title=f"Comunicaciones [{min(max, len(html_files))}]",
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
    for counter, html_file in enumerate(html_files):

        # take html information and create email
        html_files = [i for i in os.listdir(os.path.join("outbound")) if ".html" in i]
        # exit loop if reached max emails
        if counter >= max:
            break

        # open files and find all relevant elements
        with open(os.path.join("outbound", html_file), "r", encoding="utf-8") as file:
            data = file.read()
            soup = BeautifulSoup(data, features="lxml")

        # load all meta information into variable
        msg = {i.get("name"): i.get("content") for i in soup.find_all("meta")}

        # parse message types and convert to list
        msg["msgTypes"] = [i for i in msg["msgTypes"][1:-1].split(",")]

        # parse attachment paths and convert to list
        if msg.get("attachment"):
            msg["attachments"] = [
                i.get("content")
                for i in soup.find_all("meta")
                if i.get("name") == "attachment"
            ]
        msg.update({"html_content": data})

        # log action
        dash.log(card=CARD, text=f"Enviando: {msg["to"]}")

        # activate mail API and send all
        response = email.send_email(msg)

        # update dashboard with progress and last update timestamp
        dash.log(
            card=CARD,
            progress=int((counter / min(max, len(html_files))) * 100),
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
            _idmensaje = db.cursor.fetchone()[0]

            # register all message types included in message in mensajeContenidos table
            for msg_type in msg["msgTypes"]:
                db.cursor.execute(
                    f"INSERT INTO mensajeContenidos VALUES ({_idmensaje}, {msg_type})"
                )

            # erase message from outbound folder
            os.remove(os.path.join("outbound", html_file))
            dash.log(action=f"[ SEND ] | {msg['to']}")

        else:
            print(f"ERROR sending email to {msg['to']}.")

    db.conn.commit()

    # log last action
    dash.log(
        card=CARD,
        title="Comunicaciones",
        progress=100,
        status=3,
        text="Inactivo",
        lastUpdate=dt.now(),
    )
