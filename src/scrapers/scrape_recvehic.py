import os
import shutil
from selenium.webdriver.common.by import By
import time
from src.utils.chromedriver import ChromeUtils
from src.utils.utils import use_truecaptcha
from src.utils.constants import NETWORK_PATH


def browser(doc_num):

    # get paths to Downloads folder and destination folder
    from_path = os.path.join(
        os.path.expanduser("~/Downloads"), "RECORD DE CONDUCTOR.pdf"
    )
    to_path = os.path.join(".", "data", "images", f"RECORD_{doc_num}.pdf")

    # erase file from Downloads folder before downloading new one
    if os.path.exists(from_path):
        os.remove(from_path)

    # start browser, navigate to url
    webdriver = ChromeUtils().init_driver(headless=True, verbose=False, maximized=True)
    webdriver.get("https://recordconductor.mtc.gob.pe/")

    # outer loop: in case captcha is not accepted by webpage, try with a new one
    retry_captcha = False
    while True:
        # inner loop: in case OCR cannot figure out captcha, retry new captcha
        captcha_txt = ""
        while not captcha_txt:
            if retry_captcha:
                webdriver.refresh()
                time.sleep(2)
            # capture captcha image from webpage and store in variable
            try:
                _path = os.path.join(NETWORK_PATH, "temp", "recvehic_temp.png")
                with open(_path, "wb") as file:
                    file.write(
                        webdriver.find_element(By.ID, "idxcaptcha").screenshot_as_png
                    )
                # convert image to text using OCR
                captcha_txt = use_truecaptcha(_path)["result"]
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
            print("111111111111")
            # click on "Cerrar" to close pop-up
            webdriver.find_element(
                By.XPATH, "/html/body/div[5]/div/div/div[2]/button"
            ).click()
            # clear webpage for next iteration and small wait
            time.sleep(1)
            webdriver.refresh()
            continue
        elif _alerta and "PERSONA" in _alerta[0].text:
            print("22222222222")
            webdriver.quit()
            return -1
        else:
            print("333333333333333")
            break

    # click on download button
    b = webdriver.find_elements(By.ID, "btnprint")
    try:
        b[0].click()
    except Exception:
        webdriver.quit()
        return -1

    # wait max 10 sec while file is downloaded
    count = 0
    while not os.path.isfile(os.path.join(from_path)) and count < 10:
        time.sleep(1)
        count += 1

    webdriver.quit()

    # if file was downloaded successfully, transfer to correct folder and return filename

    print(from_path)

    print(os.path.isfile(os.path.join(from_path)))

    print(to_path)

    if count < 10:
        shutil.move(from_path, to_path)
        return str(os.path.basename(from_path))
