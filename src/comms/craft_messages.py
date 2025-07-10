import os
from datetime import datetime as dt
from jinja2 import Environment, FileSystemLoader
import uuid
from src.comms import create_within_expiration
from src.utils.constants import NETWORK_PATH
from src.utils.utils import date_to_mail_format


def craft(db_cursor, dash):

    # update table with all expiration information for message alerts
    create_within_expiration.update_table(db_cursor)

    # log action
    # dash()

    # load HTML templates
    environment = Environment(loader=FileSystemLoader("templates/"))
    template_welcome = environment.get_template("bienvenida.html")
    template_regular = environment.get_template("regular.html")

    messages = []

    # loop all members that required a welcome message
    db_cursor.execute(
        "SELECT IdMember_FK FROM _necesitan_mensajes_usuarios WHERE Tipo = 'B'"
    )
    for member in db_cursor.fetchall():
        messages.append(
            grab_message_info(
                db_cursor,
                member["IdMember_FK"],
                template=template_welcome,
                subject="Bienvenido al Servicio de Alertas Perú",
                msg_type=12,
            )
        )

    # loop all members that required a regular message
    db_cursor.execute(
        "SELECT IdMember_FK FROM _necesitan_mensajes_usuarios WHERE Tipo = 'R'"
    )
    for member in db_cursor.fetchall():
        messages.append(
            grab_message_info(
                db_cursor,
                member["IdMember_FK"],
                template=template_regular,
                subject="Tu Boletín de No Pasa Nada PE",
                msg_type=13,
            )
        )

    # save crafted messages as HTML in outbound folder
    for message in messages:
        _file_path = os.path.join(
            NETWORK_PATH, "outbound", f"message_{str(uuid.uuid4())[-6:]}.html"
        )
        with open(_file_path, "w", encoding="utf-8") as file:
            file.write(message)


def grab_message_info(db_cursor, IdMember, template, subject, msg_type):

    # get member information
    db_cursor.execute(f"SELECT * FROM members WHERE IdMember = {IdMember}")
    member = db_cursor.fetchone()

    # get message alerts
    db_cursor.execute(
        f"SELECT TipoAlerta, Placa, Vencido FROM _expira30dias WHERE IdMember = {IdMember}"
    )
    _a = db_cursor.fetchall()
    alertas = (
        [[i["TipoAlerta"], i["Placa"], i["Vencido"]] for i in _a if i] if _a else []
    )

    # get placas associated with member
    db_cursor.execute(f"SELECT Placa FROM placas WHERE IdMember_FK = {IdMember}")
    placas = [i["Placa"] for i in db_cursor.fetchall()]

    # generate random email hash
    email_id = f"{member['CodMember']}|{str(uuid.uuid4())[-12:]}"

    # create html format data
    return compose_message(
        db_cursor, member, template, email_id, subject, alertas, placas, msg_type
    )


