import unittest
import log_analyzer
import datetime

class LogAnalyzerTests(unittest.TestCase):
    def test_get_date_from_file_name(self):
        self.assertEqual(log_analyzer.get_date_from_file_name('nginx-access-ui.log-20170630.gz'),datetime.datetime(2017,6,30))

if __name__ == '__main__':
    unittest.main()