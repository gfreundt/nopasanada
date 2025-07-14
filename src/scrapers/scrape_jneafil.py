from selenium.webdriver.common.by import By
import time
import os
from PIL import Image
import io
from src.utils.chromedriver import ChromeUtils
from src.utils.utils import use_truecaptcha
from src.utils.constants import NETWORK_PATH


def browser(doc_num):
    webdriver = ChromeUtils().init_driver(headless=True, verbose=False, maximized=True)
    webdriver.get("https://sroppublico.jne.gob.pe/Consulta/Afiliado")
    time.sleep(1.5)

    # ensure page loading with refresh
    webdriver.refresh()

    while True:

        _captcha_file_like = io.BytesIO(
            webdriver.find_element(
                By.XPATH, "/html/body/div[1]/form/div/div[2]/div/div/div/div[1]/img"
            ).screenshot_as_png
        )
        captcha_txt = use_truecaptcha(img_path=_captcha_file_like)

        # enter data into fields and run
        webdriver.find_element(By.ID, "DNI").send_keys(doc_num)
        time.sleep(0.5)
        webdriver.find_element(
            By.XPATH, "/html/body/div[1]/form/div/div[2]/div/div/div/input"
        ).send_keys(captcha_txt["result"])
        time.sleep(0.5)
        webdriver.find_element(
            By.XPATH, "/html/body/div[1]/form/div/div[3]/button"
        ).click()
        time.sleep(3)

        # if no error in captcha, continue
        _alert = webdriver.find_element(By.XPATH, "/html/body/div[1]/div[2]")
        if "vencido" not in _alert.text:
            break

        # otherwise, refresh captcha and restart loop
        webdriver.find_element(
            By.XPATH, "/html/body/div[1]/form/div/div[2]/div/div/div/div[2]/i"
        ).click()
        time.sleep(1)

    # grab "Historial de Afiliacion"
    _historial = webdriver.find_element(By.ID, "divMsjHistAfil")

    if "Ninguno" in _historial.text:
        webdriver.quit()
        return ""

    else:
        # store in memory buffer
        _img_buffer = BytesIO()
        _img_buffer.write(webdriver.get_screenshot_as_png())

        # crop image
        img = Image.open(_img_buffer)
        _img_cropped = img.crop((61, 514, 1814, 1700))

        # save cropped image
        _filename = f"JNE_Afil_{doc_num}.png"
        _img_cropped.save(os.path.join(NETWORK_PATH, "data", "images", _filename))

        # close webdrive
        webdriver.quit()
        return _filename
