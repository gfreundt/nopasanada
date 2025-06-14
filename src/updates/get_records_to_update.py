def get_records(db_cursor):

    # get records that require updating

    HOURS_LAST_ATTEMPT = 120

    updates = {}

    # records that have expiration dates within time thresh (in days)
    updates["brevetes"] = get_records_brevete(
        db_cursor, thresh=30, HLA=HOURS_LAST_ATTEMPT
    )
    updates["soats"] = get_records_soats(db_cursor, thresh=15, HLA=HOURS_LAST_ATTEMPT)
    updates["revtecs"] = get_records_revtecs(
        db_cursor, thresh=30, HLA=HOURS_LAST_ATTEMPT
    )

    # records that are updated every time an email is sent (unless updated in last 48 hours)
    updates["satimpCodigos"] = get_records_satimps(db_cursor, HLA=HOURS_LAST_ATTEMPT)
    updates["satmuls"] = get_records_satmuls(db_cursor, HLA=HOURS_LAST_ATTEMPT)
    updates["sutrans"] = get_records_sutrans(db_cursor, HLA=HOURS_LAST_ATTEMPT)
    updates["recvehic"] = get_records_recvehic(db_cursor, HLA=HOURS_LAST_ATTEMPT)

    # records that were last updated within fixed time threshold (in days)
    updates["sunarps"] = get_records_sunarps(
        db_cursor, thresh=180, HLA=HOURS_LAST_ATTEMPT
    )
    updates["sunats"] = get_records_sunats(db_cursor, HLA=HOURS_LAST_ATTEMPT)

    # in development
    updates["jnemultas"] = get_records_jnemultas(db_cursor, HLA=HOURS_LAST_ATTEMPT)
    updates["jneafils"] = get_records_jneafils(db_cursor, HLA=HOURS_LAST_ATTEMPT)

    # return without any duplicates
    return {i: set(j) for i, j in updates.items()}


def get_records_brevete(db_cursor, thresh, HLA):
    # condition to update: will get email and (BREVETE expiring within thresh or no BREVETE in db) and only DNI as document and no attempt to update in last 48 hours
    db_cursor.execute(
        f"""SELECT IdMember_FK, DocTipo, DocNum FROM _necesitan_mensajes_usuarios
                WHERE IdMember_FK
                    NOT IN 
                    (SELECT IdMember_FK FROM brevetes
                        WHERE
                            FechaHasta >= datetime('now','localtime', '+{thresh} days'))
                            AND
                            DocTipo = 'DNI' 
                            AND
                            IdMember_FK
                            NOT IN 
                            (SELECT IdMember_FK FROM membersLastUpdate
                                WHERE LastUpdateBrevete >= datetime('now','localtime', '-{HLA} hours'))
            UNION
            SELECT IdMember_FK, DocTipo, DocNum FROM _necesitan_alertas
                WHERE TipoAlerta = "BREVETE"
            """
    )
    return db_cursor.fetchall()


def get_records_soats(db_cursor, thresh, HLA):
    # condition to update: will get email and (SOAT expiring within thresh or no SOAT in db) and no attempt to update latelys
    db_cursor.execute(
        f"""SELECT * FROM _necesitan_mensajes_placas
                WHERE IdPlaca_FK
                    NOT IN 
	                (SELECT IdPlaca_FK FROM soats
		                WHERE
                            FechaHasta >= datetime('now','localtime', '+{thresh} days'))
                            AND
                            IdPlaca_FK
                            NOT IN 
			                (SELECT IdPlaca FROM placas
		                        WHERE LastUpdateSOAT >= datetime('now','localtime', '-{HLA} hours'))
            UNION
            SELECT IdPlaca_FK, Placa FROM _necesitan_alertas
                WHERE TipoAlerta = 'SOAT'
        """
    )
    return db_cursor.fetchall()


def get_records_revtecs(db_cursor, thresh, HLA):
    # condition to update: will get email and no attempt to update lately
    db_cursor.execute(
        f"""SELECT * FROM _necesitan_mensajes_placas
                WHERE
                    IdPlaca_FK
                    NOT IN
                    (SELECT IdPlaca_FK FROM revtecs
                        WHERE 
                        FechaHasta >= datetime('now','localtime', '+{thresh} days'))
                    AND
                    IdPlaca_FK
                    NOT IN
                    (SELECT IdPlaca FROM placas
                        WHERE
                        LastUpdateRevtec >= datetime('now','localtime', '-{HLA} hours'))
            UNION
            SELECT IdPlaca_FK, Placa FROM _necesitan_alertas
                WHERE TipoAlerta = "REVTEC"
        """
    )
    return db_cursor.fetchall()


def get_records_satimps(db_cursor, HLA):
    # condition to update: will get email and no attempt to update lately
    db_cursor.execute(
        f"""SELECT IdMember_FK, DocTipo, DocNum FROM _necesitan_mensajes_usuarios
                WHERE
                    IdMember_FK
                    NOT IN
			        (SELECT IdMember_FK FROM membersLastUpdate
		                WHERE LastUpdateImpSAT >= datetime('now','localtime', '-{HLA} hours'))
            UNION
            SELECT IdMember_FK, DocTipo, DocNum FROM _necesitan_alertas
                WHERE TipoAlerta = "SATIMP"
        """
    )
    return db_cursor.fetchall()


