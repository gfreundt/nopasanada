from datetime import datetime as dt
import re
import os
import platform
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as WebDriverOptions
from selenium.webdriver.chrome.service import Service
import subprocess
import requests
import json
import speech_recognition
import ctypes
import pypdfium2.raw as pdfium
import math
from PIL import Image
import img2pdf
import pyautogui


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
            "--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.218 Safari/537.36"
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
        except:
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
            except:
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


class PDFUtils:

    def pdf_to_png(self, from_path, to_path=None, scale=1):
        """if parameter to_path is given, result of funtion is to save image
        if parameter to_path is not given, return object as PIL image"""

        # Load document
        pdf = pdfium.FPDF_LoadDocument((from_path + "\x00").encode("utf-8"), None)

        # Check page count to make sure it was loaded correctly
        page_count = pdfium.FPDF_GetPageCount(pdf)
        assert page_count >= 1

        # Load the first page and get its dimensions
        page = pdfium.FPDF_LoadPage(pdf, 0)
        width = int(math.ceil(pdfium.FPDF_GetPageWidthF(page)) * scale)
        height = int(math.ceil(pdfium.FPDF_GetPageHeightF(page)) * scale)

        # Create a bitmap
        # (Note, pdfium is faster at rendering transparency if we use BGRA rather than BGRx)
        use_alpha = pdfium.FPDFPage_HasTransparency(page)
        bitmap = pdfium.FPDFBitmap_Create(width, height, int(use_alpha))
        # Fill the whole bitmap with a white background
        # The color is given as a 32-bit integer in ARGB format (8 bits per channel)
        pdfium.FPDFBitmap_FillRect(bitmap, 0, 0, width, height, 0xFFFFFFFF)

        # Store common rendering arguments
        render_args = (
            bitmap,  # the bitmap
            page,  # the page
            # positions and sizes are to be given in pixels and may exceed the bitmap
            0,  # left start position
            0,  # top start position
            width,  # horizontal size
            height,  # vertical size
            0,  # rotation (as constant, not in degrees!)
            pdfium.FPDF_LCD_TEXT
            | pdfium.FPDF_ANNOT,  # rendering flags, combined with binary or
        )

        # Render the page
        pdfium.FPDF_RenderPageBitmap(*render_args)

        # Get a pointer to the first item of the buffer
        buffer_ptr = pdfium.FPDFBitmap_GetBuffer(bitmap)
        # Re-interpret the pointer to encompass the whole buffer
        buffer_ptr = ctypes.cast(
            buffer_ptr, ctypes.POINTER(ctypes.c_ubyte * (width * height * 4))
        )
        # Create a PIL image from the buffer contents
        img = Image.frombuffer(
            "RGBA", (width, height), buffer_ptr.contents, "raw", "BGRA", 0, 1
        )
        # Close all
        pdfium.FPDFBitmap_Destroy(bitmap)
        pdfium.FPDF_ClosePage(page)
        pdfium.FPDF_CloseDocument(pdf)
        # Save it as file or return image object
        if to_path:
            img.save(to_path)
            return None
        else:
            return img

    def image_to_pdf(self, image_bytes, to_path):

        with open(to_path, "wb") as file:
            file.write(img2pdf.convert(image_bytes.filename))


class SpeechUtils:

    def __init__(self):
        self.speech_driver_errors = 0

    def clean_military_alphabet(self, text):
        with open(os.path.join("static", "military_alphabet.txt")) as file:
            ma_index = [i.strip() for i in file.readlines()]
            for word in ma_index:
                text = text.replace(word, word[0])
        return text

    def get_speech(self, use_military_alphabet=True, max_driver_errors=5, timeout=10):
        while True:
            try:
                with speech_recognition.Microphone() as mic:
                    self.speech = speech_recognition.Recognizer()
                    self.speech.adjust_for_ambient_noise(mic, duration=0.2)
                    _audio = self.speech.listen(mic, timeout=timeout)
                    text = self.speech.recognize_google(_audio)

                # clean military alphabet letters
                if use_military_alphabet:
                    text = self.clean_military_alphabet(text.lower())

                return text

            except speech_recognition.WaitTimeoutError:
                print("[ SPEECH RECOGNITION TIMEOUT ]")
                return "$$TIMEOUT$$"

            except:
                if self.speech_driver_errors < max_driver_errors:
                    self.speech = speech_recognition.Recognizer()
                    self.speech_driver_errors += 1
                else:
                    return None


class VPNUtils:

    def __init__(self):
        try:
            self.avp = os.path.join(
                r"C:\Program Files (x86)",
                "Kaspersky Lab",
                "Kaspersky VPN 5.20",
                "ksdeui.exe",
            )
            subprocess.Popen([self.avp])
            self.button_location = pyautogui.locateOnScreen("kpvn.png")
            self.vpn_on = False
            return True
        except:
            return False

    def turn_on(self):
        if self.button_location and self.vpn_on:
            pyautogui.click(self.button_location)

    def turn_off(self):
        if self.button_location and not self.vpn_on:
            pyautogui.click(self.button_location)


def log_action_in_db(db_cursor, table_name, idMember="", idPlaca=""):
    """Registers scraping action in actions table in database."""

    _values = (table_name, idMember, idPlaca, dt.now().strftime("%Y-%m-%d %H:%M:%S"))
    db_cursor.execute(f"INSERT INTO actions VALUES {_values}")


def revisar_symlinks():
    """validate symlink to see image files is active, if not create it"""
    link_path = Path("static/images")
    target_path = Path("data/images").resolve()

    if link_path.exists():
        if link_path.is_symlink():
            if link_path.resolve() == target_path:
                print("✅ Symlink data/images.")
                return
            else:
                print("⚠ Recreando symlink data/images...")
                link_path.unlink()
                link_path.parent.mkdir(parents=True, exist_ok=True)
                link_path.symlink_to(target_path, target_is_directory=True)
                print("✅ Symlink creado.")
        else:
            raise Exception(
                f"❌ {link_path} existe pero no es un symlink. Remover de forma manual."
            )


def date_to_db_format(data):
    """Takes dd.mm.yyyy date formats with different separators and returns yyyy-mm-dd."""

    # define valid patterns, everything else is returned as is
    pattern = r"^(0[1-9]|[12][0-9]|3[01])[/-](0[1-9]|1[012])[/-]\d{4}$"

    new_record_dates_fixed = []

    for data_item in data:

        # test to determine if format is date we can change to db format
        try:
            if re.fullmatch(pattern, data_item):
                # if record has date structure, alter it, everything else throws exception and no changes made
                sep = "/" if "/" in data_item else "-" if "-" in data_item else None
                new_record_dates_fixed.append(
                    dt.strftime(dt.strptime(data_item, f"%d{sep}%m{sep}%Y"), "%Y-%m-%d")
                )

            else:
                new_record_dates_fixed.append(data_item)

        except:
            new_record_dates_fixed.append(data_item)

    return new_record_dates_fixed
