from datetime import datetime as dt
import easyocr
import logging

# local imports
from src.utils.utils import date_to_db_format
from src.scrapers import scrape_revtec


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

    # start OCR with no log to console
    logging.getLogger("easyocr").setLevel(logging.ERROR)
    ocr = easyocr.Reader(["es"], gpu=False)

    # iterate on all records that require updating and get scraper results
    for counter, placa in enumerate(update_data, start=1):

        retry_attempts = 0
        # loop to catch scraper errors and retry limited times
        while retry_attempts < 3:
            try:
                # log action
                dash.log(card=CARD, text=f"Procesando: {placa}")

                # send request to scraper
                revtec_response = scrape_revtec.browser(ocr=ocr, placa=placa)

                # webpage is down: stop gathering and show error in dashboard
                if revtec_response == 404:
                    dash.log(
                        card=CARD,
                        status=2,
                        text="MTC offline",
                        lastUpdate=dt.now(),
                    )
                    return

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

                # next placa if blank response from scraper
                if not revtec_response:
                    break

                # adjust date to match db format (YYYY-MM-DD)
                new_record_dates_fixed = date_to_db_format(
                    data=revtec_response.values()
                )

                # add foreign key and current date to scraper response
                _values = [999] + new_record_dates_fixed + [_now]

                # delete all old records from placa

                db_cursor.execute(
                    f"DELETE FROM revtecs WHERE PlacaValidate = (SELECT Placa FROM placas WHERE Placa = '{placa}')"
                )

                # insert new record into database
                db_cursor.execute(f"INSERT INTO revtecs VALUES {tuple(_values)}")
                dash.log(action=f"[ REVTECS ] {"|".join([str(i) for i in _values])}")

                # skip to next record
                break

            except KeyboardInterrupt:
                quit()

            except Exception:
                retry_attempts += 1
                dash.log(
                    card=CARD,
                    text=f"|ADVERTENCIA| Reintentando [{retry_attempts}/3]: {placa}",
                )

    # log last action
    dash.log(
        card=CARD,
        title="Revisión Técnica",
        progress=100,
        status=3,
        text="Inactivo",
        lastUpdate=dt.now(),
    )
