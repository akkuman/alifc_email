# -*- coding: utf-8 -*-

import logging
import json
import socket
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.mime.text import MIMEText
from email.utils import formatdate, make_msgid
import time
import base64

logger: logging.Logger = logging.getLogger()

# To enable the initializer feature (https://help.aliyun.com/document_detail/158208.html)
# please implement the initializer function as below：
def initializer(context):
   logger = logging.getLogger()  
   logger.info('initializing')


class SMTPBase():
    def __init__(self, host):
        pass

    def login(self, user, password):
        pass

    def quit(self):
        pass

    def send_mail(self, mail_tos, subject, relay_to, relay_name, mail_body, files=None):
        pass

class SMTPClient(SMTPBase):
    def __init__(self, host, timeout=socket._GLOBAL_DEFAULT_TIMEOUT):
        super().__init__(host)
        self.host = host
        try:
            self.client = smtplib.SMTP_SSL(host=host, timeout=timeout)
        except Exception:
            self.client = smtplib.SMTP(host=host, timeout=timeout)
        n, byte = self.client.connect(host)
        logger.info(f"connect n= {n} byte = {byte.decode()}")
        self.user = None

    def login(self, user, password):
        self.user = user
        n, byte = self.client.login(user, password)
        logger.info(f"login n= {n} byte = {byte.decode()}")

    def quit(self):
        self.client.quit()

    def send_mail(self, mail_tos, subject, relay_to, relay_name, mail_body, files=None):
        msg = MIMEMultipart()
        att_text = MIMEText(mail_body, 'html', 'utf-8')
        relay_name = "管理员" if not relay_name else relay_name
        if relay_to != "":
            msg['From'] = "=?UTF-8?B?{}?= <{}>".format(base64.b64encode(relay_name.encode()).decode(), relay_to)
        else:
            msg['From'] = "=?UTF-8?B?{}?= <{}>".format(base64.b64encode(relay_name.encode()).decode(), self.user)
        msg['Subject'] = subject
        msg['Date'] = formatdate()
        msg['To'] = mail_tos
        msg['Message-Id'] = make_msgid()
        msg.attach(att_text)
        plan_text = MIMEText("")
        msg.attach(plan_text)
        if files:
            for file_name, file in files.items():
                logger.info(f"file name= {file_name}")
                att_file = MIMEApplication(base64.b64decode(file))
                att_file.add_header('Content-Disposition', 'attachment', filename=file_name)
                # att_file = MIMEText(base64.b64decode(file), 'base64', 'utf-8')
                # att_file["Content-Type"] = 'application/octet-stream'
                # att_file["Content-Disposition"] = f'attachment; filename="{file_name}"'
                msg.attach(att_file)
        err = self.client.send_message(msg=msg, from_addr=self.user, to_addrs=mail_tos)
        if len(err) > 0:
            logger.error(err)
        time.sleep(5)

    @classmethod
    def get_logined_client(cls, host, user, password):
        client = cls(host)
        client.login(user, password)
        return client


def _get_json_body(environ):
    try:
        request_body_size = int(environ.get('CONTENT_LENGTH', 0))
    except (ValueError):
        request_body_size = 0
    request_body = environ['wsgi.input'].read(request_body_size)
    if request_body_size:
        body = json.loads(request_body.decode())
        return body
    return None


def new_response(start_response, code, msg, data):
    status = '200 OK'
    response_headers = [('Content-type', 'application/json')]
    start_response(status, response_headers)
    body = {
        'code': code,
        'msg': msg,
        'data': data
    }
    return [json.dumps(body).encode()]


def sendmail(host, username, password, mail_to, subject, relay_to, relay_name, mail_body, files):
    '''发送邮件
    Args:
        host: 邮服地址
        username: 邮服用户名
        password: 邮服密码
        ...
    Retuens:
        将会自动重试三次，如果成功则退出，返回None，如果失败则返回错误
    '''
    err = None
    for _ in range(3):
        try:
            logger.info(f'{username} -> {mail_to}: 邮件主题为 "{subject}"')
            client = SMTPClient.get_logined_client(host, username, password)
            client.send_mail(mail_to, subject, relay_to, relay_name, mail_body, files)
            err = None
            break
        except smtplib.SMTPException as e:
            logger.exception('smtp错误')
            err = e
            continue
        except Exception as e:
            logger.exception('出现未知异常')
            # 出现未知异常
            err = e
            break
    return err


def handler(environ, start_response):
    context = environ['fc.context']
    request_uri = environ['fc.request_uri']
    for k, v in environ.items():
      if k.startswith('HTTP_'):
        # process custom request headers
        pass
    try:
        json_body = _get_json_body(environ)
        #邮件服务器地址
        host = json_body['host']
        # 邮件服务用户名
        username = json_body['username']
        # 邮件服务密码
        password = json_body['password']
        # 邮件发送给
        mail_to = json_body['mail_to']
        # 邮件主题
        subject = json_body['subject']
        relay_to = json_body.get('relay_to') or username
        relay_name = json_body.get('relay_name') or username.split('@', 1)[0]
        mail_body = json_body.get('mail_body', '')
        files = json_body.get('files', {})
    except Exception as e:
        return new_response(start_response, 400, '参数错误：%s' % str(e), None)

    err = sendmail(host, username, password, mail_to, subject, relay_to, relay_name, mail_body, files)
    if err is not None:
        return new_response(start_response, 500, '发送邮件失败: %s' % str(err), None)

    return new_response(start_response, 0, '发送邮件成功', {
        'username': username,
        'mail_to': mail_to,
        'subject': subject,
    })
