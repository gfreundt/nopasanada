import os
from jinja2 import Environment, FileSystemLoader
from datetime import datetime as dt
import uuid
from src.utils.constants import NETWORK_PATH
from src.utils.utils import date_to_mail_format


def craft(db_cursor, dash):

    # load HTML templates
    environment = Environment(loader=FileSystemLoader("templates/"))
    template_alertas = environment.get_template("alerta.html")

    alerts = []
    index_alertas = {"SOAT": 1, "REVTEC": 3, "SATIMP": 5, "BREVETE": 7}

    # loop all members that required an alert
    db_cursor.execute(
        "SELECT IdMember_FK, TipoAlerta, Vencido, FechaHasta, Placa FROM _necesitan_alertas"
    )
    for idmember, tipo_alerta, vencido, fecha_hasta, placa in db_cursor.fetchall():

        if idmember:
            alerts.append(
                compose_message(
                    db_cursor,
                    idmember=idmember,
                    template=template_alertas,
                    fecha_hasta=fecha_hasta,
                    subject="ALERTA de No Pasa Nada PE",
                    msg_type=index_alertas[tipo_alerta],
                    tipo_alerta=tipo_alerta,
                    vencido=vencido,
                    placa=placa,
                )
            )

    # loop all members in alert list, compose message
    for k, alert in enumerate(alerts):
        if alert:
            # write in outbound folder
            with open(
                os.path.join(NETWORK_PATH, "outbound", f"alert_{k:03d}.html"),
                "w",
                encoding="utf-8",
            ) as file:
                file.write(alert)


def compose_wapp(alert_data):
    # same header for all alerts
    _base_msg = "No Pasa Nada PE te informa:\n"

    # add all corresponding alerts to message text
    match alert_data[5]:
        case "BREVETE":
            msg = f"{_base_msg}{alert_data[1]}, tu Licencia de Conducir vence el {date_to_mail_format(alert_data[4])}.\n"
        case "SOAT":
            msg = f"{_base_msg}{alert_data[1]}, tu Certificado SOAT de placa *{alert_data[3]}* vence el *{date_to_mail_format(alert_data[4])}*.\n"
        case "SATIMP":
            msg = f"{_base_msg}{alert_data[1]}, tu Impuesto Vehicular SAT vence el {date_to_mail_format(alert_data[4])}.\n"
        case "REVTEC":
            msg = f"{_base_msg}{alert_data[1]}, tu Revision Técnica de placa *{alert_data[3]}* vence el *{date_to_mail_format(alert_data[4])}*.\n"

    return msg


def compose_message(
    db_cursor,
    idmember,
    template,
    subject,
    msg_type,
    tipo_alerta,
    vencido,
    fecha_hasta,
    placa,
):

    # get member information
    db_cursor.execute(f"SELECT * FROM members WHERE IdMember = {idmember}")
    member = db_cursor.fetchone()

    if not member:
        return

    # generate random email hash
    email_id = f"{member['CodMember']}|{str(uuid.uuid4())[-12:]}"

    _info = {}

    titulo_alerta = "Alerta de Vencimiento: "
    if tipo_alerta == "BREVETE":
        _t = "Licencia de Conducir"
    elif tipo_alerta == "REVTEC":
        _t = f"Revisión Técnica para placa {placa}"
    elif tipo_alerta == "SOAT":
        _t = f"SOAT para placa {placa}"
    elif tipo_alerta == "SATIMP":
        _t = "Impuesto Vehicular SAT Lima "

    texto_alerta = f"Tu {_t} {"ha vencido" if vencido else "está cerca de vencer"} el {fecha_hasta}."

    _info.update(
        {
            "nombre_usuario": member["NombreCompleto"],
            "codigo_correo": email_id,
            "titulo_alerta": titulo_alerta,
            "texto_alerta": texto_alerta,
            "vencido": vencido,
        }
    )

    # meta data
    _info.update({"to": member["Correo"]})
    _info.update({"bcc": "gabfre@gmail.com"})
    _info.update({"subject": f"{subject}"})
    _info.update({"msg_types": [msg_type]})
    _info.update({"idMember": int(member["IdMember"])})
    _info.update({"timestamp": dt.now().strftime("%Y-%m-%d %H:%M:%S")})
    _info.update({"hashcode": f"{member[1]}|{str(uuid.uuid4())[-12:]}"})
    _info.update({"attachment_paths": []})

    return template.render(_info)
