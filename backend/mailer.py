"""Local-only email delivery. Points at Mailpit (or any local mail catcher)
by default — swapping this for a real SMTP relay with internet access would
fail the challenge's offline requirement, so don't."""
import smtplib
from email.mime.text import MIMEText

from . import config


def send_mom_email(subject: str, body_markdown: str, recipients: list[str] | None = None):
    recipients = recipients or config.MOM_RECIPIENTS
    msg = MIMEText(body_markdown, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = "secure-mom@medpark.local"
    msg["To"] = ", ".join(recipients)

    with smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT) as server:
        server.sendmail(msg["From"], recipients, msg.as_string())
