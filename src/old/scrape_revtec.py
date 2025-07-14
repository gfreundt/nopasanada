import time
import io
import urllib
from selenium.webdriver.common.by import By
from PIL import Image
from src.utils.chromedriver import ChromeUtils


def browser(ocr, placa):
    webdriver = ChromeUtils().init_driver(headless=True, verbose=False, maximized=True)
    webdriver.get("https://portal.mtc.gob.pe/reportedgtt/form/frmconsultaplacaitv.aspx")
    time.sleep(3)

    # test for 404
    if "HTTP 404" in webdriver.page_source:
        return 404

    retry_captcha = False
    while True:
        # get captcha in string format
        captcha_txt = ""
        while not captcha_txt:
            if retry_captcha:
                webdriver.refresh()
                time.sleep(1)
            # captura captcha image from webpage store in variable
            _captcha_img_url = webdriver.find_element(
                By.ID, "imgCaptcha"
            ).get_attribute("src")
            _img = io.BytesIO(urllib.request.urlopen(_captcha_img_url).read())

            # convert image to text using OCR
            _captcha = ocr.readtext(_img, text_threshold=0.5)
            captcha_txt = (
                _captcha[0][1] if len(_captcha) > 0 and len(_captcha[0]) > 0 else ""
            )
            retry_captcha = True

        # enter data into fields and run
        webdriver.find_element(By.ID, "txtPlaca").send_keys(placa)
        time.sleep(0.5)
        webdriver.find_element(By.ID, "txtCaptcha").send_keys(captcha_txt)
        time.sleep(0.5)
        webdriver.find_element(By.ID, "BtnBuscar").click()
        time.sleep(1)

        # if captcha is not correct, refresh and restart cycle, if no data found, return None
        _alerta = webdriver.find_element(By.ID, "lblAlertaMensaje").text
        if "no es correcto" in _alerta:
            continue
        elif "encontraron resultados" in _alerta:
            webdriver.quit()
            return []
        else:
            break

    # extract data from table and parse relevant data, return a dictionary with RTEC data for each PLACA
    # TODO: capture ALL revisiones (not just latest) -- response not []
    response = {}
    data_index = (
        ("certificadora", 1),
        ("placa", 1),
        ("certificado", 2),
        ("fecha_desde", 3),
        ("fecha_hasta", 4),
        ("resultado", 5),
        ("vigencia", 6),
    )
    for data_unit, pos in data_index:
        response.update(
            {
                data_unit: webdriver.find_element(
                    By.XPATH,
                    f"/html/body/form/div[4]/div/div/div[2]/div[2]/div/div/div[6]/div[{'2' if data_unit == 'certificadora' else '3'}]/div/div/div/table/tbody/tr[2]/td[{pos}]",
                ).text
            }
        )

    if response["resultado"] == "DESAPROBADO":
        response["fecha_hasta"] = response["fecha_desde"]
        response["vigencia"] = "VENCIDO"

    # process completed succesfully
    webdriver.quit()
    return response
