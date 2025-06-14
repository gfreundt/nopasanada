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
                errors["nombre"].append("Nombre debe tener mínimo 5 dígitos")

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

            # validacion de constraseña
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

            # validacion de constraseña
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
        }

        # nombre
        # if len(mic["nombre"]) < 6:
        #     errors["nombre"].append("Nombre debe tener minimo 5 digitos")

        # dni
        # if not re.match(r"^[0-9]{8}$", mic["dni"]):
        #     errors["dni"].append("DNI solamente debe tener 8 digitos")
        # if mic["dni"] in self.dnis:
        #     errors["dni"].append("DNI ya esta registado")

        # celular
        if not re.match(r"^[0-9]{9}$", mic["celular"]):
            errors["celular"].append("Ingrese un celular valido")

        return errors

    def mic_changes(self, user, placas, post):

        _c = [
            user[2] != post["nombre"],
            user[4] != post["dni"],
            user[5] != post["celular"],
            sorted([i for i in (post["placa1"], post["placa2"], post["placa3"]) if i])
            != sorted(placas),
        ]

        return any(_c)

    def update_password(self, correo, password, db):
        cmd = f"UPDATE members SET Password = '{password}' WHERE Correo = '{correo}'"
        db.cursor.execute(cmd)
        db.conn.commit()
