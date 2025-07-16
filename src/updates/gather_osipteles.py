from datetime import datetime as dt

# local imports
from src.scrapers import scrape_osiptel


def gather(db_cursor, dash, update_data):

    CARD = 11

    # log first action
    dash.logging(
        card=CARD,
        title=f"JNE Afiliacion [{len(update_data)}]",
        status=1,
        progress=0,
        text="Inicializando",
        lastUpdate="Actualizado:",
    )

    # iterate on all records that require updating and get scraper results
    for counter, (id_member, doc_tipo, doc_num) in enumerate(update_data, start=1):

        retry_attempts = 0
        while retry_attempts < 3:
            try:
                # log action
                dash.logging(card=CARD, text=f"Procesando: {doc_num}")

                # send request to scraper
                response = scrape_osiptel.browser(doc_num)

                # update memberLastUpdate table with last update information
                _now = dt.now().strftime("%Y-%m-%d")
                db_cursor.execute(
                    f"UPDATE membersLastUpdate SET LastUpdateOSIPTEL = '{_now}' WHERE IdMember_FK = {id_member}"
                )

                # update dashboard with progress and last update timestamp
                dash.logging(
                    card=CARD,
                    progress=int((counter / len(update_data)) * 100),
                    lastUpdate=dt.now(),
                )

                # add foreign key, True/False flag and current date to scraper response
                _values = [id_member, response[0], response[1], response[2], _now]

                # delete all old records from member
                db_cursor.execute(
                    f"DELETE FROM osipteles WHERE IdMember_FK = {id_member}"
                )

                # insert gathered record of member
                db_cursor.execute(f"INSERT INTO osipteles VALUES {tuple(_values)}")
                dash.logging(
                    action=f"[ OSIPTEL ] {"|".join([str(i) for i in _values])}"
                )

                # next record
                break

            except KeyboardInterrupt:
                quit()

            # except Exception:
            #     retry_attempts += 1
            #     dash.logging(
            #         card=CARD,
            #         text=f"|ADVERTENCIA| Reintentando [{retry_attempts}/3]: {doc_num}",
            #     )

    # log last action
    dash.logging(
        card=CARD,
        title="OSIPTEL",
        progress=100,
        status=3,
        text="Inactivo",
        lastUpdate=dt.now(),
    )
