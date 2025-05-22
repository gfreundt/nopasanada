import os


def pre_maint(db_cursor):

    # erase all comms that might still be in outbound folder
    for file in os.listdir("outbound"):
        if "alert" in file or "message" in file:
            os.remove(os.path.join("outbound", file))

    # erase all placas with no associated member for database
    cmd = "SELECT * FROM placas WHERE IdMember_FK NOT IN (SELECT IdMember FROM members)"
    db_cursor.execute(cmd)
    print(db_cursor.fetchall())


def post_maint(db_cursor):
    # extract text data from soat images
    # create reviews: duplicate placas
    pass
