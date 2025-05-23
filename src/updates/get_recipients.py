def need_message(db_cursor):
    """creates two tables (docs and placas) with all the members that require a monthly email
    which are later used as reference for determining which records to update"""

    cmd = """
            -- Crear tabla temporal primaria de usuarios que necesitan mensajes
            DROP TABLE IF EXISTS _necesitan_mensajes_usuarios;
            CREATE TABLE _necesitan_mensajes_usuarios (IdMember_FK, DocTipo, DocNum, Tipo);

            -- Incluir usuarios que han recibido ultimo mensaje regular o de bienvenida hace mas de un mes (mensaje regular)
            INSERT INTO _necesitan_mensajes_usuarios (IdMember_FK, DocTipo, DocNum, Tipo)
                SELECT IdMember, DocTipo, DocNum, "R" from members 
                WHERE IdMember NOT IN (
                    SELECT IdMember_FK FROM mensajes 
                        WHERE FechaEnvio >= datetime('now','localtime', '-1 month'));
                        
            -- Cambiar flag de mensaje de regular a bienvenida si nunca antes han recibido mensajes
            UPDATE _necesitan_mensajes_usuarios SET Tipo = "B"
                WHERE IdMember_FK in (
                    SELECT IdMember_FK FROM mensajes
                        GROUP BY IdMember_FK
                        HAVING count(*) = 1);		
                        
            -- Crear tabla temporal secundaria que lista las placas de usarios que necesitan mensajes
            DROP TABLE IF EXISTS _necesitan_mensajes_placas;
            CREATE TABLE _necesitan_mensajes_placas (IdPlaca_FK, Placa);
            INSERT INTO _necesitan_mensajes_placas (IdPlaca_FK, Placa) select idplaca, placa from placas where IdMember_FK IN (SELECT IdMember_FK from _necesitan_mensajes_usuarios)
            """

    db_cursor.executescript(cmd)


def need_alert(db_cursor):
    """creates one table with all the members/placas that require an alert
    which is later used as reference for determining which records to update"""

    cmd = """   
                -- Crear tabla temporal de usuarios que necesitan alertas
                DROP TABLE IF EXISTS _necesitan_alertas;
                CREATE TABLE _necesitan_alertas (IdMember_FK, DocTipo, DocNum, IdPlaca_FK, Placa, FechaHasta, TipoAlerta, Vencido);

                --- Incluir usuarios/placas con documentos en fecha de vencimiento en x dias exactos o 0-3 dias vencido.
                INSERT INTO _necesitan_alertas (IdPlaca_FK, FechaHasta, TipoAlerta, Placa, IdMember_FK)
                    SELECT idplaca_FK, FechaHasta, "SOAT", (SELECT Placa FROM placas WHERE IdPlaca = IdPlaca_FK), (SELECT IdMember_FK FROM placas WHERE IdPlaca = IdPlaca_FK) FROM soats
                        WHERE 	DATE('now', 'localtime', '+5 days') = FechaHasta
                        OR 		(DATE('now', 'localtime', '0 days') >= FechaHasta
                                    AND DATE('now', 'localtime', '-3 days') <= FechaHasta)
                    UNION
                    SELECT idplaca_FK, FechaHasta, "REVTEC", (SELECT Placa FROM placas WHERE IdPlaca = IdPlaca_FK), (SELECT IdMember_FK FROM placas WHERE IdPlaca = IdPlaca_FK) FROM revtecs
                        WHERE 	DATE('now', 'localtime', '+15 days')= FechaHasta
                        OR 		DATE('now', 'localtime', '+7 days')= FechaHasta
                        OR 		(DATE('now', 'localtime', '0 days') >= FechaHasta
                                    AND DATE('now', 'localtime', '-3 days') <= FechaHasta);
                    
                INSERT INTO _necesitan_alertas (IdMember_FK, FechaHasta, TipoAlerta, DocTipo, DocNum)
                    SELECT IdMember_FK, FechaHasta, "BREVETE", (SELECT DocTipo FROM members WHERE IdMember = IdMember_FK), (SELECT DocNum FROM members WHERE IdMember = IdMember_FK) FROM brevetes
                        WHERE 	DATE('now', 'localtime', '+30 days') = FechaHasta
                        OR 		DATE('now', 'localtime', '+10 days')= FechaHasta
                        OR 		(DATE('now', 'localtime', '0 days') >= FechaHasta
                                    AND DATE('now', 'localtime', '-3 days') <= FechaHasta)
                    UNION
                    SELECT IdMember_FK, FechaHasta, "SATIMP", (SELECT DocTipo FROM members WHERE IdMember = IdMember_FK), (SELECT DocNum FROM members WHERE IdMember = IdMember_FK) FROM satimpDeudas 
                        JOIN
                            (SELECT * FROM satimpCodigos)
                        ON IdCodigo_FK = IdCodigo
                        WHERE DATE('now', 'localtime', '+10 days') = FechaHasta
                        OR 		(DATE('now', 'localtime', '0 days') >= FechaHasta
                                    AND DATE('now', 'localtime', '-3 days') <= FechaHasta);
                
                --- Poner todos los flags en 0 (no vencido) y cambiar los que estan vencidos a 1
                UPDATE _necesitan_alertas SET Vencido = 0;
                UPDATE _necesitan_alertas SET Vencido = 1 WHERE DATE('now', 'localtime') >= FechaHasta;
            """

    db_cursor.executescript(cmd)
