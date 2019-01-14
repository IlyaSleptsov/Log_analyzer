#!/usr/bin/env python
# -*- coding: utf-8 -*-


# log_format ui_short '$remote_addr  $remote_user $http_x_real_ip [$time_local] "$request" '
#                     '$status $body_bytes_sent "$http_referer" '
#                     '"$http_user_agent" "$http_x_forwarded_for" "$http_X_REQUEST_ID" "$http_X_RB_USER" '
#                     '$request_time';

import os
import gzip
import logging
import datetime
import re
import collections
import numpy as np
import operator
import json
import string
import argparse
import pandas as pd

try:
    import configparser
except ImportError:
    import ConfigParser as configparser

config = {
    "REPORT_SIZE": 1000,
    "REPORT_DIR": "./reports",
    "LOG_DIR": "./log",
    "FILE_FOR_LOGS": "logs"
}

regex_for_log_file = re.compile('nginx-access-ui.log-\n|\d{8}')


def get_date_from_file_name(file_name):
    """Finds date in filename string and transforms it to datetime"""
    return datetime.datetime.strptime(re.search(regex_for_log_file, file_name)[0], '%Y%m%d')


def get_dict_from_config(config_path):
    """Parses config file and transferts it into dict"""
    cfg = configparser.RawConfigParser(allow_no_value=True)
    cfg.read(config_path)
    return dict((name.upper(), value) for (name, value) in cfg.items('default'))


def get_last_log_file(path_to_file):
    """Finds last log file by date"""
    last_file = {'file_name': 'nothing', 'date': datetime.datetime(2001, 1, 1)}
    for file_name in os.listdir(path_to_file):
        try:
            if re.search(regex_for_log_file, file_name):
                log_date = get_date_from_file_name(file_name)
                if log_date > last_file['date']:
                    last_file['file_name'] = os.path.join(path_to_file, file_name)
                    last_file['date'] = log_date
        except Exception as e:
            logging.info('Problem {} with file {}'.format(e, file_name))

    return last_file


def parse_log_files(log_file):
    """Parses rows from log file"""
    if log_file.endswith('.gz'):
        log = gzip.open(log_file, 'rb')
    else:
        log = open(log_file)
    for line in log:
        yield line.decode()
    log.close()


def get_url_and_time(line):
    list_of_values = line.split(' ')
    try:
        url = list_of_values[7].strip()
        time = float(list_of_values[-1].strip())
    except Exception:
        return None, None
    return url, time


def extract_line_from_log_file(log_file):
    """Extracts information from log file lines """
    url_stats = collections.defaultdict()
    sum_urls = 0
    sum_time = 0
    for line in log_file:
        url, time = get_url_and_time(line)
        if url and time:
            sum_urls += 1
            sum_time += time
            url_stats[url] = url_stats.get(url, list()) + [time]
    result = []
    for url, time in url_stats.items():
        result.append({
            'url': url,
            'count': len(time),
            'count_perc': round(len(time) / sum_urls, 2),
            'time_sum': sum(time),
            'time_perc': round(sum(time) / sum_time, 2),
            'time_avg': round(np.mean(time), 2),
            'time_max': max(time),
            'time_med': np.median(time)
        })
    result.sort(key=operator.itemgetter('count'), reverse=True)
    return result


def make_report(data_to_report, file_name):
    """Generates report"""
    template_report = string.Template('$json_table').substitute(json_table=json.dumps(data_to_report))
    try:
        with open(file_name, 'w') as f:
            f.write(template_report)
    except Exception as e:
        logging.info('Problem with writing file: {}'.format(e))


def main(config):
    last_file = get_last_log_file(config['LOG_DIR'])
    if os.path.isfile(last_file['file_name']):
        report_file = os.path.join(config['REPORT_DIR'],
                                   'report_{}.html'.format(last_file['date'].strftime('%Y-%m-%d')))
        if not os.path.exists(report_file):
            result = extract_line_from_log_file(parse_log_files(last_file['file_name']))
            if result:
                make_report(result[0:config['REPORT_SIZE']], report_file)
                pd.DataFrame(result[0:config['REPORT_SIZE']]).to_html(report_file)
                logging.info('Report is created')
            else:
                logging.info('Something went wrong with extracting lines')
        else:
            logging.info('Last logfile is already analyzed')
    else:
        logging.info('Program did not find relevant log files')

    print(last_file)


if __name__ == "__main__":
    arg = argparse.ArgumentParser()
    arg.add_argument('--config', type=str, dest='config', nargs='?',
                     default='configs/cfg')
    args = arg.parse_args()

    if os.path.isfile(args.config):
        config.update(get_dict_from_config(args.config))

        logging.basicConfig(format=u'[%(asctime)s] %(levelname).1s %(message)s',
                            datefmt='%Y.%m.%d %H:%M:%S',
                            filename=config.get('FILE_FOR_LOGS'),
                            filemode='a',
                            level=logging.INFO)

        main(config)
    else:
        raise NameError('This {} config file is not correct'.format(args.config))
