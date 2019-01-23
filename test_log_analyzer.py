import unittest
import log_analyzer
import datetime

class LogAnalyzerTests(unittest.TestCase):
    def test_get_date_from_file_name(self):
        self.assertEqual(log_analyzer.get_date_from_file_name('nginx-access-ui.log-20170630.gz') ,datetime.datetime(2017,6,30))
    def test_median(self):
        self.assertEqual(log_analyzer.count_median([1,1,2,3,3]),2)


if __name__ == '__main__':
    unittest.main()