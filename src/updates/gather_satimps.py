from datetime import datetime as dt

# local imports
from src.scrapers import scrape_satimp


def gather(db_cursor, dash, update_data):

    CARD = 3

    # log first action
    dash.logging(
        card=CARD,
        title=f"Impuestos SAT [{len(update_data)}]",
        status=1,
        progress=0,
        text="Inicializando",
        lastUpdate="Actualizado:",
    )

    # iterate on all records that require updating and get scraper results
    for counter, (id_member, doc_tipo, doc_num) in enumerate(update_data, start=1):

        retry_attempts = 0
        # loop to catch scraper errors and retry limited times
        while retry_attempts < 3:
            try:
                # log action
                dash.logging(card=CARD, text=f"Procesando: {doc_tipo} {doc_num}")

                # send request to scraper
                new_records = scrape_satimp.browser(doc_tipo=doc_tipo, doc_num=doc_num)

                # if no error in scrape, delete any prior satimp data of this member in both tables
                db_cursor.executescript(
                    f"""DELETE FROM satimpDeudas WHERE IdCodigo_FK =
                          (SELECT IdCodigo FROM satimpCodigos WHERE IdMember_FK = '{id_member}');
                        
                        DELETE FROM satimpCodigos WHERE IdMember_FK = '{id_member}'"""
                )

                _now = dt.now().strftime("%Y-%m-%d")

                for new_record in new_records:

                    # add foreign key and current date to scraper response
                    _values = [
                        id_member,
                        new_record["codigo"],
                        _now,
                    ]

                    # insert gathered record of member
                    db_cursor.execute(
                        f"INSERT INTO satimpCodigos (IdMember_FK, Codigo, LastUpdate) VALUES {tuple(_values)}"
                    )

                    # get id created to use as foreign id in satimpDeudas table
                    _c = new_record["codigo"]
                    db_cursor.execute(
                        f"SELECT * FROM satimpCodigos WHERE Codigo = '{_c}'"
                    )
                    _id = db_cursor.fetchone()[0]

                    # loop through all deudas for new id created (if any)
                    for deuda in new_record["deudas"]:

                        # add new foreign key to response and add to database
                        _values = [_id] + list(deuda.values())
                        db_cursor.execute(
                            f"INSERT INTO satimpDeudas VALUES {tuple(_values)}"
                        )
                        dash.logging(
                            action=f"[ SATIMPS ] {"|".join([str(i) for i in _values])}"
                        )

                # update memberLastUpdate table with last update information
                db_cursor.execute(
                    f"UPDATE membersLastUpdate SET LastUpdateImpSAT = '{_now}' WHERE IdMember_FK = '{id_member}'"
                )

                # update dashboard with progress and last update timestamp
                dash.logging(
                    card=CARD,
                    status=1,
                    progress=int((counter / len(update_data)) * 100),
                    lastUpdate=dt.now(),
                )

                # next record
                break

            except KeyboardInterrupt:
                quit()

            # except Exception:
            #     retry_attempts += 1
            #     dash.logging(
            #         card=CARD,
            #         status=2,
            #         text=f"|ADVERTENCIA| Reintentando [{retry_attempts}/3]: {doc_tipo} {doc_num}",
            #     )

        # if code gets here, means scraping has encountred three consecutive errors, skip record
        dash.logging(
            card=CARD, msg=f"|ERROR| No se pudo procesar {doc_tipo} {doc_num}."
        )

    # log last action
    dash.logging(
        card=CARD,
        title="Impuestos SAT",
        progress=100,
        status=3,
        text="Inactivo",
        lastUpdate=dt.now(),
    )
