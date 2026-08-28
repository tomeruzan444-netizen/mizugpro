# -*- coding: utf-8 -*-
"""
Email the latest SEO report.

Optional: the weekly audit already files a GitHub issue, and GitHub emails the
assignee. This exists for the case where the report should land in an inbox
directly, without GitHub in the middle.

Reads from the environment so no address or password is ever committed:

    MAIL_TO         where the report goes           (required)
    MAIL_USER       the Gmail account that sends it (defaults to MAIL_TO)
    MAIL_PASSWORD   a Google App Password           (required)
    MAIL_HOST/PORT  default smtp.gmail.com:465

A normal Gmail password will not work — Google requires an App Password, made
at https://myaccount.google.com/apppasswords with 2-step verification on.
"""
import datetime
import os
import smtplib
import ssl
import sys
from email.message import EmailMessage

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPORT = os.path.join(ROOT, "seo-reports", "latest.md")


def main():
    to = os.environ.get("MAIL_TO", "").strip()
    password = os.environ.get("MAIL_PASSWORD", "").strip()
    user = os.environ.get("MAIL_USER", "").strip() or to
    host = os.environ.get("MAIL_HOST", "smtp.gmail.com")
    port = int(os.environ.get("MAIL_PORT", "465"))

    if not to or not password:
        print("MAIL_TO and MAIL_PASSWORD are not set — skipping email",
              file=sys.stderr)
        return 0

    if not os.path.exists(REPORT):
        print("no report at %s" % REPORT, file=sys.stderr)
        return 1

    with open(REPORT, encoding="utf-8") as fh:
        body = fh.read()

    msg = EmailMessage()
    msg["Subject"] = "ביקורת SEO שבועית — מיזוג פרו — %s" % datetime.date.today()
    msg["From"] = user
    msg["To"] = ", ".join(a.strip() for a in to.split(",") if a.strip())
    msg.set_content(body)

    with smtplib.SMTP_SSL(host, port, context=ssl.create_default_context()) as s:
        s.login(user, password)
        s.send_message(msg)

    print("sent the report to %s" % msg["To"], file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
