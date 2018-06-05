#!/usr/bin/env python2.7
# coding: utf-8

# SERVER
server_listen_port = 12345
server_debug_mode = True

# 监测模块日志配置
monitor_log_env = "develop"
monitor_log_target = "logs"
monitor_log_name = 'monitor'
monitor_log_size = 1000000
monitor_log_count = 100
monitor_log_level = "info"

# MySQL数据库配置
mysql_host = '123456'
mysql_port = 3306
mysql_user = 'root'
mysql_pwd = '123456'
mysql_db = 'monitor'

# 监测模块进程数和线程数
worker_process_count = 4
thread_number = 10

# SSH KEY
key_file = 'id_rsa'
key_pwd = None

# Fake info
fake_mail = True
