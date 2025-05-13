def get_records(db_cursor):

    # creates temporary tables with all members/placas that haven't received an email in 30+ days
    create_tables_need_messages(db_cursor)

    # create dictionary with all tables as keys and empty list as value
    db_cursor.execute("SELECT * FROM '@tableInfo'")
    _data = db_cursor.fetchall()
    all_updates = {i[1]: [] for i in _data}
    nice_names = [i[2] for i in _data]

    # get records that require updating

    # records that have expiration dates within time threshold (in days)
    all_updates["brevetes"] = get_records_brevete(db_cursor, threshold=30)
    all_updates["soats"] = get_records_soats(db_cursor, threshold=15)
    all_updates["revtecs"] = get_records_revtecs(db_cursor, threshold=30)

    # records that are updated every time an email is sent (unless updated in last 48 hours)
    all_updates["satimpCodigos"] = get_records_satimps(db_cursor)
    all_updates["satmuls"] = get_records_satmuls(db_cursor)
    all_updates["sutrans"] = get_records_sutrans(db_cursor)
    all_updates["recvehic"] = get_records_recvehic(db_cursor)

    # records that were last updated within fixed time threshold (in days)
    all_updates["sunarps"] = get_records_sunarps(db_cursor, threshold=180)
    all_updates["sunats"] = get_records_sunats(db_cursor, threshold=90)

    # get all new members (no welcome email) and include in list of records to update
    # TODO: is this really necessary??? aren't they included in step 1??
    # all_updates = get_new_members(db_cursor, all_updates)

    # eliminate any duplicates
    all_updates = {i: set(j) for i, j in all_updates.items()}

    return all_updates


def create_tables_need_messages(db_cursor):
    """creates two tables (docs and placas) with all the members that require a monthly email
    which are later used as reference for determining which records to update"""

    # cmd = """   DROP TABLE IF EXISTS _necesitan_mensajes_usuarios;
    #             CREATE TABLE _necesitan_mensajes_usuarios (IdMember_FK, DocTipo, DocNum, Tipo);
    #             INSERT INTO _necesitan_mensajes_usuarios (IdMember_FK, DocTipo, DocNum, Tipo) SELECT IdMember, DocTipo, DocNum FROM members JOIN (
    #                 SELECT IdMember AS x FROM members
    #                 EXCEPT
    #                     SELECT IdMember_FK FROM mensajes
    # 	                JOIN mensajeContenidos
    # 	                ON IdMensaje = IdMensaje_FK
    # 	            WHERE Fecha >= datetime('now','localtime', '-1 month')
    # 		        AND (IdTipoMensaje_FK = 12 OR IdTipoMensaje_FK = 13)
    #             )
    #                 ON members.IdMember = x;

    #             DROP TABLE IF EXISTS _necesitan_mensajes_placas;
    #             CREATE TABLE _necesitan_mensajes_placas (IdPlaca_FK, Placa);
    #             INSERT INTO _necesitan_mensajes_placas (IdPlaca_FK, Placa) SELECT IdPlaca, Placa FROM placas
    #                 JOIN (_necesitan_mensajes_usuarios)
    #                 ON placas.IdMember_FK = _necesitan_mensajes_usuarios.IdMember_FK"""

    cmd = """
            -- Crear tabla temporal primaria de usuarios que necesitan mensajes
            DROP TABLE IF EXISTS _necesitan_mensajes_usuarios;
            CREATE TABLE _necesitan_mensajes_usuarios (IdMember_FK, DocTipo, DocNum, Tipo);

            -- Incluir usuarios que han recibido ultimo mensaje regular o de bienvenida hace mas de un mes (mensaje regular)
            INSERT INTO _necesitan_mensajes_usuarios (IdMember_FK, DocTipo, DocNum, Tipo)
                SELECT IdMember, DocTipo, DocNum, "R" from members 
                WHERE IdMember NOT IN (
                    SELECT IdMember_FK FROM mensajes 
                        WHERE FechaEnvio >= datetime('now','localtime', '-1 month')
                        AND (IdTipoMensaje_FK = 12 OR IdTipoMensaje_FK = 13));
                        
            -- Cambiar flag de mensaje de regular a bienvenida si nunca antes han recibido mensajes		
            UPDATE _necesitan_mensajes_usuarios SET Tipo = "B"
                WHERE IdMember_FK NOT IN (
                    SELECT IdMember_FK FROM mensajes
                    WHERE (IdTipoMensaje_FK = 12 OR IdTipoMensaje_FK = 13));
                        
            -- Crear tabla temporal secundaria que lista las placas de usarios que necesitan mensajes
            DROP TABLE IF EXISTS _necesitan_mensajes_placas;
            CREATE TABLE _necesitan_mensajes_placas (IdPlaca_FK, Placa);
            INSERT INTO _necesitan_mensajes_placas (IdPlaca_FK, Placa) select idplaca, placa from placas where IdMember_FK IN (SELECT IdMember_FK from _necesitan_mensajes_usuarios)

            """

    db_cursor.executescript(cmd)


