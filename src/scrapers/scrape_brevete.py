import time
import io
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from src.utils.chromedriver import ChromeUtils
from src.utils.utils import use_truecaptcha


def browser(doc_num):

    webdriver = ChromeUtils().init_driver(
        headless=False, verbose=False, maximized=False
    )
    url = "https://licencias.mtc.gob.pe/#/index"

    # load webpage
    webdriver.set_page_load_timeout(10)
    try:
        webdriver.get(url)
    except TimeoutException:
        webdriver.quit()
        return {}, []

    retry_captcha = False
    # outer loop: in case captcha is not accepted by webpage, try with a new one
    while True:
        captcha_txt = ""
        # inner loop: in case OCR cannot figure out captcha, retry new captcha
        while not captcha_txt:
            if retry_captcha:
                webdriver.refresh()
                time.sleep(2)
            # capture captcha image from webpage and store in object
            try:
                _captcha_img_url = webdriver.find_element(
                    By.XPATH,
                    "/html/body/app-root/div[2]/app-home/div/mat-card[1]/form/div[3]/div[2]/img",
                )
                _img = io.BytesIO(_captcha_img_url.screenshot_as_png)
                # convert image to text using OCR
                captcha_txt = use_truecaptcha(_img)["result"]
                retry_captcha = True

            except ValueError:
                # captcha image did not load, reset webpage
                webdriver.refresh()
                time.sleep(1.5)
                webdriver.get(url)
                time.sleep(1.5)
                webdriver.refresh()
                time.sleep(1.5)

        # enter data into fields and run
        webdriver.find_element(By.ID, "mat-input-1").send_keys(doc_num)
        webdriver.find_element(By.ID, "mat-input-0").send_keys(captcha_txt)
        webdriver.find_element(By.ID, "mat-checkbox-1").click()
        webdriver.find_element(
            By.XPATH,
            "/html/body/app-root/div[2]/app-home/div/mat-card[1]/form/div[5]/div[1]/button",
        ).click()
        time.sleep(1)

        # if captcha is not correct, refresh and restart cycle, if no data found, return None
        _alerta = webdriver.find_elements(By.ID, "swal2-html-container")
        if _alerta and "persona natural" in _alerta[0].text:
            # click on "Ok" to close pop-up
            webdriver.find_element(
                By.XPATH, "/html/body/div/div/div[6]/button[1]"
            ).click()
            # clear webpage for next iteration and small wait
            time.sleep(1)
            webdriver.back()
            time.sleep(0.5)
            webdriver.refresh()
            return [], []
        elif _alerta and "captcha" in _alerta[0].text:
            # click on "Ok" to close pop-up
            webdriver.find_element(
                By.XPATH, "/html/body/div/div/div[6]/button[1]"
            ).click()
            time.sleep(0.5)
            continue
        else:
            break

    # extract data from table and parse relevant data, return dictionary
    time.sleep(3)
    # exact IDs for "tipo" depends if there are one or two licenses shown
    if webdriver.find_elements(
        By.XPATH,
        "/html/body/app-root/div[2]/app-search/div[2]/mat-tab-group/div/mat-tab-body[1]/div/div/div/mat-card/mat-card-content/div/div/div/div[1]/mat-form-field/div/div[1]/div/input",
    ):
        _id_tipo = 12
    else:
        _id_tipo = 18

    data_index = (
        ("clase", 6),
        ("numero", 7),
        ("tipo", _id_tipo),
        ("fecha_expedicion", 8),
        ("restricciones", 9),
        ("fecha_hasta", 10),
        ("centro", 11),
    )

    response = {}
    for data_unit, pos in data_index:
        response.update(
            {
                data_unit: webdriver.find_element(
                    By.ID,
                    f"mat-input-{pos}",
                ).get_attribute("value")
            }
        )

    # check if no licencia registrada, respond with empty for each field
    _nr = webdriver.find_elements(By.CLASS_NAME, "div_non_data")
    if _nr:
        webdriver.quit()
        return -1, []

    # next tab (Puntos) - make sure all is populated before tabbing along (with timeout) and wait a little
    timeout = 0
    while not webdriver.find_elements(By.ID, "mat-tab-label-0-0"):
        time.sleep(1)
        timeout += 1
        if timeout > 10:
            webdriver.quit()
            return [], []
    time.sleep(1.5)

    action = ActionChains(webdriver)
    # enter key combination to open tabs
    for key in (Keys.TAB * 5, Keys.RIGHT, Keys.ENTER):
        action.send_keys(key)
        action.perform()
        time.sleep(0.5)

    # extract data
    _puntos = webdriver.find_element(
        By.XPATH,
        "/html/body/app-root/div[2]/app-search/div[2]/mat-tab-group/div/mat-tab-body[2]/div/div/mat-card/mat-card-content/div/app-visor-sclp/mat-card/mat-card-content/div/div[2]/label",
    )

    _puntos = int(_puntos.text.split(" ")[0]) if " " in _puntos.text else 0
    response.update({"puntos": _puntos})

    # next tab (Record)
    time.sleep(0.8)
    action.send_keys(Keys.RIGHT)
    action.perform()
    time.sleep(0.7)
    action.send_keys(Keys.ENTER)
    action.perform()
    time.sleep(0.5)

    _recordnum = webdriver.find_element(
        By.XPATH,
        "/html/body/app-root/div[2]/app-search/div[2]/mat-tab-group/div/mat-tab-body[3]/div/div/mat-card/mat-card-content/div/app-visor-record/div[1]/div/mat-card-title",
    ).text
    response.update({"record_num": _recordnum[9:] if _recordnum else None})

    # next tab (Papeletas Impagas)
    time.sleep(0.8)
    action.send_keys(Keys.RIGHT)
    action.perform()
    time.sleep(0.7)
    action.send_keys(Keys.ENTER)
    action.perform()
    time.sleep(0.5)

    pimpagas = webdriver.find_elements(
        By.XPATH,
        "/html/body/app-root/div[2]/app-search/div[2]/mat-tab-group/div/mat-tab-body[4]/div/div/mat-card/mat-card-content/div/app-visor-papeletas/div/shared-table/div/div",
    )
    if pimpagas and "se encontraron" in pimpagas[0].text:
        pimpagas = []
    elif not pimpagas:
        d = webdriver.find_element(
            By.XPATH,
            "/html/body/app-root/div[2]/app-search/div[2]/mat-tab-group/div/mat-tab-body[4]/div/div/mat-card/mat-card-content/div/app-visor-papeletas/div/shared-table/div/mat-table/mat-row[1]/mat-cell[1]/span",
        )
        d.click()
        time.sleep(1)

        _v = [
            i.text.split("\n")
            for i in webdriver.find_elements(
                By.XPATH,
                "/html/body/app-root/div[2]/app-search/div[2]/mat-tab-group/div/mat-tab-body[4]/div/div/mat-card/mat-card-content/div/app-visor-papeletas/div/shared-table/div/mat-table/mat-row",
            )
        ]
        pimpagas = [
            {
                "entidad": _v[0][1],
                "papeleta": _v[0][2],
                "fecha": _v[0][3],
                "fecha_firme": _v[1][1].strip(),
                "falta": _v[1][3].strip(),
                "estado_deuda": _v[1][5].strip(),
            }
        ]

    # process completed succesfully
    webdriver.quit()
    return response, pimpagas
