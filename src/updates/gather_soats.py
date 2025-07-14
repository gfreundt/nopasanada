from datetime import datetime as dt
from copy import deepcopy as copy

# local imports
from src.updates import soat_image_generator
from src.utils.utils import date_to_db_format, use_truecaptcha
from src.scrapers import scrape_soat


def gather(db_oonn, db_cursor, dash, update_data):

    CARD = 5

    # log first action
    dash.logging(
        card=CARD,
        title=f"Certificados Soat [{len(update_data)}]",
        status=1,
        progress=0,
        text="Inicializando",
        lastUpdate="Actualizado:",
    )

    scraper = scrape_soat.Soat()
    # iterate on every placa and write to database
    for counter, placa in enumerate(update_data, start=1):

        retry_attempts = 0
        # loop to catch scraper errors and retry limited times
        while retry_attempts < 3:
            try:
                # log action
                dash.logging(card=CARD, text=f"Procesando: {placa}")

                # grab captcha image from website and solve
                captcha_file_like = scraper.get_captcha()
                captcha = use_truecaptcha(captcha_file_like)["result"]

                # captcha timeout - manual user not there to enter captcha, skip process
                if captcha == -1:
                    dash.logging(
                        card=CARD,
                        title="Certificados Soat",
                        status=0,
                        text="Timeout (usuario)",
                        lastUpdate=dt.now(),
                    )
                    return

                # with captcha manually resolved, proceed to scraping
                response_soat = scraper.browser(placa=placa, captcha_txt=captcha)

                # wrong captcha - restart loop with same placa
                if response_soat == -2:
                    continue

                # scraper exceed limit of manual captchas - abort iteration
                elif response_soat == -1:
                    dash.logging(
                        card=CARD,
                        title="Certificados Soat",
                        status=2,
                        text="Detenido por limite Apeseg.",
                        lastUpdate=dt.now(),
                    )
                    scraper.webdriver.quit()
                    return

                # if there is data in response, enter into database, go to next placa
                elif response_soat:

                    # adjust date to match db format (YYYY-MM-DD)
                    new_record_dates_fixed = date_to_db_format(
                        data=response_soat.values()
                    )

                    # if soat data gathered succesfully, generate soat image and save in folder
                    img_name = soat_image_generator.generate(
                        db_cursor, data=copy(new_record_dates_fixed)
                    )

                    _now = dt.now().strftime("%Y-%m-%d")

                    # insert data into table
                    _values = [999] + list(new_record_dates_fixed) + [img_name] + [_now]

                    # delete all old records from member
                    db_cursor.execute(
                        f"DELETE FROM soats WHERE PlacaValidate = (SELECT Placa FROM placas WHERE Placa = '{placa}')"
                    )

                    # insert gathered record of member
                    db_cursor.execute(f"INSERT INTO soats VALUES {tuple(_values)}")
                    dash.logging(
                        action=f"[ SOATS ] {"|".join([str(i) for i in _values])}"
                    )

                    # update placas table with last update information
                    db_cursor.execute(
                        f"UPDATE placas SET LastUpdateSOAT = '{_now}' WHERE Placa = '{placa}'"
                    )

                # update dashboard with progress and last update timestamp
                dash.logging(
                    card=CARD,
                    progress=int((counter / len(update_data)) * 100),
                    lastUpdate=dt.now(),
                )

                # no errors - update database and next member
                db_oonn.commit()
                break

            except KeyboardInterrupt:
                quit()

            except Exception:
                retry_attempts += 1
                dash.logging(
                    card=CARD,
                    text=f"|ADVERTENCIA| Reintentando [{retry_attempts}/3]: {placa}",
                )

        # if code gets here, means scraping has encountred three consecutive errors, skip record
        dash.logging(card=CARD, msg=f"|ERROR| No se pudo procesar {placa}.")

        # log last action and close webdriver
    dash.logging(
        card=CARD,
        title="Certificados Soat",
        progress=100,
        status=3,
        text="Inactivo",
        lastUpdate=dt.now(),
    )

    scraper.webdriver.quit()
