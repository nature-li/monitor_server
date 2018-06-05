#!/usr/bin/env  python2.7
# -*- coding:utf8 -*-

import sys
import tornado
import tornado.web
import tornado.ioloop
from config import config
from defer import Defer
import signal
import json
import datetime
from mt_log.logger import Logger
from status_holder import StatusCode
from controller import Controller


# Get detail monitor status for one job
class ApiGetDetailStatus(tornado.web.RequestHandler):
    def post(self):
        Logger.info(json.dumps(self.request.arguments, ensure_ascii=False), self.request.uri)

        # Get service id
        a_dict = dict()
        a_dict['code'] = -1
        a_dict['healthy_code'] = StatusCode.WHITE_CODE
        a_dict['command_healthy_code'] = dict()
        a_dict['monitor_time'] = '1970-01-01 00:00:00'

        service_id = self.get_argument("service_id")
        if not service_id or not service_id.isdigit():
            self.write(json.dumps(a_dict, ensure_ascii=False))

        # Query status data
        service_id = int(service_id)
        result = Controller.status_holder.get_one_full_status(service_id)
        if result is None:
            self.write(json.dumps(a_dict, ensure_ascii=False))

        # Return status data
        (healthy_code, cmd_status, last_t) = result
        last = datetime.datetime.fromtimestamp(last_t).strftime('%Y-%m-%d %H:%M:%S')
        a_dict['code'] = 0
        a_dict['healthy_code'] = healthy_code
        a_dict['command_healthy_code'] = cmd_status
        a_dict['monitor_time'] = last
        self.write(json.dumps(a_dict, ensure_ascii=False))


# Get monitor status for a list of job
class ApiMonitorStatus(tornado.web.RequestHandler):
    def post(self):
        Logger.info(json.dumps(self.request.arguments, ensure_ascii=False), self.request.uri)

        a_dict = dict()
        a_dict['code'] = -1
        a_dict['content'] = dict()

        # Get service id
        service_id_string = self.get_argument("service_id")
        """:type: string"""
        if not service_id_string:
            self.write(json.dumps(a_dict, ensure_ascii=False))

        # Query status data
        raw_service_id_list = service_id_string.strip().split(',')
        """:type: list[string]"""
        service_id_set = set()
        for raw_service_id in raw_service_id_list:
            if raw_service_id.isdigit():
                service_id_set.add(int(raw_service_id))
        result = Controller.status_holder.get_group_status(service_id_set)
        if result is None:
            self.write(json.dumps(a_dict, ensure_ascii=False))

        a_dict['code'] = 0
        a_dict['content'] = result
        self.write(json.dumps(a_dict, ensure_ascii=False))


def __main__():
    # 设置编码
    reload(sys)
    sys.setdefaultencoding('utf-8')

    # 初始化日志
    result = Logger.init(config.monitor_log_env, config.monitor_log_target, config.monitor_log_name, config.monitor_log_size,
                         config.monitor_log_count, multiprocess=True)
    if not result:
        print 'init logger failed'
        return False

    with Defer(Logger.close):
        # Start worker process
        signal.signal(signal.SIGTERM, Controller.master_signal_handler)
        Controller.start_worker_process()

        print "server is starting..."
        Logger.info("server is starting...")
        Logger.info("config.server_listen_port: %s" % config.server_listen_port)
        app = tornado.web.Application(
            [
                (r'/api_get_detail_status', ApiGetDetailStatus),
                (r'/api_monitor_status', ApiMonitorStatus),
            ],
            xsrf_cookies=False,
            debug=config.server_debug_mode
        )
        # Listen on a port
        app.listen(config.server_listen_port)
        Controller.instance = tornado.ioloop.IOLoop.current()
        Controller.instance.start()


if __name__ == "__main__":
    __main__()
