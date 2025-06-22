import time
from threading import Thread
from src.updates import (
    gather_brevetes,
    gather_revtecs,
    gather_sutrans,
    gather_satimps,
    gather_recvehic,
    gather_sunarps,
    gather_soats,
    gather_satmuls,
    gather_sunats,
    gather_jneafil,
    gather_jnemulta,
)


def gather_no_threads(db_conn, db_cursor, dash, all_updates):

    dash.log(general_status=("Activo", 1))

    # auto gathering
    gather_brevetes.gather(db_cursor, db_conn, dash, all_updates["brevetes"])
    gather_revtecs.gather(db_cursor, dash, all_updates["revtecs"])
    gather_sutrans.gather(db_cursor, dash, all_updates["sutrans"])
    gather_satimps.gather(db_cursor, dash, all_updates["satimpCodigos"])
    gather_recvehic.gather(db_cursor, db_conn, dash, all_updates["recvehic"])
    gather_sunarps.gather(db_cursor, db_conn, dash, all_updates["sunarps"])
    gather_soats.gather(db_conn, db_cursor, dash, all_updates["soats"])

    # # manual gathering
    gather_satmuls.gather(db_conn, db_cursor, dash, all_updates["satmuls"])

    # # in development
    gather_sunats.gather(db_cursor, dash, all_updates["sunats"])
    gather_jnemulta.gather(db_cursor, dash, all_updates["jnemultas"])
    gather_jneafil.gather(db_cursor, dash, all_updates["jneafils"])

    # commit all changes to database
    db_conn.commit()

    # final log update and give some time for webpage update
    dash.log(general_status=("Inactivo", 2))
    time.sleep(5)


def gather_threads(db_conn, db_cursor, dash, all_updates):

    dash.log(general_status=("Activo", 1))

    threads = []

    # requires manual captcha input (might timeout)
    threads.append(
        Thread(
            target=gather_satmuls.gather,
            args=(db_conn, db_cursor, dash, all_updates["satmuls"]),
        )
    )

    # do not require manual captcha input
    threads.append(
        Thread(
            target=gather_brevetes.gather,
            args=(db_cursor, db_conn, dash, all_updates["brevetes"]),
        )
    )
    threads.append(
        Thread(
            target=gather_revtecs.gather,
            args=(db_cursor, dash, all_updates["revtecs"]),
        )
    )
    threads.append(
        Thread(
            target=gather_sutrans.gather,
            args=(db_cursor, dash, all_updates["sutrans"]),
        )
    )
    threads.append(
        Thread(
            target=gather_satimps.gather,
            args=(db_cursor, dash, all_updates["satimpCodigos"]),
        )
    )
    threads.append(
        Thread(
            target=gather_recvehic.gather,
            args=(db_cursor, db_conn, dash, all_updates["recvehic"]),
        )
    )
    threads.append(
        Thread(
            target=gather_sunarps.gather,
            args=(db_cursor, db_conn, dash, all_updates["sunarps"]),
        )
    )
    threads.append(
        Thread(
            target=gather_soats.gather,
            args=(db_conn, db_cursor, dash, all_updates["soats"]),
        )
    )
    threads.append(
        Thread(
            target=gather_sunats.gather,
            args=(db_cursor, dash, all_updates["sunats"]),
        )
    )
    threads.append(
        Thread(
            target=gather_jnemulta.gather,
            args=(db_cursor, dash, all_updates["jnemultas"]),
        )
    )
    threads.append(
        Thread(
            target=gather_jneafil.gather,
            args=(db_cursor, dash, all_updates["jneafils"]),
        )
    )

    # start all threads with a 2 second gap to avoid webdriver conflict
    for thread in threads:
        thread.start()
        time.sleep(2)

    # wait for all active threads to finish
    while any([i.is_alive() for i in threads]):
        time.sleep(10)

    # commit all changes to database
    db_conn.commit()

    # final log update and give some time for webpage update
    dash.log(general_status=("Inactivo", 2))
    time.sleep(5)
