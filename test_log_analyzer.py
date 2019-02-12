import unittest
from unittest import mock
import log_analyzer
import datetime
import os
import collections
import operator

LOG_LINES = [
    '1.196.116.32 -  - [29/Jun/2017:03:50:22 +0300] "GET /api/v2/banner/25019354 HTTP/1.1" 200 927 "-" "Lynx/2.8.8dev.9 libwww-FM/2.14 SSL-MM/1.4.1 GNUTLS/2.10.5" "-" "1498697422-2190034393-4708-9752759" "dc7161be3" 0.390',
    '1.99.174.176 3b81f63526fa8  - [29/Jun/2017:03:50:22 +0300] "GET /api/1/photogenic_banners/list/?server_name=WIN7RB4 HTTP/1.1" 200 12 "-" "Python-urllib/2.7" "-" "1498697422-32900793-4708-9752770" "-" 0.133',
    '1.169.137.128 -  - [29/Jun/2017:03:50:22 +0300] "GET /api/v2/banner/16852664 HTTP/1.1" 200 19415 "-" "Slotovod" "-" "1498697422-2118016444-4708-9752769" "712e90144abee9" 0.199',
    '1.199.4.96 -  - [29/Jun/2017:03:50:22 +0300] "GET /api/v2/slot/4705/groups HTTP/1.1" 200 2613 "-" "Lynx/2.8.8dev.9 libwww-FM/2.14 SSL-MM/1.4.1 GNUTLS/2.10.5" "-" "1498697422-3800516057-4708-9752745" "2a828197ae235b0b3cb" 0.704',
    '1.168.65.96 -  - [29/Jun/2017:03:50:22 +0300] "GET /api/v2/internal/banner/24294027/info HTTP/1.1" 200 407 "-" "-" "-" "1498697422-2539198130-4709-9928846" "89f7f1be37d" 0.146']
BAD_LOG_LINES = [
    '1.196.116.32 -  - [29/Jun/2017:03:50:22 +0300] "GET /api/v2/banner/25019354 HTTP/1.1" 200 927 "-" "Lynx/2.8.8dev.9 libwww-FM/2.14 SSL-MM/1.4.1 GNUTLS/2.10.5" "-" "1498697422-2190034393-4708-9752759" "dc7161be3" 0.390',
    'bad_line',
    'another_bad_line'
]


class LogAnalyzerTests(unittest.TestCase):
    def setUp(self):
        self.config = {
            "REPORT_SIZE": 1000,
            "REPORT_DIR": "./reports",
            "LOG_DIR": "./log",
            "LOG_FILE": "logs",
            "REGEX": r"^nginx-access-ui\.log-(\d{8})(\.gz)?$",
        }

    def test_median(self):
        self.assertEqual(log_analyzer.count_median([1, 1, 2, 3, 3]), 2)

    @mock.patch.object(os, 'listdir')
    def test_get_last_log_file(self, mock_listdir):
        mock_listdir.return_value = ['nginx-access-ui.log-20170630',
                                     'nginx-access-ui.log-20170629',
                                     'nginx-access-ui.log-20160730']
        last_file = log_analyzer.get_last_log_file(self.config['LOG_DIR'])
        self.assertEqual(last_file.date, datetime.datetime(2017, 6, 30))

    @mock.patch.object(os, 'listdir')
    def test_finds_correct_file(self, mock_listdir):
        mock_listdir.return_value = ['something_wrong_20170630',
                                     'nginx-access-ui.log-20170630.gz',
                                     'nginx-access-ui.log-20160730.py',
                                     'nginx-access-ui.log-20160730.something_wrong_again']
        last_file = log_analyzer.get_last_log_file(self.config['LOG_DIR'])
        self.assertEqual(last_file.name, self.config['LOG_DIR'] + '\\' + 'nginx-access-ui.log-20170630.gz')

    def test_extract_line_from_log_file(self):
        results = log_analyzer.extract_line_from_log_file(LOG_LINES)
        self.assertGreater(len(results), 0)

    def test_extract_line_threshold(self):
        with self.assertRaises(Exception) as context:
            log_analyzer.extract_line_from_log_file(BAD_LOG_LINES)
            self.assertTrue("There are too many mistakes in log file line" in context.exception)


if __name__ == '__main__':
    unittest.main()
