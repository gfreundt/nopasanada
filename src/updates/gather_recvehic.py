from datetime import datetime as dt
from src.scrapers import scrape_recvehic
from ..utils import log_action_in_db
import logging
import easyocr

# remove easyocr warnings in logger
logging.getLogger("easyocr").setLevel(logging.ERROR)


def gather(db_cursor, dash, update_data):

    CARD = 1

    # log first action
    dash.log(
        card=CARD,
        title=f"Record del Conductor [{len(update_data)}]",
        status=1,
        progress=0,
        text="Inicializando",
        lastUpdate="Actualizado:",
    )

    # remove easyocr warnings in logger and start reader
    logging.getLogger("easyocr").setLevel(logging.ERROR)
    ocr = easyocr.Reader(["es"], gpu=False)

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
                dash.log(card=CARD, text=f"Procesando: {doc_tipo} {doc_num}")

                # send request to scraper
                _img_filename = scrape_recvehic.browser(doc_num=doc_num, ocr=ocr)

                # register action
                log_action_in_db(db_cursor, table_name="revtec", idMember=id_member)

                # update memberLastUpdate table with last update information
                _now = dt.now().strftime("%Y-%m-%d")
                db_cursor.execute(
                    f"UPDATE membersLastUpdate SET LastUpdateRecord = '{_now}' WHERE IdMember_FK = '{id_member}'"
                )

                # stop processing if blank response from scraper
                if not _img_filename:
                    break

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

                # no errors - next member
                break

            except KeyboardInterrupt:
                quit()

            except:
                retry_attempts += 1
                dash.log(
                    card=CARD,
                    text=f"|ADVERTENCIA| Reintentando [{retry_attempts}/3]: {doc_tipo} {doc_num}",
                )

        # if code gets here, means scraping has encountred three consecutive errors, skip record
        dash.log(card=CARD, msg=f"|ERROR| No se pudo procesar {doc_tipo} {doc_num}.")

    # log last action
    dash.log(
        card=CARD,
        title="Record del Conductor",
        status=0,
        text="Inactivo",
        lastUpdate=dt.now(),
    )
