import os
from selenium.webdriver.common.by import By
from selenium.common.exceptions import *
from selenium.webdriver.support.ui import Select
import time
from src.utils.chromedriver import ChromeUtils


def browser(placa):

    TIMEOUT = 90  # seconds

    webdriver = ChromeUtils().init_driver(
        headless=False, verbose=False, maximized=True, incognito=False
    )
    webdriver.get("https://www.sat.gob.pe/WebSitev8/IncioOV2.aspx")

    time.sleep(0.5)
    _target = (
        "https://www.sat.gob.pe/VirtualSAT/modulos/papeletas.aspx?tri=T&mysession="
        + webdriver.current_url.split("=")[-1]
    )
    webdriver.get(_target)
    time.sleep(0.5)

    # select alternative option from dropdown to reset it
    drop = Select(webdriver.find_element(By.ID, "tipoBusquedaPapeletas"))
    drop.select_by_value("busqLicencia")
    time.sleep(0.5)

    # select Busqueda por Documento from dropdown
    drop.select_by_value("busqPlaca")
    time.sleep(0.5)

    # enter placa
    c = webdriver.find_element(By.ID, "ctl00_cplPrincipal_txtPlaca")
    c.send_keys(placa)

    # wait until clicking on Buscar does not produce error (means "I'm not a robot passed")
    # or return with timeout
    timeout_start = time.time()
    while webdriver.find_elements(By.ID, "ctl00_cplPrincipal_txtPlaca"):
        if time.time() - timeout_start > TIMEOUT:
            webdriver.quit()
            return -1
        time.sleep(0.5)
        e = webdriver.find_elements(By.ID, "ctl00_cplPrincipal_CaptchaContinue")
        if e:
            try:
                e[0].click()
            except Exception:
                pass

    time.sleep(2)
    v = webdriver.find_elements(By.ID, "ctl00_cplPrincipal_lblMensajeVacio")

    # blank response if no papeletas found
    if v and "No se encontraron" in v[0].text:
        webdriver.find_element(By.ID, "menuOption10").click()
        webdriver.quit()
        return []

    # if papeletas found, go through all and return list of papeletas
    n = 2
    responses = []
    xpath = lambda row, col: webdriver.find_elements(
        By.XPATH,
        f"/html/body/form/div[3]/section/div/div/div[2]/div[8]/div/div/div[1]/div/div/table/tbody/tr[{row}]/td[{col}]",
    )

    keys = [
        "placa",
        "reglamento",
        "falta",
        "documento",
        "fecha_emision",
        "importe",
        "gastos",
        "descuento",
        "deuda",
        "estado",
        "",
        "licencia",
        "doc_tipo",
        "doc_num",
    ]

    while xpath(n, 1):

        resp = {
            dict_key: xpath(n, k + 2)[0].text
            for k, dict_key in enumerate(keys)
            if k != 10
        }

        # search if ticket image exists
        imgs = webdriver.find_elements(
            By.ID, "ctl00_cplPrincipal_grdEstadoCuenta_ctl02_lnkImagen"
        )

        # no image found, empty filename string
        if not imgs:
            img_filename = ""

        # image found, grab image and save in file,
        else:
            img_filename = os.path.join(
                "data",
                "images",
                f"SATMUL_{placa.upper()}.png",
            )

            # navigate to page with image
            webdriver.get(imgs[0].get_attribute("href"))
            time.sleep(0.5)

            # save image to file
            with open(img_filename, "wb") as file:
                file.write(webdriver.find_element(By.ID, "imgPapel").screenshot_as_png)
            time.sleep(0.5)

        # add image filename to response and add response to list of papeletas
        resp.update({"img_filename": str(os.path.basename(img_filename))})
        responses.append(resp)
        n += 1

    webdriver.quit()
    return responses
