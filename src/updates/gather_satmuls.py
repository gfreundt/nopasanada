from datetime import datetime as dt

# local imports
from src.utils.utils import date_to_db_format
from src.scrapers import scrape_satmul


def gather(db_conn, db_cursor, dash, update_data):

    CARD = 4

    # log first action
    dash.logging(
        card=CARD,
        title=f"Multas SAT Lima [{len(update_data)}]",
        status=1,
        progress=0,
        text="Inicializando",
        lastUpdate="Actualizado:",
    )

    # iterate on every placa and write to database
    for counter, placa in enumerate(update_data, start=1):

        retry_attempts = 0
        # loop to catch scraper errors and retry limited times
        while retry_attempts < 3:
            try:
                # log action
                dash.logging(card=CARD, text=f"Procesando: {placa}")

                # send request to scraper
                response_satmul = scrape_satmul.browser(placa=placa)

                # captcha timeout - manual user not there to enter captcha, skip process
                if response_satmul == -1:
                    dash.logging(
                        card=CARD,
                        title="Multas SAT Lima",
                        status=2,
                        text="Timeout (usuario)",
                        lastUpdate=dt.now(),
                    )
                    return True  # tells gather all that user has timed out

                # if there is data in response, enter into database, go to next placa
                _now = dt.now().strftime("%Y-%m-%d")
                for response in response_satmul:

                    # adjust date to match db format (YYYY-MM-DD)
                    new_record_dates_fixed = date_to_db_format(data=response.values())
                    _values = [999] + new_record_dates_fixed + [_now]

                    # delete all old records from member
                    db_cursor.execute(
                        f"DELETE FROM satmuls WHERE PlacaValidate = '{placa}'"
                    )

                    # insert new record into database
                    db_cursor.execute(f"INSERT INTO satmuls VALUES {tuple(_values)}")

                # update placas table with last update information
                db_cursor.execute(
                    f"UPDATE placas SET LastUpdateSATMUL = '{_now}' WHERE Placa = '{placa}'"
                )

                # update dashboard with progress and last update timestamp
                dash.logging(
                    card=CARD,
                    progress=int((counter / len(update_data)) * 100),
                    lastUpdate=dt.now(),
                )

                # no errors - update database and next member
                db_conn.commit()
                break

            except KeyboardInterrupt:
                quit()

            except:
                retry_attempts += 1
                dash.logging(
                    card=CARD,
                    text=f"|ADVERTENCIA| Reintentando [{retry_attempts}/3]: {placa}",
                )

        # if code gets here, means scraping has encountred three consecutive errors, skip record
        dash.logging(card=CARD, msg=f"|ERROR| No se pudo procesar {placa}.")

    # log last action
    dash.logging(
        card=CARD,
        title="Multas SAT Lima",
        progress=100,
        status=3,
        text="Inactivo",
        lastUpdate=dt.now(),
    )
