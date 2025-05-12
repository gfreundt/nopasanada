def update_table(db_cursor):
    """Creates table with all members with SOAT, REVTEC, SUTRAN, SATMUL, BREVETE or SATIMP
    expired or expiring within 30 days."""

    _cmd = f""" DROP TABLE IF EXISTS _expira30dias;
                CREATE TABLE _expira30dias (IdMember, Placa, FechaHasta, TipoAlerta, Vencido);

                -- Incluir usuarios que tienen multas vigentes o documentos por vencer dentro de 30 dias o ya vencidos
                INSERT INTO _expira30dias (IdMember, FechaHasta, TipoAlerta)
                    SELECT IdMember, FechaHasta, TipoAlerta from members 
                        JOIN (
                            SELECT IdMember_FK, FechaHasta, "BREVETE" AS TipoAlerta FROM brevetes 
                                WHERE DATE('now', 'localtime', '30 days') >= FechaHasta OR DATE('now', 'localtime', '30 days')= FechaHasta OR DATE('now', 'localtime', '0 days')= FechaHasta
                                UNION
                            SELECT IdMember_FK, FechaHasta, "SATIMP" AS TipoAlerta FROM satimpDeudas 
                                JOIN
                            (SELECT * FROM satimpCodigos)
                                ON IdCodigo_FK = IdCodigo
                            WHERE DATE('now', 'localtime', '30 days') >= FechaHasta
                                UNION
                            SELECT IdMember_FK, "", "MTCPAPELETA" FROM mtcPapeletas)
                        ON IdMember = IdMember_FK;


                -- Incluir placas que tienen multas vigentes o documentos por vencer dentro de 30 dias o ya vencidos
                INSERT INTO _expira30dias (IdMember,  Placa, FechaHasta, TipoAlerta)
                    SELECT IdMember, Placa, FechaHasta, TipoAlerta FROM members
                        JOIN (
                            SELECT * FROM placas 
                                JOIN (
                            SELECT idplaca_FK, FechaHasta, "SOAT" AS TipoAlerta FROM soats
                                WHERE DATE('now', 'localtime', '+30 days') >= FechaHasta
                                UNION
                            SELECT idplaca_FK, FechaHasta, "REVTEC" FROM revtecs
                                WHERE DATE('now', 'localtime', '+30 days') >= FechaHasta
                                UNION 
                            SELECT idplaca_FK, "", "SUTRAN" FROM sutrans
                                UNION 
                            SELECT idplaca_FK, "", "SATMUL" FROM satmuls)
                                ON idplaca = IdPlaca_FK)
                        ON IdMember = IdMember_FK;

                                    
                -- Crear un flag de si esta por vencer o ya vencio     
                UPDATE _expira30dias SET Vencido = 0;
                UPDATE _expira30dias SET Vencido = 1 WHERE FechaHasta < DATE('now', 'localtime');
            """
    db_cursor.executescript(_cmd)
