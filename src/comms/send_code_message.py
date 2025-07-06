from threading import Thread
from jinja2 import Environment, FileSystemLoader
from src.utils.email import Email
from src.utils.constants import ZOHO_INFO_PASSWORD


def send_code(codigo, correo, nombre):

    # activate thread to send email in parallel
    thread = Thread(target=run_thread, args=(codigo, correo, nombre))
    thread.start()


def run_thread(codigo, correo, nombre):

    # load HTML templates
    environment = Environment(loader=FileSystemLoader("templates/"))
    template = environment.get_template("codigo.html")

    # crea objeto para enviar correo desde info@
    email = Email(from_account="info@nopasanadape.com", password=ZOHO_INFO_PASSWORD)

    # crear contenido del correo
    msg = {
        "to": correo,
        "bcc": "gabfre@gmail.com",
        "from": email.from_account,
        "subject": "Código Único de Validación",
        "html_content": template.render({"codigo": codigo, "nombre": nombre}),
    }

    # enviar
    email.send_email(msg)