def compose_message(
    db_cursor, member, template, email_id, subject, alertas, placas, msg_type
):

    _txtal = []
    _attachments = []
    _attach_txt = []
    _msgrecords = []
    _info = {}

    # create list of alerts
    for i in alertas:
        match i[0]:
            case "BREVETE":
                _txtal.append(
                    f"Licencia de Conducir {'vencida.' if i[2] else 'vence en menos de 30 días.'}"
                )
            case "SOAT":
                _txtal.append(
                    f"Certificado SOAT de placa {i[1]} {'vencido.' if i[2] else 'vence en menos de 30 días.'}"
                )
            case "SATIMP":
                _txtal.append(
                    f"Impuesto Vehicular SAT {'vencido.' if i[2] else 'vence en menos de 30 días.'}"
                )
            case "REVTEC":
                _txtal.append(
                    f"Revision Técnica de placa {i[1]} {'vencida.' if i[2] else 'vence en menos de 30 días.'}"
                )
            case "SUTRAN":
                _txtal.append(f"Multa impaga en SUTRAN para placa {i[1]}.")
            case "SATMUL":
                _txtal.append(f"Multa impaga en SAT para {i[1]}.")
            case "MTCPAPELETA":
                _txtal.append("Papeleta Impaga reportada en el MTC.")

    # add list of Alertas or "Ninguna" if empty
    _info.update({"alertas": _txtal if _txtal else ["Ninguna"]})

    # add randomly generated email ID, nombre and lista placas for opening text
    _info.update(
        {
            "nombre_usuario": member[2],
            "codigo_correo": email_id,
            "lista_placas": ", ".join(placas),
        }
    )

    # add revision tecnica information
    db_cursor.execute(
        f"SELECT * FROM revtecs WHERE PlacaValidate IN (SELECT Placa FROM placas WHERE IdMember_FK = {member[0]}) ORDER BY LastUpdate DESC"
    )
    _revtecs = []

    for _m in db_cursor.fetchall():

        _revtecs.append(
            {
                "certificadora": _m["Certificadora"].split("-")[-1][:35],
                "placa": _m["PlacaValidate"],
                "certificado": _m["Certificado"],
                "fecha_desde": date_to_mail_format(_m["FechaDesde"]),
                "fecha_hasta": date_to_mail_format(_m["FechaHasta"], delta=True),
                "resultado": _m["Resultado"],
                "vigencia": _m["Vigencia"],
            }
        )
    _info.update({"revtecs": _revtecs})

    # add brevete information
    db_cursor.execute(
        f"SELECT * FROM brevetes WHERE IdMember_FK = {member[0]} ORDER BY LastUpdate DESC"
    )
    _m = db_cursor.fetchone()
    if _m:
        _info.update(
            {
                "brevete": {
                    "numero": _m["Numero"],
                    "clase": _m["Clase"],
                    "formato": _m["Tipo"],
                    "fecha_desde": date_to_mail_format(_m["FechaExp"]),
                    "fecha_hasta": date_to_mail_format(_m["FechaHasta"], delta=True),
                    "restricciones": _m["Restricciones"],
                    "local": _m["Centro"],
                    "puntos": _m["Puntos"],
                    "record": _m["Record"],
                }
            }
        )
    else:
        _info.update({"brevete": {}})

    # add SUTRAN information
    _sutran = []
    db_cursor.execute(
        f"SELECT * FROM sutrans JOIN placas ON Placa = PlacaValidate WHERE Placa IN (SELECT Placa FROM placas WHERE IdMember_FK = {member[0]}) ORDER BY LastUpdate DESC"
    )
    for _m in db_cursor.fetchall():
        if _m:
            _sutran.append(
                {
                    "placa": _m[9],
                    "documento": _m[1],
                    "tipo": _m[2],
                    "fecha_documento": date_to_mail_format(_m[3]),
                    "infraccion": (f"{_m[4]} - {_m[5]}"),
                }
            )
        _info.update({"sutrans": _sutran})

    # add SATIMP information
    db_cursor.execute(
        f"SELECT * FROM satimpCodigos WHERE IdMember_FK = {member[0]} ORDER BY LastUpdate DESC"
    )

    _v = []
    for satimp in db_cursor.fetchall():
        db_cursor.execute(f"SELECT * FROM satimpDeudas WHERE IdCodigo_FK = {satimp[0]}")
        _s = []
        for _x in db_cursor.fetchall():
            _s.append(
                {
                    "ano": _x[1],
                    "periodo": _x[2],
                    "doc_num": _x[3],
                    "total_a_pagar": _x[4],
                }
            )
        _v.append({"codigo": satimp[2], "deudas": _s})
    _info.update({"satimps": _v})

    # add SOAT information
    _soats = []
    db_cursor.execute(
        f"SELECT * FROM soats WHERE PlacaValidate IN (SELECT Placa FROM placas WHERE IdMember_FK = {member[0]}) ORDER BY LastUpdate DESC"
    )
    for _m in db_cursor.fetchall():
        _soats.append(
            {
                "aseguradora": _m[1],
                "fecha_desde": date_to_mail_format(_m[2]),
                "fecha_hasta": date_to_mail_format(_m[3], delta=True),
                "certificado": _m[5],
                "placa": _m[4],
                "uso": _m[6],
                "clase": _m[7],
                "vigencia": _m[8],
                "tipo": _m[9],
            }
        )
        # add image to attachment list
        _img_path = os.path.abspath(
            os.path.join(NETWORK_PATH, "data", "images", _m[11])
        )
        if os.path.isfile(_img_path):
            _attachments.append(str(_img_path))
            _attach_txt.append(
                f"Certificado Electrónico SOAT de Vehículo Placa {_m[4]}."
            )
            _msgrecords.append(15)
    _info.update({"soats": _soats})

    # add SATMUL information
    _satmuls = []
    db_cursor.execute(
        f"SELECT * FROM satmuls WHERE PlacaValidate IN (SELECT Placa FROM placas WHERE IdMember_FK = {member[0]}) ORDER BY LastUpdate DESC"
    )
    for _m in db_cursor.fetchall():
        _satmuls.append(
            {
                "placa": _m[1],
                "reglamento": _m[2],
                "falta": _m[3],
                "documento": _m[4],
                "fecha_emision": date_to_mail_format(_m[5]),
                "importe": _m[6],
                "gastos": _m[7],
                "descuento": _m[8],
                "deuda": _m[9],
                "estado": _m[10],
                "licencia": _m[11],
            }
        )
        # add image to attachment list
        _img_path = os.path.abspath(
            os.path.join(NETWORK_PATH, "data", "images", _m[14])
        )
        if os.path.isfile(_img_path):
            _attachments.append(str(_img_path))
            _attach_txt.append(
                f"Papeleta de Infracción de Tránsito de Vehículo Placa {_m[2]}."
            )
            _msgrecords.append(17)
    _info.update({"satmuls": _satmuls})

    # add PAPELETA information
    _papeletas = []
    db_cursor.execute(
        f"SELECT * FROM mtcPapeletas WHERE IdMember_FK = {member[0]} ORDER BY LastUpdate DESC"
    )

    for _m in db_cursor.fetchall():
        _papeletas.append(
            {
                "entidad": _m[1],
                "numero": _m[2],
                "fecha": date_to_mail_format(_m[3]),
                "fecha_firme": date_to_mail_format(_m[4]),
                "falta": _m[5],
                "estado_deuda": _m[6],
            }
        )
    _info.update({"papeletas": _papeletas})

    # add SUNARP image
    db_cursor.execute(
        f"""    SELECT * FROM sunarps 
                WHERE PlacaValidate IN
                    (SELECT Placa FROM placas
                        WHERE IdMember_FK = {member[0]})
                ORDER BY LastUpdate DESC"""
    )
    for _m in db_cursor.fetchall():
        # add image to attachment list
        _img_path = os.path.abspath(
            os.path.join(NETWORK_PATH, "data", "images", _m[15])
        )
        if os.path.isfile(_img_path):
            _attachments.append(str(_img_path))
            _attach_txt.append(
                f"Consulta Vehicular SUNARP de Vehículo Placa {_m[15][-10:-4]}."
            )
            _msgrecords.append(16)

    # add RECORD DE CONDUCTOR image
    db_cursor.execute(
        f"SELECT * FROM recordConductores WHERE IdMember_FK = {member[0]} ORDER BY LastUpdate DESC"
    )
    for _m in db_cursor.fetchall():
        # add image to attachment list
        _img_path = os.path.abspath(os.path.join(NETWORK_PATH, "data", "images", _m[1]))
        if os.path.isfile(_img_path):
            _attachments.append(str(_img_path))
            _attach_txt.append("Récord del Conductor MTC.")
            _msgrecords.append(14)

    # add SUNAT information
    _sunats = []
    db_cursor.execute(
        f"SELECT * FROM sunats WHERE IdMember_FK = {member[0]} ORDER BY LastUpdate DESC"
    )
    _m = db_cursor.fetchone()
    if _m:
        _sunats = {
            "ruc": _m[1],
            "tipo_contribuyente": _m[2],
            "fecha_inscripcion": _m[5],
            "fecha_inicio_actividades": _m[9],
            "estado": _m[6],
            "condicion": _m[7],
        }
    else:
        _sunats = []

    _info.update({"sunat": _sunats})

    # add JNE Afiliacion information
    db_cursor.execute(
        f"SELECT * FROM jneAfiliacion WHERE IdMember_FK = {member[0]} ORDER BY LastUpdate DESC"
    )
    _m = db_cursor.fetchone()
    if _m and _m[1]:
        _jneafil = True
        # add image to attachment list
        _img_path = os.path.abspath(os.path.join(NETWORK_PATH, "data", "images", _m[2]))
        if os.path.isfile(_img_path):
            _attachments.append(str(_img_path))
            _attach_txt.append("Afiliación a Partidos Políticos")
            _msgrecords.append(15)
    else:
        _jneafil = False

    _info.update({"jne_afiliacion": _jneafil})

    # add text list of Attachments or "Ninguno" if empty
    _info.update({"adjuntos": _attach_txt if _attach_txt else ["Ninguno"]})

    # subject title number of alerts
    _subj = (
        f"{len(_txtal)} ALERTAS"
        if len(_txtal) > 1
        else "1 ALERTA" if len(_txtal) == 1 else "SIN ALERTAS"
    )

    # meta data
    _info.update({"to": member[6]})
    _info.update({"bcc": "gabfre@gmail.com"})
    _info.update({"subject": f"{subject} ({_subj})"})
    _info.update({"msg_types": [msg_type] + _msgrecords})
    _info.update({"idMember": int(member[0])})
    _info.update({"timestamp": dt.now().strftime("%Y-%m-%d %H:%M:%S")})
    _info.update({"hashcode": email_id})
    _info.update({"attachments": _attachments})

    return template.render(_info)
