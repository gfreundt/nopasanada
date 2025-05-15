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


def need_alert(db_cursor):
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
