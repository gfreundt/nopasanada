def need_message(db_cursor):
    """creates two tables (docs and placas) with all the members that require a monthly email
    which are later used as reference for determining which records to update"""

    cmd = """
                -- Borrar todo el contenido de la tabla
                DELETE FROM _necesitan_mensajes_usuarios;

                -- Incluir usuarios que han recibido ultimo mensaje regular o de bienvenida hace mas de un mes (mensaje regular) o flag forzado
                INSERT INTO _necesitan_mensajes_usuarios (IdMember_FK, DocTipo, DocNum, Tipo)
                    SELECT IdMember, DocTipo, DocNum, "R" from members 
                    WHERE
                        IdMember NOT IN (
                            SELECT IdMember_FK FROM mensajes 
                                WHERE FechaEnvio >= datetime('now','localtime', '-1 month'))
                        OR
                        ForceMsg = 1;
                            
                -- Cambiar flag de mensaje de regular a bienvenida si nunca antes han recibido mensajes
                UPDATE _necesitan_mensajes_usuarios SET Tipo = "B"
                    WHERE IdMember_FK in (
                        SELECT IdMember_FK FROM mensajes
                            GROUP BY IdMember_FK
                            HAVING count(*) = 1);		
                            
                -- Crear tabla temporal secundaria que lista las placas de usarios que necesitan mensajes
                DELETE FROM _necesitan_mensajes_placas;

                INSERT INTO _necesitan_mensajes_placas (Placa)
                    SELECT Placa FROM placas
                        WHERE IdMember_FK IN
                            (SELECT IdMember_FK FROM _necesitan_mensajes_usuarios);
            """

    db_cursor.executescript(cmd)


def need_alert(db_cursor):
    """creates one table with all the members/placas that require an alert
    which is later used as reference for determining which records to update"""

    cmd = """   
                -- Borrar todo el contenido de la tabla
                DELETE FROM _necesitan_alertas;

                --- Incluir usuarios/placas con documentos en fecha de vencimiento en x dias exactos o 0-3 dias vencido.
                INSERT INTO _necesitan_alertas (FechaHasta, TipoAlerta, Placa, IdMember_FK)
                    SELECT FechaHasta, "SOAT", PlacaValidate, (SELECT IdMember_FK FROM placas WHERE Placa = PlacaValidate) FROM soats
                        WHERE 	DATE('now', 'localtime', '+5 days') = FechaHasta
                        OR 		(DATE('now', 'localtime', '0 days') >= FechaHasta
                                    AND DATE('now', 'localtime', '-3 days') <= FechaHasta)
                    UNION
                    SELECT FechaHasta, "REVTEC", PlacaValidate, (SELECT IdMember_FK FROM placas WHERE Placa = PlacaValidate) FROM revtecs
                        WHERE 	DATE('now', 'localtime', '+15 days') = FechaHasta
                        OR 		DATE('now', 'localtime', '+7 days') = FechaHasta
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

                --- Eliminar de alertas los registros que no esten asociados a un usuario.
                DELETE FROM _necesitan_alertas WHERE IdMember_FK = 0;
                
                --- Poner todos los flags en 0 (no vencido) y cambiar los que estan vencidos a 1
                UPDATE _necesitan_alertas SET Vencido = 0;
                UPDATE _necesitan_alertas SET Vencido = 1 WHERE DATE('now', 'localtime') >= FechaHasta;
            """

    db_cursor.executescript(cmd)
