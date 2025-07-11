from datetime import datetime as dt

# local imports
from src.scrapers import scrape_recvehic


def gather(db_cursor, db_conn, dash, update_data):

    CARD = 1

    # log first action
    dash.logging(
        card=CARD,
        title=f"Record Conductor [{len(update_data)}]",
        status=1,
        progress=0,
        text="Inicializando",
        lastUpdate="Actualizado:",
    )

    # iterate on all records that require updating and get scraper results
    for counter, (id_member, doc_tipo, doc_num) in enumerate(update_data, start=1):

        # records are only available for members with DNI
        if doc_tipo != "DNI":
            continue

        retry_attempts = 0
        # loop to catch scraper errors and retry limited times
        while retry_attempts < 3:
            try:
                # log action
                dash.logging(card=CARD, text=f"Procesando: {doc_tipo} {doc_num}")

                # send request to scraper
                _img_filename = scrape_recvehic.browser(doc_num=doc_num)

                # update memberLastUpdate table with last update information
                _now = dt.now().strftime("%Y-%m-%d")
                db_cursor.execute(
                    f"UPDATE membersLastUpdate SET LastUpdateRecord = '{_now}' WHERE IdMember_FK = '{id_member}'"
                )

                # response from scraper is that there is no record
                if _img_filename == -1:
                    break

                # stop process if blank response from scraper
                if not _img_filename:
                    dash.logging(
                        card=CARD,
                        status=2,
                        text="Scraper crash",
                        lastUpdate=dt.now(),
                    )
                    return

                # add foreign key and current date to response
                _values = (id_member, _img_filename, _now)

                # delete all old records from member
                db_cursor.execute(
                    f"""    DELETE FROM recordConductores WHERE IdMember_FK =
                            (SELECT IdMember FROM members WHERE DocTipo = '{doc_tipo}'
                                AND DocNum = '{doc_num}')"""
                )

                # insert record into database
                db_cursor.execute(f"INSERT INTO recordConductores VALUES {_values}")
                dash.logging(action=f"[ RECORD ] {"|".join([str(i) for i in _values])}")

                # update dashboard with progress and last update timestamp
                dash.logging(
                    card=CARD,
                    progress=int((counter / len(update_data)) * 100),
                    lastUpdate=dt.now(),
                )

                # no errors - next member
                break

            except KeyboardInterrupt:
                quit()

            except Exception:
                retry_attempts += 1
                dash.logging(
                    card=CARD,
                    status=2,
                    text=f"|ADVERTENCIA| Reintentando [{retry_attempts}/3]: {doc_tipo} {doc_num}",
                )

        db_conn.commit()

    # log last action
    dash.logging(
        card=CARD,
        title="Record del Conductor",
        progress=100,
        status=3,
        text="Inactivo",
        lastUpdate=dt.now(),
    )
