import os
from datetime import datetime as dt


class UserData:

    def __init__(self, db):
        self.cursor = db.cursor

    def date_to_user_format(self, fecha, delta=False):
        _months = (
            "Ene",
            "Feb",
            "Mar",
            "Abr",
            "May",
            "Jun",
            "Jul",
            "Ago",
            "Set",
            "Oct",
            "Nov",
            "Dic",
        )
        _day = fecha[8:]
        _month = _months[int(fecha[5:7]) - 1]
        _year = fecha[:4]
        _deltatxt = ""
        if delta:
            _delta = int((dt.strptime(fecha, "%Y-%m-%d") - dt.now()).days)
            _deltatxt = f"[ {_delta:,} días ]" if _delta > 0 else "[ VENCIDO ]"
        return f"{_day}-{_month}-{_year} {_deltatxt}"

    def get_header(self, correo):
        # gathering user data header
        self.cursor.execute(f"SELECT * FROM members WHERE Correo = '{correo}'")
        user = self.cursor.fetchone()
        print({user.keys()[n]: user[n] for n in range(13)})
        return {user.keys()[n]: user[n] for n in range(13)}

    def get_reports(self, user):

        _info = {"user": user}

        _attachments = []
        member = user["IdMember"]

        # add placas
        self.cursor.execute(f"SELECT * FROM placas WHERE IdMember_FK = {member}")
        _info.update({"placas": [i["Placa"] for i in self.cursor.fetchall()]})

        # add brevete information
        self.cursor.execute(
            f"SELECT * FROM brevetes WHERE IdMember_FK = {member} ORDER BY LastUpdate DESC"
        )
        _m = self.cursor.fetchone()
        if _m:
            _vigencia = int((dt.strptime(_m["FechaHasta"], "%Y-%m-%d") - dt.now()).days)
            _info.update(
                {
                    "brevete": {
                        "numero": _m["Numero"],
                        "clase": _m["Clase"],
                        "formato": _m["Tipo"],
                        "fecha_desde": _m["FechaExp"],
                        "fecha_hasta": _m["FechaHasta"],
                        "restricciones": _m["Restricciones"],
                        "local": _m["Centro"],
                        "puntos": _m["Puntos"],
                        "record": _m["Record"],
                        "vigencia": (
                            f"{_vigencia:,} días" if _vigencia > 0 else "Vencida"
                        ),
                    }
                }
            )
        else:
            _info.update({"brevete": {}})

        # add SATIMP information
        self.cursor.execute(
            f"SELECT * FROM satimpCodigos WHERE IdMember_FK = {member} ORDER BY LastUpdate DESC"
        )

        _v = []
        for satimp in self.cursor.fetchall():
            self.cursor.execute(
                f"SELECT * FROM satimpDeudas WHERE IdCodigo_FK = {satimp[0]}"
            )
            _s = []
            for _x in self.cursor.fetchall():
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

        # add RECORD DE CONDUCTOR image
        self.cursor.execute(
            f"SELECT * FROM recordConductores WHERE IdMember_FK = {member} ORDER BY LastUpdate DESC"
        )

        _records = []
        for _m in self.cursor.fetchall():
            # add image to attachment list
            _img_path = os.path.join(os.curdir, "data", "images", _m[1])
            if True:  # os.path.isfile(_img_path):
                _records.append(str(_m[1]))
        _info.update({"record": _records})

        # add SATMUL information
        _satmuls = []
        self.cursor.execute(
            f"SELECT * FROM satmuls WHERE PlacaValidate IN (SELECT Placa FROM placas WHERE IdMember_FK = {member}) ORDER BY LastUpdate DESC"
        )
        for _m in self.cursor.fetchall():
            _satmuls.append(
                {
                    "placa": _m[1],
                    "reglamento": _m[2],
                    "falta": _m[3],
                    "documento": _m[4],
                    "fecha_emision": self.date_to_user_format(_m[5]),
                    "importe": _m[6],
                    "gastos": _m[7],
                    "descuento": _m[8],
                    "deuda": _m[9],
                    "estado": _m[10],
                    "licencia": _m[11],
                }
            )
            # add image to attachment list
            _img_path = os.path.abspath(os.path.join("..", "data", "images", _m[14]))
            if os.path.isfile(_img_path):
                _attachments.append(str(_img_path))
        _info.update({"satmuls": _satmuls})

        # add SUTRAN information
        _sutran = []
        self.cursor.execute(
            f"SELECT * FROM sutrans JOIN placas ON Placa = PlacaValidate WHERE PlacaValidate IN (SELECT Placa FROM placas WHERE IdMember_FK = {member}) ORDER BY LastUpdate DESC"
        )
        for _m in self.cursor.fetchall():
            if _m:
                _sutran.append(
                    {
                        "placa": _m[9],
                        "documento": _m[1],
                        "tipo": _m[2],
                        "fecha_documento": self.date_to_user_format(_m[3]),
                        "infraccion": (f"{_m[4]} - {_m[5]}"),
                    }
                )
        _info.update({"sutrans": _sutran})

        # add PAPELETA information
        _papeletas = []
        self.cursor.execute(
            f"SELECT * FROM mtcPapeletas WHERE IdMember_FK = {member} ORDER BY LastUpdate DESC"
        )
        for _m in self.cursor.fetchall():
            _papeletas.append(
                {
                    "entidad": _m[2],
                    "numero": _m[3],
                    "fecha": self.date_to_user_format(_m[4]),
                    "fecha_firme": self.date_to_user_format(_m[5]),
                    "falta": _m[6],
                    "estado_deuda": _m[7],
                }
            )
        _info.update({"papeletas": _papeletas})

        # add SOAT information
        _soats = []
        self.cursor.execute(
            f"SELECT * FROM soats WHERE PlacaValidate IN (SELECT Placa FROM placas WHERE IdMember_FK = {member}) ORDER BY LastUpdate DESC"
        )
        for _m in self.cursor.fetchall():
            _soats.append(
                {
                    "aseguradora": _m[1],
                    "fecha_desde": self.date_to_user_format(_m[2]),
                    "fecha_hasta": self.date_to_user_format(_m[3], delta=True),
                    "certificado": _m[5],
                    "placa": _m[4],
                    "uso": _m[6],
                    "clase": _m[7],
                    "vigencia": _m[8],
                    "tipo": _m[9],
                }
            )
            # add image to attachment list
            _img_path = os.path.abspath(os.path.join("..", "data", "images", _m[11]))
            if os.path.isfile(_img_path):
                _attachments.append(str(_img_path))

        _info.update({"soats": _soats})

        # add REVTEC information
        self.cursor.execute(
            f"SELECT * FROM revtecs WHERE PlacaValidate IN (SELECT Placa FROM placas WHERE IdMember_FK = {member}) ORDER BY LastUpdate DESC"
        )
        _revtecs = []

        for _m in self.cursor.fetchall():

            _revtecs.append(
                {
                    "certificadora": _m[1].split("-")[-1][:35],
                    "placa": _m[2],
                    "certificado": _m[3],
                    "fecha_desde": self.date_to_user_format(_m[4]),
                    "fecha_hasta": self.date_to_user_format(_m[5], delta=True),
                    "resultado": _m[6],
                    "vigencia": _m[7],
                }
            )
        _info.update({"revtecs": _revtecs})

        # add SUNARP image
        _images = []
        self.cursor.execute(
            f"""SELECT * FROM sunarps
                    WHERE PlacaValidate IN (SELECT Placa FROM placas WHERE IdMember_FK = {member})
                ORDER BY LastUpdate DESC"""
        )
        for _m in self.cursor.fetchall():
            # add image to attachment list
            _img_path = os.path.abspath(os.path.join("..", "data", "images", _m[15]))
            if os.path.isfile(_img_path):
                _images.append(os.path.basename(_img_path))

        _info.update({"sunarps": _images})

        return _info
