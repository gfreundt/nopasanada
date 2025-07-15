import time
import io
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select

from src.utils.chromedriver import ChromeUtils
from src.utils.utils import use_truecaptcha
from src.utils.constants import HEADLESS


def browser(doc_num, doc_tipo):
    webdriver = ChromeUtils().init_driver(
        headless=HEADLESS["satimp"], verbose=False, maximized=True
    )
    webdriver.get("https://www.sat.gob.pe/WebSitev8/IncioOV2.aspx")
    # navigate once to Tributo Detalles page with internal URL
    _target = (
        "https://www.sat.gob.pe/VirtualSAT/modulos/TributosResumen.aspx?tri=T&mysession="
        + webdriver.current_url.split("=")[-1]
    )
    webdriver.get(_target)
    time.sleep(2)

    captcha_attempts = 0

    while True:
        # capture captcha image from webpage store in temp file
        _captcha_img = webdriver.find_element(
            By.XPATH,
            "/html/body/form/div[3]/section/div/div/div[2]/div[3]/div[5]/div/div[1]/div[2]/div/img",
        )

        # apply OCR to temp file
        _img = io.BytesIO(_captcha_img.screenshot_as_png)
        captcha_txt = use_truecaptcha(_img)["result"]

        # select alternative option from dropdown to reset it
        drop = Select(webdriver.find_element(By.ID, "tipoBusqueda"))
        drop.select_by_value("busqCodAdministrado")
        time.sleep(0.5)

        # select Busqueda por Documento from dropdown
        drop.select_by_value("busqTipoDocIdentidad")
        time.sleep(0.5)

        # select tipo documento (DNI/CE) from dropdown
        drop = Select(webdriver.find_element(By.ID, "ctl00_cplPrincipal_ddlTipoDocu"))
        drop.select_by_value("4" if doc_tipo == "CE" else "2")
        time.sleep(0.5)

        # clear field and enter DNI/CE
        _dnice = webdriver.find_element(By.ID, "ctl00_cplPrincipal_txtDocumento")
        _dnice.clear()
        _dnice.send_keys(doc_num)

        # clear field and enter captcha
        _captcha_field = webdriver.find_element(By.ID, "ctl00_cplPrincipal_txtCaptcha")
        _captcha_field.clear()
        _captcha_field.send_keys(captcha_txt)
        time.sleep(0.5)

        # click BUSCAR
        webdriver.find_element(By.CLASS_NAME, "boton").click()
        time.sleep(0.5)

        # captcha tries counter
        captcha_attempts += 1

        _msg = webdriver.find_element(
            By.ID, "ctl00_cplPrincipal_lblMensajeCantidad"
        ).text
        if _msg:
            break

        # reload page, start again
        webdriver.refresh()

    _qty = int("".join([i for i in _msg if i.isdigit()]))
    if _qty == 0:
        webdriver.quit()
        return []

    response = []
    for row in range(_qty):
        codigo = webdriver.find_element(
            By.ID, f"ctl00_cplPrincipal_grdAdministrados_ctl0{row+2}_lnkCodigo"
        ).text

        x = webdriver.find_element(
            By.ID, f"ctl00_cplPrincipal_grdAdministrados_ctl0{row+2}_lnkNombre"
        )
        x.click()
        time.sleep(0.5)

        _deudas = []
        webdriver.find_element(By.ID, "ctl00_cplPrincipal_rbtMostrar_2").click()
        time.sleep(0.5)

        for i in range(2, 10):
            _placeholder = f"ctl00_cplPrincipal_grdEstadoCuenta_ctl0{i}_lbl"
            y = f"{_placeholder}Anio"
            x = webdriver.find_elements(By.ID, y)
            if x:
                periodo = webdriver.find_element(By.ID, f"{_placeholder}Periodo").text
                ano = x[0].text
                # build fecha_hasta based on ano and periodo
                _f = ("03-31", "06-30", "09-30", "12-31")
                fecha_hasta = f"{ano}-{_f[int(periodo)-1]}"
                _fila = {
                    "ano": ano,
                    "periodo": periodo,
                    "documento": webdriver.find_element(
                        By.ID, f"{_placeholder}Documento"
                    ).text,
                    "total_a_pagar": webdriver.find_element(
                        By.ID, f"{_placeholder}Deuda"
                    ).text,
                    "fecha_hasta": fecha_hasta,
                }
                _deudas.append(_fila)

        webdriver.back()
        time.sleep(1)
        webdriver.back()
        time.sleep(1)
        response.append({"codigo": int(codigo), "deudas": _deudas})

    time.sleep(0.5)
    x = webdriver.find_element(By.ID, "ctl00_cplPrincipal_btnNuevaBusqueda")
    x.click()

    time.sleep(0.5)

    webdriver.quit()
    return response
