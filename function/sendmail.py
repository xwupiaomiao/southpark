#!/usr/bin/python3
# -*- coding:utf-8 -*-


import smtplib, os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from email.header import Header
import base64


class SendMail(object):
    def __init__(self, username, passwd, email_host, recv, title, content, file=None, imagefile=None, ssl=False,
                 port=25, ssl_port=465):
        '''
        :param username: 用户名
        :param passwd: 密码
        :param email_host: smtp服务器地址
        :param recv: 收件人，多个要传list ['a@qq.com','b@qq.com]
        :param title: 邮件标题
        :param content: 邮件正文
        :param file: 附件路径，如果不在当前目录下，要写绝对路径，默认没有附件
        :param imagefile:  图片路径，如果不在当前目录下，要写绝对路径，默认没有图片
        :param ssl: 是否安全链接，默认为普通
        :param port: 非安全链接端口，默认为25
        :param ssl_port: 安全链接端口，默认为465
        '''
        self.username = username  # 用户名
        self.passwd = passwd  # 密码
        self.recv = recv  # 收件人，多个要传list ['a@qq.com','b@qq.com]
        self.title = title  # 邮件标题
        self.content = content  # 邮件正文
        self.file = file  # 附件路径，如果不在当前目录下，要写绝对路径
        self.imagefile = imagefile  # 图片路径，如果不在当前目录下，要写绝对路径
        self.email_host = email_host  # smtp服务器地址
        self.port = port  # 普通端口
        self.ssl = ssl  # 是否安全链接
        self.ssl_port = ssl_port  # 安全链接端口

    def send_mail(self):
        # msg = MIMEMultipart()
        msg = MIMEMultipart('mixed')
        # 发送内容的对象
        if self.file:  # 处理附件的
            file_name = os.path.split(self.file)[-1]  # 只取文件名，不取路径
            try:
                f = open(self.file, 'rb').read()
            except Exception as e:
                raise Exception('附件打不开！！！！')
            else:
                att = MIMEText(f, "base64", "utf-8")
                att["Content-Type"] = 'application/octet-stream'
                # base64.b64encode(file_name.encode()).decode()
                new_file_name = '=?utf-8?b?' + base64.b64encode(file_name.encode()).decode() + '?='
                # 这里是处理文件名为中文名的，必须这么写
                att["Content-Disposition"] = 'attachment; filename="%s"' % (new_file_name)
                msg.attach(att)
        if self.imagefile:
            try:
                sendimagefile = open(self.imagefile, 'rb').read()
            except Exception as e:
                raise Exception('图片无法打开！！！！')
            else:
                image = MIMEImage(sendimagefile)
                image.add_header('Content-ID', '<image1>')
                msg.attach(image)
        text_html = MIMEText(self.content, 'html', 'utf-8')
        msg.attach(text_html)
        # msg.attach(MIMEText(self.content))  # 邮件正文的内容
        msg['Subject'] = self.title  # 邮件主题
        msg['From'] = self.username  # 发送者账号
        msg['To'] = ','.join(self.recv)  # 接收者账号列表
        if self.ssl:
            self.smtp = smtplib.SMTP_SSL(self.email_host, port=self.ssl_port)
        else:
            self.smtp = smtplib.SMTP(self.email_host, port=self.port)
        # 发送邮件服务器的对象
        self.smtp.login(self.username, self.passwd)
        try:
            self.smtp.sendmail(self.username, self.recv, msg.as_string())
            pass
        except Exception as e:
            print('出错了。。', e)
        else:
            print('发送成功！')
        self.smtp.quit()


if __name__ == '__main__':
    """
    发送正文中的图片:由于包含未被许可的信息，网易邮箱定义为垃圾邮件，报554 DT:SPM ：<p><img src="cid:image1"></p>
    """
    m = SendMail(
        username='xxxx@qq.com',
        passwd='xxxxxxx',
        email_host='smtp.exmail.qq.com',
        recv=['xxxx@163.com', 'xxxx@qq.com'],
        title='发送邮件',
        content="""
        <html>  
          <head></head>  
          <body>  
            <p>Hi!<br>  
               How are you?<br>  
               Here is the <a href="http://www.baidu.com">link</a> you wanted.<br> 
            </p>
            <img src="cid:image1">
          </body>  
        </html>  
        """,
        file=r'测试附件.xls',
        imagefile=r'test.png',
        ssl=True,
    )
    m.send_mail()
