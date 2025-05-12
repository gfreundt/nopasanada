def get_alert_list(db_cursor):

    # create list of members that require an alert if items expiring within parameters
    cmd = f"""  DROP TABLE IF EXISTS _alertaEnviar;
                CREATE TABLE _alertaEnviar (CodMember, NombreCompleto, Celular, Placa, FechaHasta, TipoAlerta, Correo, IdMember_FK, IdPlaca_FK);

                INSERT INTO _alertaEnviar (CodMember, NombreCompleto, Celular, Placa, FechaHasta, TipoAlerta, Correo, IdPlaca_FK)
                SELECT CodMember, NombreCompleto, Celular, Placa, FechaHasta, TipoAlerta, Correo, IdPlaca FROM members
                JOIN (
                    SELECT * FROM placas 
                    JOIN (
                    SELECT idplaca_FK, FechaHasta, "SOAT" AS TipoAlerta FROM soats WHERE DATE('now', 'localtime', '5 days') = FechaHasta OR DATE('now', 'localtime', '0 days') = FechaHasta
                    UNION
                    SELECT idplaca_FK, FechaHasta, "REVTEC" FROM revtecs WHERE DATE('now', 'localtime', '10 days')= FechaHasta OR DATE('now', 'localtime', '0 days')= FechaHasta)
                    ON idplaca = IdPlaca_FK)
                ON IdMember = IdMember_FK;

                INSERT INTO _alertaEnviar (CodMember, NombreCompleto, FechaHasta, TipoAlerta, Correo, IdMember_FK)
                SELECT CodMember, NombreCompleto, FechaHasta, TipoAlerta, Correo, IdMember from members 
                    JOIN (
                        SELECT IdMember_FK, FechaHasta, "BREVETE" AS TipoAlerta FROM brevetes WHERE DATE('now', 'localtime', '30 days') = FechaHasta OR DATE('now', 'localtime', '0 days')= FechaHasta
                    UNION
                        SELECT IdMember_FK, FechaHasta, "SATIMP" AS TipoAlerta FROM satimpDeudas 
                        JOIN
                        (SELECT * FROM satimpCodigos)
                        ON IdCodigo_FK = IdCodigo
                        WHERE DATE('now', 'localtime', '10 days') = FechaHasta OR DATE('now', 'localtime', '0 days') = FechaHasta)
                ON IdMember = IdMember_FK;"""

    db_cursor.executescript(cmd)

    db_cursor.execute("SELECT * FROM _alertaEnviar")
    return db_cursor.fetchall()
