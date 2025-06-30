import os
import smtplib
import mimetypes
from email.message import EmailMessage


class Email:

    def __init__(self, from_account, password):
        self.from_account = from_account
        self.password = password

    def send_email(self, emails):

        # if user sends single email, change format
        if emails is not list:
            emails = [emails]

        for email in emails:
            # create the email message
            msg = EmailMessage()
            msg["From"] = self.from_account
            msg["To"] = email["to"]
            msg["Subject"] = email["subject"]

            # add plain text and HTML alternative
            if email.get("plain_content"):
                msg.set_content(email["plain_content"])
            if email.get("html_content"):
                msg.add_alternative(email["html_content"], subtype="html")

            # process attachments
            if email.get("attachments"):
                for file_path in email["attachments"]:
                    if os.path.isfile(file_path):
                        mime_type, _ = mimetypes.guess_type(file_path)
                        mime_type = mime_type or "application/octet-stream"
                        maintype, subtype = mime_type.split("/", 1)

                        with open(file_path, "rb") as f:
                            file_data = f.read()
                            filename = os.path.basename(file_path)
                            msg.add_attachment(
                                file_data,
                                maintype=maintype,
                                subtype=subtype,
                                filename=filename,
                            )

            # send the email via Zoho's SMTP server
            try:
                with smtplib.SMTP("smtp.zoho.com", 587) as server:
                    server.starttls()  # Secure the connection
                    server.login(self.from_account, self.password)
                    server.send_message(msg)
                    return True
            except Exception:
                return False
