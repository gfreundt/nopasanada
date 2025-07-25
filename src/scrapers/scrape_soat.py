from selenium.webdriver.common.by import By
from selenium.common.exceptions import *
import time
import io
from src.utils.chromedriver import ChromeUtils
from src.utils.constants import NETWORK_PATH, HEADLESS


class Soat:

    def __init__(self):
        self.webdriver = ChromeUtils().init_driver(
            headless=HEADLESS["soat"], maximized=True, verbose=False, incognito=True
        )

    def get_captcha(self):
        self.webdriver.get("https://www.dimequetienesseguro.com/consulta-soat/")
        time.sleep(3)
        _img = self.webdriver.find_element(
            By.XPATH,
            "/html/body/div[1]/main/article/div/div[2]/div/div[1]/div[2]/form/div[2]/img",
        )
        return io.BytesIO(_img.screenshot_as_png)

    def browser(self, placa=None, captcha_txt=None):

        # llenar campo de placa
        self.webdriver.find_element(
            By.XPATH,
            "/html/body/div[1]/main/article/div/div[2]/div/div[1]/div[2]/form/div[1]/input",
        ).send_keys(placa)

        # llenar campo de captcha
        self.webdriver.find_element(
            By.XPATH,
            "/html/body/div[1]/main/article/div/div[2]/div/div[1]/div[2]/form/div[2]/input",
        ).send_keys(captcha_txt)

        # apretar "Consultar"
        self.webdriver.find_element(
            By.XPATH,
            "/html/body/div[1]/main/article/div/div[2]/div/div[1]/div[2]/form/button",
        ).click()

        time.sleep(1)
        _iframe = self.webdriver.find_element(By.CSS_SELECTOR, "iframe")
        self.webdriver.switch_to.frame(_iframe)

        time.sleep(2)

        # Check if limit of scraping exceeded and wait
        limit_msg = self.webdriver.find_elements(By.XPATH, "/html/body")
        if limit_msg and "superado" in limit_msg[0].text:
            # self.webdriver.refresh()
            self.webdriver.quit()
            return -1

        # Check if error message pops up
        error_msg = self.webdriver.find_elements(
            By.XPATH, "/html/body/div[3]/div/div/div[2]"
        )

        # Error: wrong captcha
        if error_msg and "incorrecto" in error_msg[0].text:
            # self.webdriver.refresh()
            self.webdriver.quit()
            return -2

        # Error: no data for placa
        if error_msg and "registrados" in error_msg[0].text:
            # self.webdriver.refresh()
            self.webdriver.quit()
            return {}

        time.sleep(2)

        # No Error: proceed with data capture
        headers = (
            "aseguradora",
            "fecha_inicio",
            "fecha_fin",
            "placa",
            "certificado",
            "uso",
            "clase",
            "vigencia",
            "tipo",
            "fecha_venta",
            "fecha_anulacion",
        )

        # adapt to xpath change if one soat listed or more than one
        single = "[1]"
        if self.webdriver.find_elements(
            By.XPATH, "/html/body/div[2]/div/div/div/div[2]/table/tbody/tr/td[1]"
        ):
            single = ""

        response = {
            i: self.webdriver.find_element(
                By.XPATH,
                f"/html/body/div[2]/div/div/div/div[2]/table/tbody/tr{single}/td[{j}]",
            ).text.strip()
            for i, j in zip(headers, range(1, 11))
        }

        # get out of frame and click CERRAR
        self.webdriver.switch_to.default_content()
        self.webdriver.find_element(
            By.XPATH,
            "/html/body/div[1]/main/article/div/div[2]/div/div[1]/div[4]/div/div/div[3]/button",
        ).click()

        self.webdriver.quit()
        return response
