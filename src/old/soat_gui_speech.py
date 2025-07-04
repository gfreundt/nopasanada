import cv2
import os


def get_captcha():
    # capture speech and return only if it matches criteria
    img = cv2.imread(os.path.join("static", "captcha_soat.png"))
    img = cv2.resize(img, (0, 0), fx=4, fy=4)
    cv2.imshow("captcha", img)
    cv2.waitKey(500)

    while True:
        text = SpeechUtils().get_speech(timeout=10).lower()

        # if speech recognition returns timeout, let gather know
        if text == "$$timeout$$":
            cv2.destroyAllWindows()
            return -1

        # text corrections
        text = text.replace(" ", "")
        text = text.replace("zero", "0")
        text = text.replace("one", "1")
        text = text.replace("to", "2")
        text = text.replace("two", "2")
        text = text.replace("for", "4")
        text = text.replace("five", "5")

        # show captured text
        print(f"Captured: {text}")

        # if speech is "pass" return wrong captcha to get a new one
        if text.lower() == "pass":
            cv2.destroyAllWindows()
            return "xxxxxx"

        # only accept 6-letter captchas
        if len(text) == 6:
            print("[ACCEPTED]")
            cv2.destroyAllWindows()
            return text
        else:
            print("[NOT VALID]")
