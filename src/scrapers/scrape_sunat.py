# TODO: carnet extranjeria

from selenium.webdriver.common.by import By
from selenium.common.exceptions import *
import time
from ..utils import ChromeUtils


def browser(doc_tipo, doc_num):

    webdriver = ChromeUtils().init_driver(headless=True, verbose=False, maximized=True)
    webdriver.get(
        "https://e-consultaruc.sunat.gob.pe/cl-ti-itmrconsruc/FrameCriterioBusquedaWeb.jsp"
    )
    time.sleep(2)

    webdriver.find_element(By.ID, "btnPorDocumento").click()
    time.sleep(2)
    webdriver.find_element(By.ID, "txtNumeroDocumento").send_keys(doc_num)
    webdriver.find_element(By.ID, "btnAceptar").click()
    time.sleep(3)
    webdriver.find_element(
        By.XPATH, "/html/body/div/div[2]/div/div[3]/div[2]/a/span"
    ).click()
    time.sleep(2)
    c = webdriver.find_elements(By.XPATH, "/html/body/div/div[2]/div/div[2]/div[2]")
    if c and "NO REGISTRA" in c[0].text:
        webdriver.quit()
        return []

    response = []
    for i in range(1, 9):
        d = webdriver.find_elements(
            By.XPATH, f"/html/body/div/div[2]/div/div[3]/div[2]/div[{i}]/div/div[2]"
        )
        if d:
            response.append(d[0].text)
    e = webdriver.find_elements(
        By.XPATH, "/html/body/div/div[2]/div/div[3]/div[2]/div[5]/div/div[4]/p"
    )

    if e:
        response.append(e[0].text)

    webdriver.find_element(By.XPATH, "/html/body/div/div[2]/div/div[2]/button").click()

    if len(response) == 9:
        webdriver.quit()
        return response
