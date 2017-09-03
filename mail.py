#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
from configparser import SafeConfigParser
import os.path
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formatdate
import smtplib

if __name__ == "__main__":
    # åæをåç
    section, to, subject, body = sys.argv[1:5]
    # ini ファイルのデフォルトåをèå
    defaults = {
        'host': '127.0.0.1', 'port': 25,
        'use_smtps': 'no',
        'use_starttls': 'no',
        'user': None, 'password': None,
        'from': 'pandora@localhost',
        'encoding': 'iso-2022-jp',
    }
    # ini ファイルをèみèむ
    config = SafeConfigParser(defaults)
    conf_path = os.path.join(os.path.dirname(__file__), 'mail.ini')
    config.read(conf_path, encoding = 'utf-8')
    c = dict()
    for key, value in config.items(section):
        c[key] = value
    for key in ['use_smtps', 'use_starttls']:
        c[key] = config.getboolean(section, key)
    # email メッセージのäæ
    msg = MIMEText(body, 'plain', c['encoding'])
    msg['Subject'] = Header(subject, c['encoding'])
    msg['From'] = c['from']
    msg['To'] = to
    msg['Date'] = formatdate(localtime=True)
    # 送信
    if c['use_smtps']:
        smtp = smtplib.SMTP_SSL(c['host'], c['port'])
    else:
        smtp = smtplib.SMTP(c['host'], c['port'])
        if c['use_starttls']:
            smtp.starttls()
    if c['user'] and c['password']:
        smtp.login(c['user'], c['password'])
    smtp.sendmail(c['from'], to.split(','), msg.as_string())
    smtp.close()
