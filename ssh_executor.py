#!/usr/bin/env  python2.7
# -*- coding:utf8 -*-

import paramiko
import sys


class SSHExecutor(object):
    def __init__(self, ssh_ip, ssh_port, ssh_user, key_file, key_pwd=None):
        self.ssh_ip = ssh_ip
        self.ssh_port = ssh_port
        self.ssh_user = ssh_user
        self.key_file = key_file
        self.key_pwd = key_pwd
        self.client = None

    def open(self):
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        if self.key_pwd:
            private_key = paramiko.RSAKey.from_private_key_file(self.key_file, self.key_pwd)
        else:
            private_key = paramiko.RSAKey.from_private_key_file(self.key_file)
        self.client.connect(hostname=self.ssh_ip,
                            port=self.ssh_port,
                            username=self.ssh_user,
                            pkey=private_key)
        return self

    def execute(self, cmd):
        """ Return stdout, stderr
        :param cmd:
        """
        _in, _out, _err = self.client.exec_command(cmd, timeout=10)
        return _out.read(), _err.read()

    def close(self):
        self.client.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.client.close()


if __name__ == '__main__':
    reload(sys)
    sys.setdefaultencoding('utf-8')

    executor = SSHExecutor("172.18.6.8", 22, "lyg", "/Users/liyanguo/tmp/id_rsa")
    with executor.open() as client:
        o, e = client.execute("netstat -anop | grep 90")
        print("out: %s" % o)
        print("err: %s" % e)
