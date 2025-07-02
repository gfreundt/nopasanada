def get_records(db_cursor):

    # get records that require updating

    RECENTLY = 120  # hours
    updates = {}

    # records that have expiration dates within time thresh (unless updated recntly)
    updates["brevetes"] = get_records_brevete(db_cursor, thresh=30, HLA=RECENTLY)
    updates["soats"] = get_records_soats(db_cursor, thresh=15, HLA=RECENTLY)
    updates["revtecs"] = get_records_revtecs(db_cursor, thresh=30, HLA=RECENTLY)
    updates["sunarps"] = get_records_sunarps(db_cursor, thresh=180, HLA=RECENTLY)

    # records that are updated every time an email is sent (unless updated recently)
    updates["satimpCodigos"] = get_records_satimps(db_cursor, HLA=RECENTLY)
    updates["satmuls"] = get_records_satmuls(db_cursor, HLA=RECENTLY)
    updates["sutrans"] = get_records_sutrans(db_cursor, HLA=RECENTLY)
    updates["recvehic"] = get_records_recvehic(db_cursor, HLA=RECENTLY)
    updates["jneafils"] = get_records_jneafils(db_cursor, HLA=RECENTLY)
    updates["sunats"] = get_records_sunats(db_cursor, HLA=RECENTLY)

    # in development
    updates["jnemultas"] = get_records_jnemultas(db_cursor, HLA=RECENTLY)

    # return without any duplicates
    return {i: set(j) for i, j in updates.items()}


def get_records_brevete(db_cursor, thresh, HLA):
    # condition to update: will get email and (BREVETE expiring within thresh or no BREVETE in db) and only DNI as document and no attempt to update recently
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
    return [(i["IdMember_FK"], i["DocTipo"], i["DocNum"]) for i in db_cursor.fetchall()]


def get_records_soats(db_cursor, thresh, HLA):
    # condition to update: will get email and (SOAT expiring within thresh or no SOAT in db) and no attempt to update recently
    db_cursor.execute(
        f"""SELECT Placa FROM _necesitan_mensajes_placas
                WHERE Placa
                    NOT IN 
	                (SELECT PlacaValidate FROM soats
		                WHERE
                            FechaHasta >= datetime('now','localtime', '+{thresh} days'))
                            AND
                            Placa
                            NOT IN 
			                (SELECT Placa FROM placas
		                        WHERE LastUpdateSOAT >= datetime('now','localtime', '-{HLA} hours'))
            UNION
            SELECT Placa FROM _necesitan_alertas
                WHERE TipoAlerta = 'SOAT'
        """
    )
    return [i["Placa"] for i in db_cursor.fetchall()]


def get_records_revtecs(db_cursor, thresh, HLA):
    # condition to update: will get email and no attempt to update recently
    db_cursor.execute(
        f"""SELECT Placa FROM _necesitan_mensajes_placas
                WHERE
                    Placa
                    NOT IN
                    (SELECT PlacaValidate FROM revtecs
                        WHERE 
                        FechaHasta >= datetime('now','localtime', '+{thresh} days'))
                    AND
                    Placa
                    NOT IN
                    (SELECT Placa FROM placas
                        WHERE
                        LastUpdateRevtec >= datetime('now','localtime', '-{HLA} hours'))
            UNION
            SELECT Placa FROM _necesitan_alertas
                WHERE TipoAlerta = "REVTEC"
        """
    )
    return [i["Placa"] for i in db_cursor.fetchall()]


def get_records_satimps(db_cursor, HLA):
    # condition to update: will get email and no attempt to update recently
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
    return [(i["IdMember_FK"], i["DocTipo"], i["DocNum"]) for i in db_cursor.fetchall()]


def get_records_satmuls(db_cursor, HLA):
    # condition to update: will get email and SATMUL not updated recently
    db_cursor.execute(
        f"""SELECT Placa FROM _necesitan_mensajes_placas
                WHERE
                    Placa
                    NOT IN
                    (SELECT Placa FROM placas
                        WHERE LastUpdateSATMUL >= datetime('now', 'localtime', '-{HLA} hours'))
        """
    )
    return [i["Placa"] for i in db_cursor.fetchall()]


def get_records_sutrans(db_cursor, HLA):
    # condition to update: will get email and SUTRAN not updated recently
    db_cursor.execute(
        f"""SELECT Placa FROM _necesitan_mensajes_placas
                WHERE
                    Placa
                    NOT IN 
			        (SELECT Placa FROM placas
		                WHERE LastUpdateSUTRAN >= datetime('now','localtime', '-{HLA} hours'))
        """
    )
    return [i["Placa"] for i in db_cursor.fetchall()]


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
    return [(i["IdMember_FK"], i["DocTipo"], i["DocNum"]) for i in db_cursor.fetchall()]


def get_records_sunarps(db_cursor, thresh, HLA):
    # condition to update: will get email and last updated within time threshold
    db_cursor.execute(
        f""" SELECT Placa FROM _necesitan_mensajes_placas
                WHERE
                    Placa
                    NOT IN
			        (SELECT Placa FROM placas
		                WHERE LastUpdateSUNARP >= datetime('now','localtime', '-{thresh} days'))
        """
    )
    return [i["Placa"] for i in db_cursor.fetchall()]


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
    return [(i["IdMember_FK"], i["DocTipo"], i["DocNum"]) for i in db_cursor.fetchall()]


def get_records_jnemultas(db_cursor, HLA):
    # TODO: develop
    return []


def get_records_jneafils(db_cursor, HLA):
    # condition to update: will get email and no attempt to update in last 48 hours
    db_cursor.execute(
        f"""SELECT IdMember_FK, DocTipo, DocNum FROM _necesitan_mensajes_usuarios
                WHERE
                    IdMember_FK
                    NOT IN
                    (SELECT IdMember_FK FROM membersLastUpdate
            		    WHERE LastUpdateJNEAfil >= datetime('now','localtime', '-{HLA} hours'))
                    AND DocTipo = 'DNI'
        """
    )
    return [(i["IdMember_FK"], i["DocTipo"], i["DocNum"]) for i in db_cursor.fetchall()]
