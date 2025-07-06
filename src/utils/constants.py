import os

NETWORK_PATH = os.path.join(r"\\192.168.68.110\d\pythonCode\nopasanada")
SCRAPER_TEST = False


DB_LOCAL_PATH = os.path.join("data", "members.db")
DB_NETWORK_PATH = os.path.join(NETWORK_PATH, "data", "members.db")

INFO_EMAIL_PASSWORD = os.environ["ZOHO-1-PWD"]

ZOHO_MAIL_API_CLIENT_ID = "1000.400ELE5I2WU72H931RQI8HTIY2Y30E"
ZOHO_MAIL_API_CLIENT_SECRET = "fe41ea63cc1c667091b32b1068660cf0b44fffd823"
ZOHO_MAIL_API_REDIRECT_URL = "https://nopasanadape.share.zrok.io/redir"
