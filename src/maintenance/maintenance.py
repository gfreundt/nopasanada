import os


def pre_maint(db_cursor):

    # erase all alerts that might still be in outbound folder
    for file in os.listdir(os.path("outbound")):
        if "alert" in file:
            os.remove(file)
