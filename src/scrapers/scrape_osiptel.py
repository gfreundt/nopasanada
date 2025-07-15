import time
import os

import pyautogui
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select


# local imports
from src.utils.chromedriver import ChromeUtils
from src.utils.constants import HEADLESS, NETWORK_PATH


def browser(doc_num):
    webdriver = ChromeUtils().init_driver(
        headless=HEADLESS["osiptel"], verbose=False, maximized=True
    )

    while True:
        webdriver.get("https://checatuslineas.osiptel.gob.pe/")
        time.sleep(4)

        drop = Select(webdriver.find_element(By.ID, "IdTipoDoc"))
        drop.select_by_value("1")

        time.sleep(3)

        webdriver.find_element(By.ID, "NumeroDocumento").send_keys(doc_num)
        time.sleep(3)

        x = pyautogui.locateCenterOnScreen(
            os.path.join(NETWORK_PATH, "static", "btn2.png")
        )
        pyautogui.moveTo(x, duration=1.3)
        pyautogui.click()
        time.sleep(2)

        result = []
        for i in ("", "[1]", "[2]", "[3]", "[4]", "[5]"):
            parts = []
            for j in range(1, 4):
                xpath = f"/html/body/div[1]/div[2]/div/div/div/div/form/div[4]/div[2]/div/div/div[2]/div/table/tbody/tr{i}/td[{j}]"
                elem = webdriver.find_elements(By.XPATH, xpath)
                if elem:
                    parts.append(elem[0].text)
                else:
                    break
            result.append(parts)

        if result == [[], [], [], [], [], []]:
            webdriver.refresh()
        else:
            webdriver.quit()
            return result