def get_records_satmuls(db_cursor, HLA):
    # condition to update: will get email and SATMUL not updated lately
    db_cursor.execute(
        f"""SELECT * FROM _necesitan_mensajes_placas
                WHERE
                    IdPlaca_FK
                    NOT IN
                    (SELECT IdPlaca FROM placas
                        WHERE LastUpdateSATMUL >= datetime('now', 'localtime', '-{HLA} hours'))
        """
    )
    return db_cursor.fetchall()


def get_records_sutrans(db_cursor, HLA):
    # condition to update: will get email and SUTRAN not updated in last 48 hours
    db_cursor.execute(
        f"""SELECT * FROM _necesitan_mensajes_placas
                WHERE
                    IdPlaca_FK
                    NOT IN 
			        (SELECT IdPlaca FROM placas
		                WHERE LastUpdateSUTRAN >= datetime('now','localtime', '-{HLA} hours'))
        """
    )
    return db_cursor.fetchall()


def get_records_recvehic(db_cursor, HLA):
    # condition to update: will get email and no attempt to update in last 48 hours
    db_cursor.execute(
        f"""SELECT IdMember_FK, DocTipo, DocNum FROM _necesitan_mensajes_usuarios
                WHERE
                    IdMember_FK
                    NOT IN
                    (SELECT IdMember_FK FROM membersLastUpdate
            		    WHERE LastUpdateRecord >= datetime('now','localtime', '-{HLA} hours'))
                    AND DocTipo = 'DNI'
        """
    )

    return db_cursor.fetchall()


def get_records_sunarps(db_cursor, thresh, HLA):
    # condition to update: will get email and last updated within time threshold
    db_cursor.execute(
        f""" SELECT * FROM _necesitan_mensajes_placas
                WHERE
                    IdPlaca_FK
                    NOT IN
			        (SELECT IdPlaca FROM placas
		                WHERE LastUpdateSUNARP >= datetime('now','localtime', '-{thresh} days'))
        """
    )
    return db_cursor.fetchall()


def get_records_sunats(db_cursor, HLA):
    # condition to update: will get email and no attempt to update in last 48 hours
    db_cursor.execute(
        f"""SELECT IdMember_FK, DocTipo, DocNum FROM _necesitan_mensajes_usuarios
                WHERE
                    IdMember_FK
                    NOT IN
                    (SELECT IdMember_FK FROM membersLastUpdate
            		    WHERE LastUpdateSUNAT >= datetime('now','localtime', '-{HLA} hours'))
                    AND DocTipo = 'DNI'
        """
    )

    return db_cursor.fetchall()


def get_records_jnemultas(db_cursor, HLA):
    # TODO: develop
    return []


def get_records_jneafils(db_cursor, HLA):
    # TODO: develop
    return []


def get_new_members(db_cursor, all_updates):
    # docs
    cmd = [
        """ SELECT IdMember, DocTipo, DocNum FROM members
                EXCEPT
                SELECT IdMember, DocTipo, DocNum FROM (
                SELECT mensajes.IdMember_FK FROM mensajes JOIN mensajeContenidos ON mensajes.IdMensaje = mensajeContenidos.IdMensaje_FK
                WHERE IdTipoMensaje_FK = 12)
                JOIN members
                ON members.IdMember = IdMember_FK
        """
    ]

    # placas
    cmd.append(
        """ SELECT IdPlaca, Placa FROM placas
                JOIN (SELECT IdMember, DocTipo, DocNum FROM members
                EXCEPT
                SELECT IdMember, DocTipo, DocNum FROM (
                SELECT mensajes.IdMember_FK FROM mensajes JOIN mensajeContenidos ON mensajes.IdMensaje = mensajeContenidos.IdMensaje_FK
                WHERE IdTipoMensaje_FK = 12)
                JOIN members
                ON members.IdMember = IdMember_FK)
                ON placas.IdMember_FK = IdMember
        """
    )

    #
    for i in (0, 1):
        db_cursor.execute(cmd[i])
        _result = db_cursor.fetchall()
        db_cursor.execute(f"SELECT * FROM '@tableInfo' WHERE dataRequired = {i+1}")
        for table in db_cursor.fetchall():
            all_updates[table[1]] += _result

    # brevetes, satimps
    for table in [("brevetes", "BREVETE"), ("satimpCodigos", "SATIMP")]:
        cmd = f"""select members.IdMember, DocTipo, DocNum from members 
                       JOIN (select * from _alertaEnviar WHERE TipoAlerta = '{table[1]}')
                       ON IdMember = IdMember_FK"""
        db_cursor.execute(cmd)
        all_updates[table[0]] += db_cursor.fetchall()

    # soats, revtecs
    for table in [("soats", "SOAT"), ("revtecs", "REVTEC")]:
        cmd = f"""select placas.IdPlaca, placas.Placa from placas 
                       JOIN (select * from _alertaEnviar WHERE TipoAlerta = '{table[1]}')
                       ON IdPlaca = IdPlaca_FK"""
        db_cursor.execute(cmd)
        all_updates[table[0]] += db_cursor.fetchall()

    return all_updates
