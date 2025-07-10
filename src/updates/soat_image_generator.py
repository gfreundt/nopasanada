import os
from datetime import datetime as dt
from PIL import Image, ImageDraw, ImageFont

# local imports
from src.utils.pdf import PDFUtils
from src.utils.constants import NETWORK_PATH


def generate(db_cursor, data):

    # load fonts
    _resources = os.path.join("D:\pythonCode", "Resources", "Fonts")
    font_small = ImageFont.truetype(os.path.join(_resources, "seguisym.ttf"), 30)
    font_large = ImageFont.truetype(os.path.join(_resources, "seguisym.ttf"), 45)

    # get list of available company logos
    _templates_path = os.path.join(NETWORK_PATH, "static")
    cias = [i.split(".")[0] for i in os.listdir(_templates_path)]

    # open blank template image and prepare for edit
    base_img = Image.open(os.path.join(_templates_path, "SOAT_base.png"))
    editable_img = ImageDraw.Draw(base_img)

    # turn date into correct format for certificate
    data[1] = dt.strftime(dt.strptime(data[1], "%Y-%m-%d"), "%d/%m/%Y")
    data[2] = dt.strftime(dt.strptime(data[2], "%Y-%m-%d"), "%d/%m/%Y")

    # if logo in database add it to image, else add word
    if data[0] in cias:
        logo = Image.open(os.path.join(_templates_path, f"{data[0]}.png"))
        logo_width, logo_height = logo.size
        logo_pos = (10 + (340 - logo_width) // 2, 250 + (120 - logo_height) // 2)

        # add insurance company logo to image
        base_img.paste(logo, logo_pos)

        # get INSURANCE COMPANY phone number from database
        db_cursor.execute(
            f"SELECT Telefono1 FROM '@aseguradoras' WHERE Aseguradora='{data[0]}'"
        )
        _phone = db_cursor.fetchone()[0]

        # add insurance company phone number to image
        editable_img.text(
            (400, 275), _phone if _phone else "", font=font_large, fill=(59, 22, 128)
        )
    else:
        editable_img.text(
            (40, 275), data[0].upper(), font=font_large, fill=(59, 22, 128)
        )

    # positions for each text in image
    coordinates = [
        (40, 516, 1),
        (40, 588, 2),
        (40, 665, 3),
        (337, 588, 2),
        (337, 665, 3),
        (40, 819, 4),
        (40, 897, 5),
        (40, 970, 6),
        (406, 971, 3),
    ]

    # loop through all positions and add them to image
    for c in coordinates:
        editable_img.text(
            (c[0], c[1]), data[c[2]].upper(), font=font_small, fill=(59, 22, 128)
        )

    file_name = f"SOAT_{data[4].upper()}.pdf"
    to_path = os.path.join(NETWORK_PATH, "data", "images", file_name)

    # delete image with same name (previous version) from destination folder if it exists
    if os.path.exists(to_path):
        os.remove(to_path)

    # save image to temporary folder
    temp_path = os.path.join(NETWORK_PATH, "temp", "temp_img.png")
    base_img.save(temp_path)

    # open image and transfrom to pdf
    img = Image.open(temp_path)
    pdf = PDFUtils()
    pdf.image_to_pdf(img, to_path)

    # return image file name to include in database table
    return file_name
