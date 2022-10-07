#!/usr/bin/env python
# -*- coding:utf-8 -*-

import paramiko
from .conndb import condb


class comupload(object):
    def __init__(self, hostname, project=None, username='root', port=22):
        self.private_key = paramiko.RSAKey.from_private_key_file('/root/.ssh/id_rsa')
        self.hostname = hostname
        self.username = username
        self.port = port
        self.project = project
        self.transport = paramiko.Transport((self.hostname, self.port))
        self.transport.connect(username=self.username, pkey=self.private_key)
        self.sftp = paramiko.SFTPClient.from_transport(self.transport)
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())  # 允许连接不存在在know_hosts文件里的主机
        self.client.connect(hostname=self.hostname, port=self.port, username=self.username, pkey=self.private_key)

    def upload(self, local_path, remote_path):
        # 将文件上传至服务器
        if self.project:
            self.sftp.put(local_path, remote_path, callback=self.__callback)
        else:
            self.sftp.put(local_path, remote_path)

    def download(self, remotepath, localpath):
        # 将文件下载到本地
        self.sftp.get(remotepath, localpath)

    def comand(self, com):
        # 执行命令
        stdin, stdout, stderr = self.client.exec_command(com)
        result = stdout.read().decode()
        reserr = stderr.read().decode()
        return result, reserr

    def exec_com(self, com):
        # 执行命令,返回命令结果和状态码
        self.channel = self.client.get_transport().open_session()
        self.channel.exec_command(com)
        stdout = self.channel.makefile().read()
        stderr = self.channel.makefile_stderr().read()
        exit_code = self.channel.recv_exit_status()
        self.channel.close()
        return stdout, stderr, exit_code

    def __callback(self, send, total):
            '''
            需求： 制作传输进度条
            1. CallBack方法获取总字节数和已传输字节数
            2. 通过计算获取已传输字节数占总字节数的百分比
            3. 制作进度条
            :param send:
            :param total:
            :return:
            '''
        #     end = '' if send != total else '\n'
        #     # 上传进度条
        #     print('\r    |{:<50}| {:.2f} M [{:.2f}%]'.format('#' * int(send * 100 / total / 2), send / 1024 / 1024,
        #                                                      send * 100 / total), end=end, flush=True)
            sendsize = send / 1024 / 1024
            percent = send * 100 / total
            condb(
                'UPDATE `project` SET `sendsize`="{}",`percent`="{}" WHERE `name`="{}";'.format(sendsize, percent,self.project))

    def sshclose(self):
        # 关闭连接
        self.sftp.close()
        self.client.close()


if __name__ == '__main__':
    ssh_sftp = comupload('172.17.0.5')
    ssh_sftp.comand(
        'cd /var/www/html && tar xf momostorytime.tar.gz && chown -R root.root momostorytime && rm -fr momostorytime.tar.gz')
