import os
import platform


# paths
if platform.system() == "Linux":
    NETWORK_PATH = os.path.join("/root/pythonCode/nopasanada")
elif platform.system() == "Windows":
    NETWORK_PATH = os.path.join(r"\\192.168.68.110", "d", "pythonCode", "nopasanada")

DB_NETWORK_PATH = os.path.join(NETWORK_PATH, "data", "members.db")
DB_LOCAL_PATH = os.path.join("data", "members.db")

# info email account
ZOHO_INFO_PASSWORD = "5QJWEKi0trAL"

# api email
ZOHO_MAIL_API_CLIENT_ID = "1000.400ELE5I2WU72H931RQI8HTIY2Y30E"
ZOHO_MAIL_API_CLIENT_SECRET = "fe41ea63cc1c667091b32b1068660cf0b44fffd823"
ZOHO_MAIL_API_REDIRECT_URL = "https://nopasanadape.share.zrok.io/redir"

# 3-letter months
MONTHS_3_LETTERS = (
    "Ene",
    "Feb",
    "Mar",
    "Abr",
    "May",
    "Jun",
    "Jul",
    "Ago",
    "Set",
    "Oct",
    "Nov",
    "Dic",
)

# scrapers headless
HEADLESS = {"soat": True}
