import sys
from pprint import pprint

# local imports
from src.monitor import monitor
from src.updates import get_records_to_update, gather_all
from src.comms import craft_messages, send_messages, craft_alerts

# import maintenance

# TODO: display $review on web page
# TODO: expand brevetes to include CE


def launcher(dash, db):
    """Program entry point. Executes actions depending on arguments ran at prompt.
    Valid arguments: FULL, MEMBER, UPDATE, MAN, AUTO, ALL, ALERT, EMAIL, MAINT
    """

    # check for new members, unsub/resub requests and generate 30-day list
    if "MEMBER" in sys.argv or "FULL" in sys.argv:
        # add to monitor display
        monitor.log("Checking New Members...", type=0)
        # add new members from online form
        add_members.add(db.cursor, monitor)
        # process unsub/resub requests
        process_unsub.process(db.cursor, monitor)
        # save database changes
        db.conn.commit()

    # if updates or messages selected, first update table of users that require an update
    if any([i in sys.argv for i in ("UPDATE", "FULL", "INFO", "MSG")]):
        all_updates = get_records_to_update.get_records(db.cursor)

        pprint(all_updates)
        print([f"{i}: {len(all_updates[i])}" for i in all_updates])

        # get members that will require alert to include in records that require update
        # required_alerts = ALERT.get_alert_list(db_cursor)

    # scrape information on necessary users and placas
    if any([i in sys.argv for i in ("UPDATE", "FULL")]):
        # gather data for all record types
        gather_all.gather_threads(db.conn, db.cursor, dash, all_updates)

    # craft messages, save them to outbound folder
    if "MSG" in sys.argv or "FULL" in sys.argv:
        # compose emails and write them to outbound folder
        craft_messages.craft(db.cursor, dash)

    # craft alerts, save them to outbound folder
    if "ALERT" in sys.argv or "FULL" in sys.argv:
        # get members that require alerting
        required_alerts = ALERT.get_alert_list(db_cursor)
        # compose alerts and write them to outbound folder
        craft_alerts.craft(required_alerts, LOG, MONITOR)

    # send all emails and alerts in outbound folder
    if "SEND" in sys.argv or "FULL" in sys.argv:
        send_messages.send(db.cursor, dash)

    # final database maintenance before wrapping up
    if "MAINT" in sys.argv or "FULL" in sys.argv:
        MAINT = maintenance.Maintenance(LOG, MEMBERS, MONITOR)
        MAINT.housekeeping()
        MAINT.soat_images()
        # MAINT.sunarp_images()

        db.conn.commit()


def main(db):

    dash = monitor.Dashboard()

    if not "NOMON" in sys.argv:
        # begin monitoring in independent thread

        dash.run_in_background()

    # log start of script
    # mon.log("-" * 15 + "Start Program" + "-" * 15, type="0B")

    # start main program
    launcher(dash, db)

    # log end of program and quit
    # mon.log("-" * 15 + " End Program " + "-" * 15)


if __name__ == "__main__":
    main()


# idcoidog fk = 126 131 134
