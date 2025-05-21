from datetime import datetime as dt
import easyocr
import logging
from ..utils import date_to_db_format, log_action_in_db
from src.scrapers import scrape_brevete


def gather(db_cursor, db_conn, dash, update_data):

    CARD = 0

    # log first action
    dash.log(
        card=CARD,
        title=f"Brevete [{len(update_data)}]",
        status=1,
        progress=0,
        text="Inicializando",
        lastUpdate="Actualizado:",
    )

    # start OCR with no log to console
    logging.getLogger("easyocr").setLevel(logging.ERROR)
    ocr = easyocr.Reader(["es"], gpu=False)

    # iterate on all records that require updating and get scraper results
    for counter, (id_member, doc_tipo, doc_num) in enumerate(update_data):

        # skip member if doc tipo is not DNI (CE mostly) - should have been filtered, double check
        if doc_tipo != "DNI":
            continue

        retry_attempts = 0
        # loop to catch scraper errors and retry limited times
        while retry_attempts < 3:
            try:
                # log action
                dash.log(card=CARD, text=f"Procesando: {doc_tipo} {doc_num}")

                # send request to scraper
                brevete_response, pimpagas_response = scrape_brevete.browser(
                    doc_num=doc_num, ocr=ocr
                )

                # update memberLastUpdate table with last update information
                _now = dt.now().strftime("%Y-%m-%d")
                db_cursor.execute(
                    f"UPDATE membersLastUpdate SET LastUpdateBrevete = '{_now}' WHERE IdMember_FK = {id_member}"
                )

                # stop processing if blank response from scraper
                if not brevete_response:
                    dash.log(
                        card=CARD,
                        status=2,
                        text="Scraper crash",
                        lastUpdate=dt.now(),
                    )
                    return

                # go to next record if no brevete info
                if brevete_response == -1:
                    continue

                # adjust date to match db format (YYYY-MM-DD)
                new_record_dates_fixed = date_to_db_format(
                    data=brevete_response.values()
                )

                # add foreign key and current date to scraper response
                _values = [id_member] + new_record_dates_fixed + [_now]

                # delete all old records from member
                db_cursor.execute(
                    f"DELETE FROM brevetes WHERE IdMember_FK = {id_member}"
                )

                print(_values)
                print(tuple(_values))

                # insert new record into database
                db_cursor.execute(f"INSERT INTO brevetes VALUES {tuple(_values)}")
                dash.log(action=f"[ BREVETES ] {"|".join([str(i) for i in _values])}")

                # process list of papeletas impagas and put them in different table
                for papeleta in pimpagas_response:

                    # adjust date to match db format (YYYY-MM-DD)
                    papeleta_dates_fixed = date_to_db_format(data=papeleta.values())

                    # add foreign key and current date to response
                    _values = [id_member] + papeleta_dates_fixed + [_now]

                    # delete all old records from member
                    db_cursor.execute(
                        f"DELETE FROM mtcPapeletas WHERE IdMember_FK = (SELECT IdMember FROM members WHERE DocTipo = '{doc_tipo}' AND DocNum = '{doc_num}')"
                    )

                    # insert record into database
                    db_cursor.execute(
                        f"INSERT INTO mtcPapeletas VALUES {tuple(_values)}"
                    )

                # update dashboard with progress and last update timestamp
                dash.log(
                    card=CARD,
                    progress=int((counter / len(update_data)) * 100),
                    lastUpdate=dt.now(),
                )

                # register action and skip to next record
                log_action_in_db(db_cursor, table_name="brevetes", idMember=id_member)
                log_action_in_db(
                    db_cursor, table_name="mtcPapeletas", idMember=id_member
                )

                # no errors - next member
                break

            except KeyboardInterrupt:
                quit()

            except:
                retry_attempts += 1
                dash.log(
                    card=CARD, msg=f"< BREVETE > Retrying Record {doc_tipo}-{doc_num}."
                )

        # if code gets here, means scraping has encountred three consecutive errors, skip record
        dash.log(card=CARD, msg=f"|ERROR| No se pudo procesar {doc_tipo} {doc_num}.")

        db_conn.commit()

    # log last action
    dash.log(
        card=CARD,
        title="Brevetes",
        progress=100,
        status=3,
        text="Inactivo",
        lastUpdate=dt.now(),
    )
