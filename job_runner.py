#!/usr/bin/env  python2.7
# -*- coding:utf8 -*-
from job_detail import JobDetail
from job_holder import JobHolder
from status_holder import StatusHolder, StatusCode
from gevent import Greenlet
from mt_log.logger import Logger
from send_mail import SendMail
from defer import Defer


class JobRunner(Greenlet):
    def __init__(self, a_job, job_holder, status_holder):
        """
        :type a_job: JobDetail
        :type job_holder: JobHolder
        :type status_holder: StatusHolder
        """
        Greenlet.__init__(self)
        self.a_job = a_job
        self.job_holder = job_holder
        self.status_holder = status_holder

    def run(self):
        try:
            # Clear job status if job is not active
            if not self.a_job.is_active():
                self.status_holder.clear_one_status(self.a_job.get_id())
                self.job_holder.del_job(self.a_job.get_id())
                return

            # Do one job
            self.a_job.login()
            with Defer(self.a_job.logout):
                self.do_job()
            self.job_holder.del_job(self.a_job.get_id())
        except Exception, e:
            Logger.error(e.message)

    def do_job(self):
        try:
            job_id = self.a_job.get_id()
            service_name = self.a_job.get_service_name()
            healthy_code = self.a_job.do_all_check()

            # Refresh job status
            Logger.report('job_id[%s] [%s] is healthy_code[%s]' % (job_id, service_name, healthy_code))
            self.status_holder.set_one_status(job_id, healthy_code, self.a_job.get_check_cmd_healthy_code())

            # Success
            if healthy_code is StatusCode.GREEN_CODE:
                return

            # Monitor operation occur error
            if healthy_code == StatusCode.WHITE_CODE or healthy_code == StatusCode.YELLOW_CODE:
                content = 'job_id[%s] [%s], healthy_code[%s] cat not be monitored successfully' % (job_id, service_name, healthy_code)
                Logger.error(content)
                SendMail.send(self.a_job.get_mail_receiver(), service_name, content)
                return

            # Do not need to be recovered
            if not self.a_job.get_auto_recover():
                return

            # Stopped process
            stopped = self.a_job.stop()
            if stopped is None:
                content = 'job_id[%s] [%s] stop failed' % (job_id, self.a_job.get_service_name())
                Logger.info(content)
                return

            # Check relies
            relies = self.a_job.get_all_rely()
            if not self.status_holder.is_group_healthy(relies):
                content = 'services job_id[%s] [%s] relying is not healthy' % (job_id, self.a_job.get_service_name())
                Logger.info(content)
                return

            # Start process
            ok = self.a_job.start()
            if not ok:
                content = 'job_id[%s] [%s] start failed' % (job_id, self.a_job.get_service_name())
                Logger.info(content)
                return

            # Start ok
            content = 'job_id[%s] [%s] start success' % (job_id, self.a_job.get_service_name())
            Logger.info(content)
            SendMail.send(self.a_job.get_mail_receiver(), self.a_job.get_service_name(), content)
        except Exception, e:
            Logger.error(e.message)

