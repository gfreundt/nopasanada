from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time
from PIL import Image
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
            headless=False, verbose=True, maximized=True, incognito=True
        )

        # open first URL, wait and open second URL (avoids limiting requests)
        webdriver.get("https://www.gob.pe/sunarp")
        time.sleep(2)
        webdriver.get(
            "https://consultavehicular.sunarp.gob.pe/consulta-vehicular/inicio"
        )
        time.sleep(5)

        # enter placa data into field
        webdriver.find_element(By.ID, "nroPlaca").send_keys(placa)
        time.sleep(0.5)

        # loop to restart process in case captcha is not correct
        while True:

            # capture captcha image from webpage and save
            _path = os.path.join("static", "captcha_sunarp.png")
            with open(_path, "wb+") as file:
                file.write(webdriver.find_element(By.ID, "image").screenshot_as_png)
            captcha_txt = use_truecaptcha(_path)["result"]
            print("---------", captcha_txt)

            # clear captcha field and enter captcha text
            webdriver.find_element(By.ID, "codigoCaptcha").send_keys(
                Keys.BACKSPACE * 6 + captcha_txt
            )
            time.sleep(0.5)

            # click on "Realizar Busqueda"
            webdriver.find_element(
                By.XPATH,
                "/html/body/app-root/nz-content/div/app-inicio/app-vehicular/nz-layout/nz-content/div/nz-card/div/app-form-datos-consulta/div/form/fieldset/nz-form-item[3]/nz-form-control/div/div/div/button",
            ).click()
            time.sleep(1)

            # if captcha is not correct, refresh captcha and try again
            _alerta = webdriver.find_elements(By.ID, "swal2-html-container")
            if _alerta and "correctamente" in _alerta[0].text:
                print("************ refresh")
                # click salir de la alerta
                webdriver.find_element(
                    By.XPATH, "/html/body/div/div/div[6]/button[1]"
                ).click()
                # click nuevo captcha
                # webdriver.find_element(
                #     By.XPATH,
                #     "/html/body/app-root/nz-content/div/app-inicio/app-vehicular/nz-layout/nz-content/div/nz-card/div/app-form-datos-consulta/div/form/fieldset/nz-form-item[2]/table/tr/td[2]/a",
                # ).click()
                time.sleep(2)
                continue

            # if captcha correct but no image found, return False
            elif _alerta and "error" in _alerta[0].text:
                webdriver.find_element(
                    By.XPATH, "/html/body/div/div/div[6]/button[1]"
                ).click()

                webdriver.quit()
                return False

            # no error... continue
            print("breaj!!!!!!")
            break

        # wait up to 10 seconds for image to load
        time_start = time.perf_counter()
        _card_image = None
        while not _card_image and time.perf_counter() - time_start < 10:
            # search for SUNARP image
            _card_image = webdriver.find_elements(
                By.XPATH,
                "/html/body/app-root/nz-content/div/app-inicio/app-vehicular/nz-layout/nz-content/div/nz-card/div/app-form-datos-consulta/div/img",
            )
            time.sleep(0.5)

        # if image fails to load, return False
        if not _card_image:
            return False

        # grab image and save in file, return succesful
        base64_string = _card_image[0].get_attribute("src")[21:]
        output_path = os.path.join("data", "images", f"SUNARP_{placa}.png")
        base64_to_image(base64_string, output_path)

        # press boton to start over
        time.sleep(1)
        q = webdriver.find_element(
            By.XPATH,
            "/html/body/app-root/nz-content/div/app-inicio/app-vehicular/nz-layout/nz-content/div/nz-card/div/app-form-datos-consulta/div/nz-form-item/nz-form-control/div/div/div/button",
        )
        q.click()

        webdriver.quit()
        return True
