from datetime import datetime as dt
from src.utils.utils import date_to_db_format
from src.scrapers import scrape_sutran


def gather(db_cursor, dash, update_data):

    CARD = 7

    # log first action
    dash.log(
        card=CARD,
        title=f"Sutran [{len(update_data)}]",
        status=1,
        progress=0,
        text="Inicializando",
        lastUpdate="Actualizado:",
    )

    # iterate on all records that require updating and get scraper results
    for counter, (id_placa, placa) in enumerate(update_data, start=1):

        retry_attempts = 0
        # loop to catch scraper errors and retry limited times
        while retry_attempts < 3:
            try:
                # log action
                dash.log(card=CARD, text=f"Procesando: {placa}")

                # send request to scraper
                sutran_response = scrape_sutran.browser(placa=placa)

                _now = dt.now().strftime("%Y-%m-%d")

                # if no error in scrape, erase any prior records of this placa
                db_cursor.execute(
                    f"DELETE FROM sutrans WHERE PlacaValidate = '{placa}')"
                )

                # update placas table with last update information
                db_cursor.execute(
                    f"UPDATE placas SET LastUpdateSUTRAN = '{_now}' WHERE Placa = '{placa}'"
                )

                # update dashboard with progress and last update timestamp
                dash.log(
                    card=CARD,
                    progress=int((counter / len(update_data)) * 100),
                    lastUpdate=dt.now(),
                )

                # if response is blank, skip to next placa
                if not sutran_response:
                    break

                # iterate on all multas
                for response in sutran_response:
                    new_record_dates_fixed = date_to_db_format(data=response.values())
                    _values = [placa] + new_record_dates_fixed + [_now]

                    # insert gathered record of member
                    db_cursor.execute(f"INSERT INTO sutrans VALUES {tuple(_values)}")
                    dash.log(
                        action=f"[ SUTRANS ] {"|".join([str(i) for i in _values])}"
                    )

                # no errors - next placa
                break

            except KeyboardInterrupt:
                quit()

            # except Exception:
            #     retry_attempts += 1
            #     dash.log(
            #         card=CARD,
            #         text=f"|ADVERTENCIA| Reintentando [{retry_attempts}/3]: {placa}",
            #     )

        # if code gets here, means scraping has encountred three consecutive errors, skip record
        dash.log(card=CARD, msg=f"|ERROR| No se pudo procesar {placa}.")

    # log last action
    dash.log(
        card=CARD,
        title="Sutran",
        progress=100,
        status=3,
        text="Inactivo",
        lastUpdate=dt.now(),
    )
