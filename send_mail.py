#!/usr/bin/env  python2.7
# -*- coding:utf8 -*-
import requests
import traceback
from mt_log.logger import Logger
from config import config
import datetime


class SendMail(object):
    @classmethod
    def send(cls, receivers, subject, content):
        """
        :type receivers: string
        :type subject: string
        :type content: string
        :return:
        """
        try:
            if config.fake_mail:
                Logger.info('receivers=[%s], subject=[%s], content=[%s]' % (receivers, subject, content))
                return

            url = 'http://fuck.you.com/send_mail'
            a_dict = {
                'receiver': receivers,
                'subject': subject,
                'content': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') + ": " + content
            }

            ret = requests.post(url, data=a_dict)
            Logger.info("http_code[%s], http_response[%s]" % (ret.status_code, ret.text))
        except:
            Logger.error(traceback.format_exc())
