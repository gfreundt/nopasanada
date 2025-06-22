import re


class FormValidate:

    def __init__(self, db):

        self.conn = db.conn
        self.cursor = db.cursor

        # load members
        cmd = "SELECT * FROM members"
        self.cursor.execute(cmd)
        self.user_db = self.cursor.fetchall()
        self.dnis = [i[4] for i in self.user_db]
        self.celulares = [str(i[5]) for i in self.user_db]
        self.correos = [i[6] for i in self.user_db]

    def log(self, form_data, db):

        # check if correo exists
        cmd = f"SELECT * FROM members WHERE Correo = '{form_data["correo"]}'"
        self.cursor.execute(cmd)
        if not self.cursor.fetchone():
            return {"correo": ["Correo no registrado"]}

        # check if password correct for that correo
        cmd += f" AND Password = '{form_data["password"]}'"
        self.cursor.execute(cmd)
        if not self.cursor.fetchone():
            return {"password": ["Contraseña equivocada"]}

        # correo/password combo correct
        return False

    def reg(self, reg, page, codigo=None):

        # realizar todas las validaciones
        errors = {
            "nombre": [],
            "dni": [],
            "correo": [],
            "celular": [],
            "codigo": [],
            "password1": [],
            "password2": [],
        }

        if page == 1:

            # nombre
            if len(reg["nombre"]) < 5:
                errors["nombre"].append("Nombre debe tener mínimo 5 letras")

            # dni
            if not re.match(r"^[0-9]{8}$", reg["dni"]):
                errors["dni"].append("DNI solamente debe tener 8 dígitos")
            if reg["dni"] in self.dnis:
                errors["dni"].append("DNI ya está registado")

            # correo
            if not re.match(
                r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", reg["correo"]
            ):
                errors["correo"].append("Ingrese un correo válido")
            if reg["correo"] in self.correos:
                errors["correo"].append("Correo ya está registrado")

            # celular
            if not re.match(r"^[0-9]{9}$", reg["celular"]):
                errors["celular"].append("Ingrese un celular válido")
            if reg["celular"] in self.celulares:
                errors["celular"].append("Celular ya esta registrado")

        elif page == 2:

            # codigo
            if not re.match(r"^[A-Za-z]{4}$", reg["codigo"]):
                errors["codigo"].append("Codigo de validacion son 4 letras")
            if reg["codigo"] != codigo:
                errors["codigo"].append("Código de validación incorrecto")

            # constraseña
            if not re.match(r"^(?=.*[A-Z])(?=.*\d).{6,20}$", reg["password1"]):
                errors["password1"].append(
                    "Al menos 6 caracteres e incluir una mayúscula y un número"
                )

            # validacion de contraseña
            if reg["password1"] != reg["password2"]:
                errors["password2"].append("Contraseñas no coinciden")

        return errors

    def rec(self, rec, page, codigo=None):

        # realizar todas las validaciones
        errors = {
            "correo": [],
            "codigo": [],
            "password1": [],
            "password2": [],
        }

        if page == 1:

            # correo
            if not re.match(
                r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", rec["correo"]
            ):
                errors["correo"].append("Ingrese un correo valido")
            elif rec["correo"] not in self.correos:
                errors["correo"].append("Correo no esta registrado")

        elif page == 2:

            # codigo
            if not re.match(r"^[A-Za-z]{4}$", rec["codigo"]):
                errors["codigo"].append("Codigo de validacion son 4 letras")
            if rec["codigo"] != codigo:
                errors["codigo"].append("Codigo de validacion incorrecto")

            # contraseña
            if not re.match(r"^(?=.*[A-Z])(?=.*\d).{6,20}$", rec["password1"]):
                errors["password1"].append(
                    "Al menos 6 caracteres e incluir una mayuscula y un numero"
                )

            # validacion de contraseña
            if rec["password1"] != rec["password2"]:
                errors["password2"].append("Contraseñas no coinciden")

        return errors

    def mic(self, mic):

        # realizar todas las validaciones
        errors = {
            "placa1": [],
            "placa2": [],
            "placa3": [],
            "dni": [],
            "nombre": [],
            "celular": [],
            "contra1": [],
            "contra2": [],
            "contra3": [],
        }

        # nombre
        if len(mic["nombre"]) < 5:
            errors["nombre"].append("Nombre debe tener mínimo 5 letras")

        # celular: formato correcto (9 digitos)
        if not re.match(r"^[0-9]{9}$", mic["celular"]):
            errors["celular"].append("Ingrese un celular válido")

        # celular: no se esta duplicando con otro celular de la base de datos (no necesario revisar si hay error previo)
        else:
            self.cursor.execute(
                f"SELECT Celular FROM members WHERE Celular = '{mic["celular"]}' AND IdMember != (select IdMember FROM MEMBERS WHERE DocNum='{mic["dni"]}')"
            )
            if self.cursor.fetchone():
                errors["celular"].append("Celular ya está asociado con otra cuenta.")

        # placas
        for p in range(1, 4):

            _index = f"placa{p}"

            # dos letras y cuatro números, o tres letras y tres números, sin guion
            if mic[_index] and not re.match(r"^[A-Z][A-Z0-9]{2}\d{3}$", mic[_index]):
                errors[_index].append("Usar un formato válido")

            # no se esta duplicando con otra placa de la base de datos (no necesario revisar si hay error previo)
            else:
                self.cursor.execute(
                    f"SELECT Placa FROM placas WHERE Placa = '{mic[_index]}' AND IdMember_FK != 0 AND IdMember_FK != (select IdMember FROM MEMBERS WHERE DocNum='{mic["dni"]}')"
                )
                if self.cursor.fetchone():
                    errors[_index].append("Placa ya está asociada con otra cuenta.")

        # revisar solo si se ingreso algo en el campo de contraseña actual
        if len(mic["contra1"]) > 0:

            # contraseña actual
            self.cursor.execute(
                f"SELECT Password FROM members WHERE Correo = '{mic["correo"]}'"
            )
            _password = self.cursor.fetchone()[0]

            if _password != str(mic["contra1"]):
                errors["contra1"].append("Contraseña equivocada")

            # contraseña nueva
            elif not re.match(r"^(?=.*[A-Z])(?=.*\d).{6,20}$", mic["contra2"]):
                errors["contra2"].append(
                    "Mínimo 6 caracteres, incluir mayúscula y número"
                )

            # validacion de nueva contraseña
            elif mic["contra2"] != mic["contra3"]:
                errors["contra3"].append("Contraseñas no coinciden")

        return errors

    def mic_changes(self, user, placas, post):

        changes = ""

        # nombre ha cambiado
        if user[2] != post["nombre"]:
            changes += "Nombre actualizado. "

        # celular ha cambiado
        if user[5] != post["celular"]:
            changes += "Celular actualizado. "

        # alguna placa ha cambiado
        if sorted(
            [i for i in (post["placa1"], post["placa2"], post["placa3"]) if i]
        ) != sorted(placas):
            changes += "Placas actualizadas. "

        # contraseña ha cambiado
        if len(post["contra1"]) > 0 and str(post["contra2"]) != user[11]:
            changes += "Contraseña actualizada. "

        return changes

    def update_password(self, correo, password, db):
        cmd = f"UPDATE members SET Password = '{password}' WHERE Correo = '{correo}'"
        db.cursor.execute(cmd)
        db.conn.commit()
