import os

NETWORK_PATH = os.path.join(r"\\192.168.68.110\d\pythonCode\nopasanada")
SCRAPER_TEST = False


DB_LOCAL_PATH = os.path.join("data", "members.db")
DB_NETWORK_PATH = os.path.join(NETWORK_PATH, "data", "members.db")

INFO_EMAIL_PASSWORD = os.environ["ZOHO-1-PWD"]
