from selenium.webdriver.common.by import By
import time
from PIL import Image
import io
import urllib
import os
import numpy as np
from statistics import mean

from ..utils import ChromeUtils, use_truecaptcha, base64_to_image


def browser(placa):
    """returns:
    -1 = captcha ok, image did not load (retry)
     1 = captcha ok, placa does not exist
     image object = captcha ok, placa ok
    """

    # outer loop to restart in case captcha is ok but no image loads (SUNARP server error)
    while True:

        # start chromedriver
        webdriver = ChromeUtils().init_driver(
            headless=True, verbose=False, maximized=True, incognito=True
        )

        # open first URL, wait and open second URL (avoids limiting requests)
        webdriver.get("https://www.gob.pe/sunarp")
        time.sleep(2)
        webdriver.get("https://www.sunarp.gob.pe/consulta-vehicular.html")
        time.sleep(1)
        retry_captcha = False

        # inner loop to restart in case captcha is not ok
        while True:

            # get captcha in string format
            captcha_txt = ""
            while not captcha_txt:
                if retry_captcha:
                    webdriver.refresh()
                    time.sleep(1)
                # capture captcha image from webpage and save
                _path = os.path.join("static", "captcha_sunarp.png")
                _img = webdriver.find_element(By.ID, "image")
                with open(_path, "wb+") as file:
                    file.write(_img.screenshot_as_png)
                captcha_txt = use_truecaptcha(_path)["result"]
                retry_captcha = True

            # enter data into fields and run
            webdriver.find_element(By.ID, "nroPlaca").send_keys(placa)
            time.sleep(0.5)
            webdriver.find_element(By.ID, "codigoCaptcha").send_keys(captcha_txt)
            time.sleep(0.5)
            webdriver.find_element(
                By.XPATH,
                "/html/body/app-root/nz-content/div/app-inicio/app-vehicular/nz-layout/nz-content/div/nz-card/div/app-form-datos-consulta/div/form/fieldset/nz-form-item[3]/nz-form-control/div/div/div/button",
            ).click()
            time.sleep(1)

            # if captcha is not correct, restart inner loop;
            _alerta = webdriver.find_elements(By.ID, "swal2-html-container")
            if _alerta and "correctamente" in _alerta[0].text:
                webdriver.find_element(
                    By.XPATH, "/html/body/div/div/div[6]/button[1]"
                ).click()
                continue

            # if no data found, return None
            elif _alerta and "error" in _alerta[0].text:
                webdriver.find_element(
                    By.XPATH, "/html/body/div/div/div[6]/button[1]"
                ).click()

                webdriver.quit()
                return False

            # no error... continue
            else:
                break

        # search for SUNARP image
        _card_image = webdriver.find_elements(
            By.XPATH,
            "/html/body/app-root/nz-content/div/app-inicio/app-vehicular/nz-layout/nz-content/div/nz-card/div/app-form-datos-consulta/div/img",
        )

        # no image found, restart outer loop
        if not _card_image:
            webdriver.refresh()
            time.sleep(0.5)
            continue

        # grab image and save in file, return succesful
        else:

            base64_string = _card_image[0].get_attribute("src")[21:]
            output_path = os.path.join("data", "images", f"SUNARP_{placa}.png")
            base64_to_image(base64_string, output_path)

            # # save image in file
            # _img_path = os.path.abspath(
            #     os.path.join("data", "images", f"SUNARP_{placa}.png")
            # )
            # with open(_img_path, "wb") as file:
            #     file.write(_card_image[0].screenshot_as_png)

            # press boton to start over
            time.sleep(1)
            q = webdriver.find_element(
                By.XPATH,
                "/html/body/app-root/nz-content/div/app-inicio/app-vehicular/nz-layout/nz-content/div/nz-card/div/app-form-datos-consulta/div/nz-form-item/nz-form-control/div/div/div/button",
            )
            q.click()

            webdriver.quit()
            return True


def process_captcha(img, ocr):

    # split image into six pieces and run OCR to each
    img.save(os.path.join("static", "sunarp_temp.jpg"))

    WHITE = np.asarray((255, 255, 255, 255))
    BLACK = np.asarray((0, 0, 0, 0))

    img_object = Image.open(os.path.join("static", "sunarp_temp.jpg"))

    original_img = np.asarray(img_object)
    original_img = np.asarray(
        [[WHITE if mean(i) > 165 else BLACK for i in j] for j in original_img],
        dtype=np.uint8,
    )

    a = len(original_img)
    b = len(original_img[1])

    h = np.full((b, a), 0)
    for x in range(len(original_img)):
        for y in range(len(original_img[0])):
            h[y][x] = int(original_img[x][y][0])

    stopx = []
    delta = -2
    check_for_next = False
    for x in range(180):
        if all([i == 0 for i in h[x]]) is check_for_next:
            stopx.append(x + delta)
            check_for_next = not check_for_next
            delta = delta * -1

    if len(stopx) % 2 == 1:
        stopx.append(179)

    phrase = ""
    for k in range(len(stopx) // 2):
        i = img_object.crop((stopx[2 * k], 0, stopx[2 * k + 1], 60))
        fn = os.path.join("static", f"temp{k}.jpg")
        i.save(fn)
        c = ocr.readtext(fn, text_threshold=0.4)
        if c:
            phrase += c[0][1]

    # ocr text correction
    phrase.replace("€", "C")

    print(phrase)

    return phrase.upper() if len(phrase) == 6 else ""
