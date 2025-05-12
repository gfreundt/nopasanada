from datetime import datetime as dt
from ..utils import log_action_in_db
from src.scrapers import scrape_sunarp
import logging
import easyocr


def gather(db_cursor, dash, update_data):

    CARD = 6

    # log first action
    dash.log(
        card=CARD,
        title=f"Fichas Sunarp [{len(update_data)}]",
        status=1,
        progress=0,
        text="Inicializando",
        lastUpdate="Actualizado:",
    )

    # remove easyocr warnings in logger and start reader
    logging.getLogger("easyocr").setLevel(logging.ERROR)
    ocr = easyocr.Reader(["es"], gpu=False)

    # iterate on every placa and write to database
    for counter, (id_placa, placa) in enumerate(update_data, start=1):

        retry_attempts = 0
        # loop to catch scraper errors and retry limited times
        while retry_attempts < 3:
            try:
                # log action
                dash.log(card=CARD, text=f"Procesando: {placa}")

                # send request to scraper
                response = scrape_sunarp.browser(placa=placa, ocr=ocr)

                # update dashboard with progress and last update timestamp
                dash.log(
                    card=CARD,
                    progress=int((counter / len(update_data)) * 100),
                    lastUpdate=dt.now(),
                )

                # correct captcha, no image for placa - enter update attempt to review database, next placa
                if not response:
                    db_cursor.execute(
                        f"INSERT INTO '$review' (IdPlaca_FK, Reason) VALUES ({id_placa}, 'SUNARP')"
                    )
                    break

                # if there is data in response, enter into database, go to next placa
                _img_filename = f"SUNARP_{placa}.png"
                _now = dt.now().strftime("%Y-%m-%d")

                # add foreign key and current date to response
                _values = (
                    [id_placa]
                    + extract_data_from_image(_img_filename)
                    + [_img_filename, _now]
                )

                # delete all old records from placa
                db_cursor.execute(
                    f"DELETE FROM sunarps WHERE IdPlaca_FK = (SELECT IdPlaca FROM placas WHERE Placa = '{placa}')"
                )

                # insert new record into database
                db_cursor.execute(f"INSERT INTO sunarps VALUES {tuple(_values)}")

                # update placas table with last update information
                db_cursor.execute(
                    f"UPDATE placas SET LastUpdateSUNARP = '{_now}' WHERE Placa = '{placa}'"
                )

                # register action and skip to next record
                log_action_in_db(db_cursor, table_name="sunarps", idMember=id_placa)
                break

            except KeyboardInterrupt:
                quit()

            except:
                retry_attempts += 1
                dash.log(
                    card=CARD,
                    text=f"|ADVERTENCIA| Reintentando [{retry_attempts}/3]: {placa}",
                )

        # if code gets here, means scraping has encountred three consecutive errors, skip record
        dash.log(card=CARD, msg=f"|ERROR| No se pudo procesar {placa}.")

    # log last action
    dash.log(
        card=CARD,
        title="Fichas Sunarp",
        status=0,
        text="Inactivo",
        lastUpdate=dt.now(),
    )


# TODO: move to post-processing
def extract_data_from_image(img_filename):
    return [""] * 14
