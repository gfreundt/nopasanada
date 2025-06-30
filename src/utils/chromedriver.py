import os
import platform
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as WebDriverOptions
from selenium.webdriver.chrome.service import Service
import subprocess
import requests
import json


class ChromeUtils:
    def init_driver(self, **kwargs):
        """Returns a ChromeDriver object with commonly used parameters allowing for some optional settings"""

        # set defaults that can be overridden by passed parameters
        parameters = {
            "incognito": False,
            "headless": False,
            "window_size": False,
            "load_profile": False,
            "verbose": True,
            "no_driver_update": False,
            "maximized": False,
        } | kwargs

        options = WebDriverOptions()

        # configurable options
        if parameters["incognito"]:
            options.add_argument("--incognito")
        if parameters["headless"]:
            options.add_argument("--headless=new")
        if parameters["window_size"]:
            options.add_argument(
                f"--window-size={parameters['window_size'][0]},{parameters['window_size'][1]}"
            )

        # fixed options
        options.add_argument(
            "--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.7151.104 Safari/537.36"
        )
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--silent")
        options.add_argument("--disable-notifications")
        options.add_argument("--log-level=3")
        options.add_experimental_option("excludeSwitches", ["enable-logging"])
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)

        _path = (
            os.path.join("src", "chromedriver.exe")
            if "Windows" in platform.uname().system
            else "/usr/bin/chromedriver"
        )

        try:
            self.driver_update(verbose=False)
        except KeyboardInterrupt:
            print("*** Cannot update Chromedriver ***")

        return webdriver.Chrome(
            service=Service(_path, log_path=os.devnull), options=options
        )

    def driver_update(self, **kwargs):
        """Compares current Chrome browser and Chrome driver versions and updates driver if necessary"""

        def check_chrome_version():
            result = subprocess.check_output(
                r'reg query "HKEY_CURRENT_USER\Software\Google\Chrome\BLBeacon" /v version'
            ).decode("utf-8")
            return result.split(" ")[-1].split(".")[0]

        def check_chromedriver_version():
            try:
                version = subprocess.check_output(f"{CURRENT_PATH} -v").decode("utf-8")
                return version.split(".")[0][-3:]
            except KeyboardInterrupt:
                return 0

        def download_chromedriver(target_version):
            # extract latest data from Google API
            api_data = json.loads(requests.get(GOOGLE_CHROMEDRIVER_API).text)

            # find latest build for current Chrome version and download zip file
            endpoints = api_data["milestones"][str(target_version)]["downloads"][
                "chromedriver"
            ]
            url = [i["url"] for i in endpoints if i["platform"] == "win64"][0]
            with open(TARGET_PATH, mode="wb") as download_file:
                download_file.write(requests.get(url).content)

            # delete current chromedriver.exe
            if os.path.exists(CURRENT_PATH):
                os.remove(CURRENT_PATH)

            # unzip downloaded file contents into Resources folder
            cmd = rf'Expand-Archive -Force -Path {TARGET_PATH} -DestinationPath "{BASE_PATH}"'
            subprocess.run(["powershell", "-Command", cmd])

            # move chromedriver.exe to correct folder
            os.rename(os.path.join(UNZIPPED_PATH, "chromedriver.exe"), CURRENT_PATH)

            # delete unnecesary files after unzipping
            os.remove(os.path.join(UNZIPPED_PATH, "LICENSE.chromedriver"))

        def file_cleanup(path):

            # erase downloaded zip file
            os.remove("chromedriver.zip")

            # erase files in unzipped folder and then erase folder
            _folder = os.path.join(path, "chromedriver-win64")
            for file in _folder:
                os.remove(file)
            os.rmdir(_folder)

        # define URIs
        GOOGLE_CHROMEDRIVER_API = "https://googlechromelabs.github.io/chrome-for-testing/latest-versions-per-milestone-with-downloads.json"
        if "Windows" in platform.uname().system:
            BASE_PATH = os.path.join("src")
        else:
            BASE_PATH = r"/home/gfreundt/pythonCode/Resources"

        CURRENT_PATH = os.path.join(BASE_PATH, "chromedriver.exe")
        TARGET_PATH = os.path.join(BASE_PATH, "chromedriver.zip")
        UNZIPPED_PATH = os.path.join(BASE_PATH, "chromedriver-win64")

        # get current browser and chromedriver versions
        driver = check_chromedriver_version()
        browser = check_chrome_version()

        # if versions don't match, get the correct chromedriver from repository
        if driver != browser:
            download_chromedriver(browser)
            print("*** Updated Chromedriver ***")
            # clean all unnecessary files
            file_cleanup(BASE_PATH)
