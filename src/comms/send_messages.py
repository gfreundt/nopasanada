import os
from bs4 import BeautifulSoup
from src.utils import Email


def send(db, dash, max=9999):

    email = Email(from_account="info@nopasanadape.com", password="5QJWEKi0trAL")

    k = 0

    # take html information and create email
    html_files = [i for i in os.listdir(os.path.join("outbound")) if ".html" in i]

    for html_file in html_files:
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

        # only send up to max emails
        if k < max:

            # activate mail API and send all
            response = email.send_email(msg)

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

                print(f"OK sending email to {msg['to']}.")

            else:
                print(f"ERROR sending email to {msg['to']}.")

        k += 1

    db.conn.commit()
