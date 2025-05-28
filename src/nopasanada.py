from pprint import pprint

# local imports
from src.updates import get_records_to_update, gather_all, get_recipients
from src.comms import craft_messages, send_messages, craft_alerts
from src.maintenance import maintenance

# import maintenance

# TODO: display $review on web page
# TODO: expand brevetes to include CE


def nopasanada(dash, db, cmds):
    """Program entry point. Executes actions depending on arguments ran at prompt.
    Valid cmds: 'update', 'comms', 'send'
    """

    # perform pre-maintenance
    maintenance.pre_maint(db.cursor)

    # update tables: users that require monthly message and users that require alert
    get_recipients.need_message(db.cursor)
    get_recipients.need_alert(db.cursor)

    # get all users and placas that need to be updated
    all_updates = get_records_to_update.get_records(db.cursor)

    pprint(all_updates)
    pprint([f"{i}: {len(all_updates[i])}" for i in all_updates])

    # scrape information on records that need to be updated
    if "update" in cmds:
        gather_all.gather_no_threads(db.conn, db.cursor, dash, all_updates)
    elif "update-threads" in cmds:
        gather_all.gather_threads(db.conn, db.cursor, dash, all_updates)

    # craft messages and alerts, save them to outbound folder
    if "comms" in cmds:
        craft_messages.craft(db.cursor, dash)
        craft_alerts.craft(db.cursor, dash)

    # send all emails and alerts from outbound folder, clear outbound folder
    if "send" in cmds:
        send_messages.send(db, dash, max=16)

    # perform post-maintenance
    maintenance.post_maint(db.cursor)

    # commit all changes before finishing code
    db.conn.commit()
