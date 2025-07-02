def recipients(db_cursor):

    # 1. generate BIENVENIDA list (records with no previous BIENVENIDA email)
    cmd = """SELECT IdMember FROM members
                EXCEPT
                SELECT IdMember FROM (
                SELECT mensajes.IdMember_FK FROM mensajes JOIN mensajeContenidos ON mensajes.IdMensaje = mensajeContenidos.IdMensaje_FK
                WHERE IdTipoMensaje_FK = 12)
                JOIN members
                ON members.IdMember = IdMember_FK
                """

    db_cursor.execute(cmd)
    welcome_recipients = [i["IdMember"] for i in db_cursor.fetchall()]

    # 2. generate REGULAR list (records with previous REGULAR or BIENVENIDA email at least 1 month ago)
    cmd = """SELECT IdMember FROM members
                EXCEPT
	            SELECT IdMember_FK FROM mensajes
		            JOIN mensajeContenidos
		            ON IdMensaje = IdMensaje_FK
		            WHERE fecha >= DATETIME('now','localtime','-1 month')
			        AND (IdTipoMensaje_FK = 12 OR IdTipoMensaje_FK = 13)
                """
    # filter this list to avoid repeating with welcome list
    db_cursor.execute(cmd)
    regular_recipients = [
        i[0] for i in db_cursor.fetchall() if i[0] not in welcome_recipients
    ]

    return welcome_recipients, regular_recipients
