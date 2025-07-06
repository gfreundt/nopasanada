from datetime import datetime as dt

# local imports
from src.utils.utils import date_to_db_format
from src.scrapers import scrape_sunat


def gather(db_cursor, dash, update_data):

    CARD = 8

    # log first action
    dash.logging(
        card=CARD,
        title=f"Sunat [{len(update_data)}]",
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
                sunat_response = scrape_sunat.browser(doc_tipo, doc_num)

                # update memberLastUpdate table with last update information
                _now = dt.now().strftime("%Y-%m-%d")
                db_cursor.execute(
                    f"UPDATE membersLastUpdate SET LastUpdateSunat = '{_now}' WHERE IdMember_FK = {id_member}"
                )

                # update dashboard with progress and last update timestamp
                dash.logging(
                    card=CARD,
                    progress=int((counter / len(update_data)) * 100),
                    lastUpdate=dt.now(),
                )

                # delete all old records from member
                db_cursor.execute(f"DELETE FROM sunats WHERE IdMember_FK = {id_member}")

                # response ok, no information available
                if sunat_response == -1:
                    dash.logging(
                        action=f"[ SUNATS ] Sin informacion para DNI {doc_num}."
                    )
                    break

                # response ok, information available

                # adjust date to match db format (YYYY-MM-DD)
                new_record_dates_fixed = date_to_db_format(data=sunat_response)

                # add foreign key and current date to scraper response
                _values = [id_member] + new_record_dates_fixed + [_now]

                # insert gathered record of member
                db_cursor.execute(f"INSERT INTO sunats VALUES {tuple(_values)}")
                dash.logging(action=f"[ SUNATS ] {"|".join([str(i) for i in _values])}")

                # skip to next record
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
        title="Sunat",
        progress=100,
        status=3,
        text="Inactivo",
        lastUpdate=dt.now(),
    )
