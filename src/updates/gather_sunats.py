from datetime import datetime as dt
from ..utils import date_to_db_format, log_action_in_db
from src.scrapers import scrape_sunat


def gather(db_cursor, dash, update_data):

    CARD = 8

    monitor.log(card=CARD, title="Consulta RUC de SUNAT...", status=1)

    # iterate on all records that require updating and get scraper results
    for counter, (id_member, doc_tipo, doc_num) in enumerate(update_data, start=1):

        retry_attempts = 0
        while retry_attempts < 3:
            try:
                # log action
                monitor.log(
                    card=CARD,
                    msg=f"[{counter}/{len(update_data)}] SUNAT: {doc_tipo}-{doc_num}",
                    type=1,
                )

                # send request to scraper
                sunat_response = scrape_sunat.browser(doc_tipo, doc_num)

                if not sunat_response:
                    break

                # adjust date to match db format (YYYY-MM-DD)
                new_record_dates_fixed = date_to_db_format(data=sunat_response)

                # add foreign key and current date to scraper response
                _values = (
                    [id_member]
                    + new_record_dates_fixed
                    + [dt.now().strftime("%Y-%m-%d")]
                )

                # delete all old records from member
                db_cursor.execute(f"DELETE FROM sunats WHERE IdMember_FK = {id_member}")

                # insert gathered record of member
                db_cursor.execute(f"INSERT INTO sunats VALUES {tuple(_values)}")
                dash.log(action=f"[ SUNATS ] {"|".join([str(i) for i in _values])}")

                # register action and skip to next record
                log_action_in_db(db_cursor, table_name="sunats", idMember=id_member)
                break

            except KeyboardInterrupt:
                quit()

            except:
                retry_attempts += 1
                monitor.log(
                    card=CARD,
                    msg=f"< SUNAT > Retrying {doc_tipo}-{doc_num}.",
                    error=True,
                    type=1,
                )

        else:
            # if code gets here, means scraping has encountred three consecutive errors, skip record
            monitor.log(
                card=CARD,
                msg=f"< SUNAT > Could not process {doc_tipo}-{doc_num}. Skipping Record.",
                error=True,
                type=1,
            )
