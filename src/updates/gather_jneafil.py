from datetime import datetime as dt

# local imports
from src.scrapers import scrape_jneafil


def gather(db_cursor, dash, update_data):

    CARD = 9

    # log first action
    dash.log(
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
                dash.log(card=CARD, text=f"Procesando: {doc_num}")

                # send request to scraper
                jne_response = scrape_jneafil.browser(doc_num)

                # update memberLastUpdate table with last update information
                _now = dt.now().strftime("%Y-%m-%d")
                db_cursor.execute(
                    f"UPDATE membersLastUpdate SET LastUpdateJNEAfil = '{_now}' WHERE IdMember_FK = {id_member}"
                )

                # update dashboard with progress and last update timestamp
                dash.log(
                    card=CARD,
                    progress=int((counter / len(update_data)) * 100),
                    lastUpdate=dt.now(),
                )

                # add foreign key, True/False flag and current date to scraper response
                _values = [id_member, bool(jne_response), jne_response, _now]

                # delete all old records from member
                db_cursor.execute(
                    f"DELETE FROM JNEAfiliacion WHERE IdMember_FK = {id_member}"
                )

                # insert gathered record of member
                db_cursor.execute(f"INSERT INTO JNEAfiliacion VALUES {tuple(_values)}")
                dash.log(action=f"[ JNE Afil ] {"|".join([str(i) for i in _values])}")

                # next record
                break

            except KeyboardInterrupt:
                quit()

            except Exception:
                retry_attempts += 1
                dash.log(
                    card=CARD,
                    text=f"|ADVERTENCIA| Reintentando [{retry_attempts}/3]: {doc_num}",
                )

    # log last action
    dash.log(
        card=CARD,
        title="JNE Afiliacion",
        progress=100,
        status=3,
        text="Inactivo",
        lastUpdate=dt.now(),
    )
