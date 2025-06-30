from selenium.webdriver.common.by import By
from selenium.common.exceptions import *
import time
import os
from src.utils.chromedriver import ChromeUtils
from src.utils.utils import use_truecaptcha


def browser(doc_num):
    webdriver = ChromeUtils().init_driver(headless=False, verbose=False, maximized=True)
    webdriver.get("https://sroppublico.jne.gob.pe/Consulta/Afiliado")
    time.sleep(1.5)

    # ensure page loading with refresh
    webdriver.refresh()

    while True:

        _img = webdriver.find_element(
            By.XPATH, "/html/body/div[1]/form/div/div[2]/div/div/div/div[1]/img"
        )

        _path = os.path.join("static", "jneafil.png")

        with open(_path, "wb+") as file:
            file.write(_img.screenshot_as_png)

        captcha_txt = use_truecaptcha(img_path=_path)

        # enter data into fields and run
        webdriver.find_element(By.ID, "DNI").send_keys(doc_num)
        time.sleep(0.2)
        webdriver.find_element(By.XPATH, "").send_keys(captcha_txt)
        time.sleep(0.2)
        webdriver.find_element(By.XPATH, "").click()

        # if no pendings, return empty dictionary
        if "pendientes" in _alerta:
            webdriver.quit()
            return {}
        else:
            break

    # get responses and package into list of dictionaries
    data_index = (
        "documento",
        "tipo",
        "fecha_documento",
        "codigo_infraccion",
        "clasificacion",
    )
    response = []
    pos1 = 2
    _xpath_partial = "/html/body/form/div[3]/div[3]/div/table/tbody/"

    # loop on all documentos
    while webdriver.find_elements(By.XPATH, _xpath_partial + f"tr[{pos1}]/td[1]"):
        item = {}

        # loop on all items in documento
        for pos2, data_unit in enumerate(data_index, start=1):
            item.update(
                {
                    data_unit: webdriver.find_element(
                        By.XPATH,
                        _xpath_partial + f"tr[{pos1}]/td[{pos2}]",
                    ).text
                }
            )

        # append dictionary to list
        response.append(item)
        pos1 += 1

    # last item is garbage, remove from response
    response.pop()

    # succesful, return list of dictionaries
    webdriver.quit()
    return response
