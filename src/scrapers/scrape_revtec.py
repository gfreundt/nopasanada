import time
import io
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoAlertPresentException
from src.utils.chromedriver import ChromeUtils
from src.utils.utils import use_truecaptcha


def browser(placa):

    webdriver = ChromeUtils().init_driver(headless=True, verbose=False, maximized=True)
    webdriver.get("https://rec.mtc.gob.pe/Citv/ArConsultaCitv")
    time.sleep(2)

    retry_captcha = False
    while True:
        # get captcha in string format
        captcha_txt = ""
        while not captcha_txt:
            if retry_captcha:
                webdriver.refresh()
                time.sleep(1)
            # captura captcha image from webpage, store in variable
            _captcha_img = webdriver.find_element(By.ID, "imgCaptcha")
            _img = io.BytesIO(_captcha_img.screenshot_as_png)
            captcha_txt = use_truecaptcha(_img)["result"]
            retry_captcha = True

        # enter data into fields and run
        webdriver.find_element(By.ID, "texFiltro").send_keys(placa)
        time.sleep(0.5)
        webdriver.find_element(By.ID, "texCaptcha").send_keys(captcha_txt)
        time.sleep(0.5)
        webdriver.find_element(By.ID, "btnBuscar").click()
        time.sleep(1)

        # look for alert - could mean error in captcha or no data for placa
        try:
            alert = webdriver.switch_to.alert
            if "no es" in alert.text:
                alert.accept()
                continue
            if "No se" in alert.text:
                webdriver.quit()
                return []
        except NoAlertPresentException:
            break

    # extract data from table and parse relevant data, return a dictionary with RTEC data for each PLACA
    # TODO: capture ALL revisiones (not just latest) -- response not []
    response = {}
    data_index = (
        ("certificadora", 1),
        ("placa", 3),
        ("certificado", 4),
        ("fecha_desde", 5),
        ("fecha_hasta", 6),
        ("resultado", 7),
        ("vigencia", 8),
    )
    for data_unit, pos in data_index:
        response.update({data_unit: webdriver.find_element(By.ID, f"Spv1_{pos}").text})

    if response["resultado"] == "DESAPROBADO":
        response["fecha_hasta"] = response["fecha_desde"]
        response["vigencia"] = "VENCIDO"

    # process completed succesfully
    webdriver.quit()
    return response
