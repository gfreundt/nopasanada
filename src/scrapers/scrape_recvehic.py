import os
from selenium.webdriver.common.by import By
import time
import re
import numpy as np
from PIL import Image
from ..utils import ChromeUtils, PDFUtils


def get_captcha(ocr):

    def invert(img):
        a = len(img)
        b = len(img[1])
        h = np.full((b, a), 0)
        for x in range(len(img)):
            for y in range(len(img[0])):
                h[y][x] = int(img[x][y][0])
        return h

    def valid(text):
        if len(text) != 6:
            return False
        text1 = "".join(re.findall("[a-zA-Z0-9]", text))
        return text == text1

    def process(depth, f):
        img = np.asarray(f)
        copyimg = np.copy(a=img)
        for i, x in enumerate(img):
            for j, y in enumerate(x):
                if max(y) > 150:
                    copyimg[i][j] = [0, 0, 0]
                else:
                    copyimg[i][j] = [255, 255, 255]
        h = invert(copyimg)
        h = h.tolist()
        for x in range(len(h)):
            if h[x].count(255) < depth:
                h[x] = [0] * len(copyimg)
        h = np.asarray(h).tolist()
        a = len(h) - 1
        b = len(h[0]) - 1
        k = [[h[i][j] for i in range(a)] for j in range(b)]
        return np.asarray(k, dtype=np.uint8)

    text = None
    max_cert = 0
    for depth in range(2, 7):
        f = Image.open(os.path.join("static", "captcha_recveh.png"))
        img = process(depth=depth, f=f)
        c = ocr.readtext(img, text_threshold=0.4)
        if c and valid(c[0][1]) and c[0][2] > max_cert:
            max_cert = c[0][2]
            text = c[0][1]
            text = text.replace("9", "g")
            text = text.replace("l", "1")
    return text


def browser(doc_num, ocr):

    # erase file from destination directory before downloading new one
    from_path = os.path.join(
        r"C:\Users", "Gabriel", "Downloads", "RECORD DE CONDUCTOR.pdf"
    )
    if os.path.exists(from_path):
        os.remove(from_path)

    pdf = PDFUtils()
    webdriver = ChromeUtils().init_driver(headless=True, verbose=False, maximized=True)
    webdriver.get("https://recordconductor.mtc.gob.pe/")

    retry_captcha = False
    # outer loop: in case captcha is not accepted by webpage, try with a new one
    while True:
        captcha_txt = ""
        # inner loop: in case OCR cannot figure out captcha, retry new captcha
        while not captcha_txt:
            if retry_captcha:
                webdriver.refresh()
                time.sleep(2)
            # capture captcha image from webpage and store in variable
            try:
                with open(os.path.join("static", "captcha_recveh.png"), "wb") as file:
                    file.write(
                        webdriver.find_element(By.ID, "idxcaptcha").screenshot_as_png
                    )
                # convert image to text using OCR
                captcha_txt = get_captcha(ocr)
                retry_captcha = True

            except ValueError:
                # captcha image did not load, reset webpage
                webdriver.refresh()
                time.sleep(1.5)

        # enter data into fields and run
        webdriver.find_element(By.ID, "txtNroDocumento").send_keys(doc_num)
        webdriver.find_element(By.ID, "idCaptcha").send_keys(captcha_txt)
        time.sleep(3)
        webdriver.find_element(By.ID, "BtnBuscar").click()
        time.sleep(1)

        # if captcha is not correct, refresh and restart cycle, if no data found, return blank
        _alerta = webdriver.find_elements(By.ID, "idxAlertmensaje")
        if _alerta and "ingresado" in _alerta[0].text:
            # click on "Cerrar" to close pop-up
            webdriver.find_element(
                By.XPATH, "/html/body/div[5]/div/div/div[2]/button"
            ).click()
            # clear webpage for next iteration and small wait
            time.sleep(1)
            webdriver.refresh()
            continue
        elif _alerta and "PERSONA" in _alerta[0].text:
            # click on "Ok" to close pop-up
            webdriver.find_element(
                By.XPATH, "/html/body/div[5]/div/div/div[2]/button"
            ).click()
            time.sleep(1)
            webdriver.quit()
            return -1
        else:
            break

    b = webdriver.find_elements(By.ID, "btnprint")
    try:
        b[0].click()
    except:
        webdriver.quit()
        return ""

    # wait max 10 sec while file is downloaded
    count = 0
    while not os.path.isfile(os.path.join(from_path)) and count < 10:
        time.sleep(1)
        count += 1

    # take downloaded PDF, process image and save in data folder
    try:
        from_path = os.path.join(from_path)
        to_path = os.path.join("data", "images", f"RECORD_{doc_num.upper()}.png")

        img = pdf.pdf_to_png(from_path, scale=1.3)

        # delete image with same name (previous version) from destination folder if it exists
        if os.path.exists(to_path):
            os.remove(to_path)
        img.save(to_path)

        # delete original downloaded file (saves space and avoids "(1)" appended on filename in future)
        os.remove(from_path)

        webdriver.quit()
        return str(os.path.basename(to_path))

    except KeyboardInterrupt:
        quit()
