from datetime import datetime as dt

# local imports
from src.scrapers import scrape_sunarp


def gather(db_cursor, db_conn, dash, update_data):

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

    # iterate on every placa and write to database
    for counter, (id_placa, placa) in enumerate(update_data, start=1):

        retry_attempts = 0
        # loop to catch scraper errors and retry limited times
        while retry_attempts < 3:
            try:
                # log action
                dash.log(card=CARD, text=f"Procesando: {placa}")

                # send request to scraper
                response = scrape_sunarp.browser(placa=placa)

                # update dashboard with progress and last update timestamp
                dash.log(
                    card=CARD,
                    progress=int((counter / len(update_data)) * 100),
                    lastUpdate=dt.now(),
                )

                # correct captcha, no image for placa - next placa
                if not response:
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
                    f"DELETE FROM sunarps WHERE PlacaValidate = (SELECT Placa FROM placas WHERE ImgFilename = '{_img_filename}')"
                )

                # insert new record into database
                db_cursor.execute(f"INSERT INTO sunarps VALUES {tuple(_values)}")
                dash.log(action=f"[ SUNARPS ] {"|".join([str(i) for i in _values])}")

                # update placas table with last update information
                db_cursor.execute(
                    f"UPDATE placas SET LastUpdateSUNARP = '{_now}' WHERE Placa = '{placa}'"
                )

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

        # if code gets here, means scraping has encountred three consecutive errors, skip record
        dash.log(card=CARD, msg=f"|ERROR| No se pudo procesar {placa}.")

        db_conn.commit()

    # log last action
    dash.log(
        card=CARD,
        title="Fichas Sunarp",
        status=3,
        progress=100,
        text="Inactivo",
        lastUpdate=dt.now(),
    )


# TODO: move to post-processing
def extract_data_from_image(img_filename):
    return [""] * 14
