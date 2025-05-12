from datetime import datetime as dt
from ..utils import date_to_db_format, log_action_in_db
from src.scrapers import scrape_revtec
import logging
import easyocr


def gather(db_cursor, dash, update_data):

    CARD = 2

    # log first action
    dash.log(
        card=CARD,
        title=f"Revisión Técnica [{len(update_data)}]",
        status=1,
        progress=0,
        text="Inicializando",
        lastUpdate="Actualizado:",
    )

    # remove easyocr warnings in logger and start reader
    logging.getLogger("easyocr").setLevel(logging.ERROR)
    ocr = easyocr.Reader(["es"], gpu=False)

    dash.log(card=CARD, title="Revisión Tecnica", status=1)

    # iterate on all records that require updating and get scraper results
    for counter, (id_placa, placa) in enumerate(update_data, start=1):

        retry_attempts = 0
        # loop to catch scraper errors and retry limited times
        while retry_attempts < 3:
            try:
                # log action
                dash.log(card=CARD, text=f"Procesando: {placa}")

                # send request to scraper
                revtec_response = scrape_revtec.browser(ocr=ocr, placa=placa)

                # update placas table with last update information
                _now = dt.now().strftime("%Y-%m-%d")
                db_cursor.execute(
                    f"UPDATE placas SET LastUpdateRevTec = '{_now}' WHERE Placa = '{placa}'"
                )

                # update dashboard with progress and last update timestamp
                dash.log(
                    card=CARD,
                    progress=int((counter / len(update_data)) * 100),
                    lastUpdate=dt.now(),
                )

                # stop processing if blank response from scraper
                if not revtec_response:
                    break

                # adjust date to match db format (YYYY-MM-DD)
                new_record_dates_fixed = date_to_db_format(
                    data=revtec_response.values()
                )

                # add foreign key and current date to scraper response
                _values = [id_placa] + new_record_dates_fixed + [_now]

                # delete all old records from placa
                db_cursor.execute(
                    f"DELETE FROM revtecs WHERE IdPlaca_FK = (SELECT IdPlaca FROM placas WHERE Placa = '{placa}')"
                )

                # insert new record into database
                db_cursor.execute(f"INSERT INTO revtecs VALUES {tuple(_values)}")

                # register action and skip to next record
                log_action_in_db(db_cursor, table_name="revtec", idPlaca=id_placa)
                break

            except KeyboardInterrupt:
                quit()

            except:
                retry_attempts += 1
                dash.log(
                    card=CARD,
                    text=f"|ADVERTENCIA| Reintentando [{retry_attempts}/3]: {placa}",
                )

            # if code gets here, means scraping has encountred three consecutive errors, skip placa
            dash.log(card=CARD, msg=f"|ERROR| No se pudo procesar {placa}.")

    # log last action
    dash.log(
        card=CARD,
        title="Revisión Técnica",
        status=0,
        text="Inactivo",
        lastUpdate=dt.now(),
    )
