# -*- coding: utf-8 -*-
import libtorrent as lt


class ResumeData(object):
    def __init__(self, client):
        self.th = client.th
        self.ses = client.ses
        self.cache = client.cache
        self.client = client

    def save_resume_data(self):
        if self.th.need_save_resume_data() and self.th.is_valid() and self.client.meta:
            self.th.save_resume_data()
            alerts = []
            while not alerts:
                self.ses.wait_for_alert(1000)
                alerts = filter(
                    lambda x: lt.alert.what(x) in ('save_resume_data_failed_alert', 'save_resume_data_alert'),
                    self.ses.pop_alerts()
                )

            if lt.alert.what(alerts[0]) == 'save_resume_data_alert':
                self.cache.save_resume(str(self.th.get_torrent_info().info_hash()), lt.bencode(alerts[0].resume_data))
