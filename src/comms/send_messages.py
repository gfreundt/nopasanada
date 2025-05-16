import os
import uuid
from bs4 import BeautifulSoup


def send(db_cursor, monitor):

    messages = []
    # loop on all message html files in outbound folder
    html_files = [
        i for i in os.listdir(os.path.join("..", "outbound")) if "message" in i
    ]

    for html_file in html_files:
        with open(
            os.path.join("..", "outbound", html_file), "r", encoding="utf-8"
        ) as file:
            data = file.read()
            soup = BeautifulSoup(data, features="lxml")
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
        msg.update({"html_body": data})
        messages.append(msg)

    # activate mail API and send all
    # email = EmailUtils(account="servicioalertasperu@outlook.com")
    # results = email.send_from_outlook(emails=messages)
    results = [True] * 20

    # TODO: create alerts to let members know that email has been sent

    # update mensaje and mensajeContenido tables depending on success reply from email attempt
    for file_name, result, message in zip(html_files, results, messages):
        if result:
            monitor.log(
                f"Email sent to {message['to']} (IdMember = {message['idMember']}). Type: {message['msgTypes']}",
                type=4,
            )

            # register message sent in mensajes table
            db_cursor.execute(
                f"INSERT INTO mensajes (IdMember_FK, Fecha, HashCode) VALUES ({message['idMember']},'{message['timestamp']}','{message['hashcode']}')"
            )

            # get IdMensaje for record
            db_cursor.execute(
                f"SELECT * FROM mensajes WHERE HashCode = '{message['hashcode']}'"
            )
            _idmensaje = db_cursor.fetchone()[0]

            # register all message types included in message in mensajeContenidos table
            for msg_type in message["msgTypes"]:
                db_cursor.execute(
                    f"INSERT INTO mensajeContenidos VALUES ({_idmensaje}, {msg_type})"
                )

            # craft alert informing email sent and place it in outbound folder
            _msg_tail = "mensual" if "13" in message["msgTypes"] else "de bienvenida"
            _path = os.path.join(
                "..", "outbound", f"alert_{str(uuid.uuid4())[-6:]}.txt"
            )
            with open(_path, "w") as outfile:
                outfile.write(
                    f"Hola. Has recibido un mensaje del Sistema de Alertas Peru a tu correo {message['to']} con tu resumen {_msg_tail}."
                )

            # erase message from outbound folder
            os.remove(os.path.join("..", "outbound", file_name))

        else:
            monitor.log(f"ERROR sending email to {message['to']}.")
