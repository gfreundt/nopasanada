from selenium.webdriver.common.by import By
from selenium.common.exceptions import *
import time
from src.utils.chromedriver import ChromeUtils


def browser(placa):
    webdriver = ChromeUtils().init_driver(headless=True, verbose=False, maximized=True)
    webdriver.get(
        "https://www.sutran.gob.pe/consultas/record-de-infracciones/record-de-infracciones/"
    )
    time.sleep(1.5)

    # ensure page loading with refresh
    webdriver.refresh()

    while True:
        # capture captcha image from frame name
        _iframe = webdriver.find_element(By.CSS_SELECTOR, "iframe")
        webdriver.switch_to.frame(_iframe)
        captcha_txt = (
            webdriver.find_element(By.ID, "iimage").get_attribute("src").split("=")[-1]
        )
        captcha_txt = captcha_txt.replace("%C3%91", "Ñ")

        # enter data into fields and run
        webdriver.find_element(By.ID, "txtPlaca").send_keys(placa)
        time.sleep(0.2)
        elements = (
            webdriver.find_elements(By.ID, "TxtCodImagen"),
            webdriver.find_elements(By.ID, "BtnBuscar"),
        )
        if not elements[0] or not elements[1]:
            webdriver.refresh()
            continue
        else:
            elements[0][0].send_keys(captcha_txt)
            time.sleep(0.2)
            elements[1][0].click()
        time.sleep(0.5)

        # if no text response, restart loop
        elements = webdriver.find_elements(By.ID, "LblMensaje")
        if elements:
            _alerta = webdriver.find_element(By.ID, "LblMensaje").text
        else:
            webdriver.refresh()
            continue

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