def get_records_brevete(db_cursor, threshold):
    # condition to update: will get email and (BREVETE expiring within threshold or no BREVETE in db) and only DNI as document and no attempt to update in last 48 hours
    db_cursor.execute(
        f""" SELECT IdMember_FK, DocTipo, DocNum FROM _necesitan_mensajes_usuarios
                WHERE IdMember_FK
                    NOT IN 
	                (SELECT IdMember_FK FROM brevetes
		                WHERE
                            FechaHasta >= datetime('now','localtime', '+{threshold} days'))
                            AND
                            DocTipo = 'DNI' 
                            AND
                            IdMember_FK
                            NOT IN 
			                (SELECT IdMember_FK FROM membersLastUpdate
		                        WHERE LastUpdateBrevete >= datetime('now','localtime', '-120 hours'))
             """
    )
    return db_cursor.fetchall()


def get_records_soats(db_cursor, threshold):
    # condition to update: will get email and (SOAT expiring within threshold or no SOAT in db) and no attempt to update in last 48 hours
    db_cursor.execute(
        f""" SELECT * FROM _necesitan_mensajes_placas
                WHERE IdPlaca_FK
                    NOT IN 
	                (SELECT IdPlaca_FK FROM soats
		                WHERE
                            FechaHasta >= datetime('now','localtime', '+{threshold} days'))
                            AND
                            IdPlaca_FK
                            NOT IN 
			                (SELECT IdPlaca FROM placas
		                        WHERE LastUpdateSOAT >= datetime('now','localtime', '-48 hours'))
        """
    )
    return db_cursor.fetchall()


def get_records_revtecs(db_cursor, threshold):
    # condition to update: will get email and no attempt to update in last 48 hours
    db_cursor.execute(
        f""" SELECT * FROM _necesitan_mensajes_placas
                WHERE
                    IdPlaca_FK
                    NOT IN
                    (SELECT IdPlaca_FK FROM revtecs
                        WHERE 
                        FechaHasta >= datetime('now','localtime', '+{threshold} days'))
                    AND
                    IdPlaca_FK
                    NOT IN
                    (SELECT IdPlaca FROM placas
                        WHERE
                        LastUpdateRevtec >= datetime('now','localtime', '-120 hours'))
        """
    )
    return db_cursor.fetchall()


def get_records_satimps(db_cursor):
    # condition to update: will get email and no attempt to update in last 48 hours
    db_cursor.execute(
        """ SELECT IdMember_FK, DocTipo, DocNum FROM _necesitan_mensajes_usuarios
                WHERE
                    IdMember_FK
                    NOT IN
			        (SELECT IdMember_FK FROM membersLastUpdate
		                WHERE LastUpdateImpSAT >= datetime('now','localtime', '-120 hours'))
        """
    )
    return db_cursor.fetchall()


def get_records_satmuls(db_cursor):
    # condition to update: will get email and SATMUL not updated in last 48 hours
    db_cursor.execute(
        """ SELECT * FROM _necesitan_mensajes_placas
                WHERE
                    IdPlaca_FK
                    NOT IN
                    (SELECT IdPlaca FROM placas
                        WHERE LastUpdateSATMUL >= datetime('now', 'localtime', '-24 hours'))
        """
    )
    return db_cursor.fetchall()


def get_records_sutrans(db_cursor):
    # condition to update: will get email and SUTRAN not updated in last 48 hours
    db_cursor.execute(
        """ SELECT * FROM _necesitan_mensajes_placas
                WHERE
                    IdPlaca_FK
                    NOT IN 
			        (SELECT IdPlaca FROM placas
		                WHERE LastUpdateSUTRAN >= datetime('now','localtime', '-120 hours'))
        """
    )
    return db_cursor.fetchall()


def get_records_recvehic(db_cursor):
    # condition to update: will get email and no attempt to update in last 48 hours
    db_cursor.execute(
        """ SELECT IdMember_FK, DocTipo, DocNum FROM _necesitan_mensajes_usuarios
                WHERE
                    IdMember_FK
                    NOT IN
                    (SELECT IdMember_FK FROM membersLastUpdate
            		    WHERE LastUpdateRecord >= datetime('now','localtime', '-120 hours'))
                    AND DocTipo = 'DNI'
        """
    )

    return db_cursor.fetchall()


def get_records_sunarps(db_cursor, threshold):
    # condition to update: will get email and last updated within time threshold
    db_cursor.execute(
        f""" SELECT * FROM _necesitan_mensajes_placas
                WHERE
                    IdPlaca_FK
                    NOT IN
			        (SELECT IdPlaca FROM placas
		                WHERE LastUpdateSUNARP >= datetime('now','localtime', '-{threshold} days'))
        """
    )
    return db_cursor.fetchall()


def get_records_sunats(db_cursor, threshold):
    # condition to update: will get email and last updated within time threshold
    db_cursor.execute(
        f""" SELECT * FROM _necesitan_mensajes_placas
                WHERE
                    IdPlaca_FK
                    NOT IN
                    (SELECT IdPlaca_FK FROM sunats
                        WHERE LastUpdate >= datetime('now','localtime', '-{threshold} days'))
        """
    )
    return db_cursor.fetchall()


def get_new_members(db_cursor, all_updates):
    # docs
    cmd = [
        """SELECT IdMember, DocTipo, DocNum FROM members
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
        """SELECT IdPlaca, Placa FROM placas
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
