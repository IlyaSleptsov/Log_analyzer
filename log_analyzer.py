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
import operator
import json
import string
import argparse
from collections import namedtuple

try:
    import configparser
except ImportError:
    import ConfigParser as configparser

config = {
    "REPORT_SIZE": 1000,
    "REPORT_DIR": "./reports",
    "LOG_DIR": "./log",
    "LOG_FILE": "logs",
    "REGEX": r"^nginx-access-ui\.log-(\d{8})(\.gz)?$",
    "TEMPLATE_FILE": 'report.html'
}


def count_median(lst):
    """Computes median of list"""
    n = len(lst)
    if n < 1:
        return None
    if n % 2 == 1:
        return sorted(lst)[n//2]
    else:
        return sum(sorted(lst)[n//2-1:n//2+1])/2.0


def get_dict_from_config(config_path):
    """Parses config file and transferts it into dict"""
    cfg = configparser.RawConfigParser(allow_no_value=True)
    cfg.read(config_path)
    return dict((name.upper(), value) for (name, value) in cfg.items('default'))


def get_last_log_file(path_to_file, regex=re.compile(config['REGEX'])):
    """Finds last log file by date"""
    last_file = namedtuple('file', ['name', 'date'])
    log_name = log_date = None
    for file_name in os.listdir(path_to_file):
        match = re.search(regex, file_name)
        if match:
            date, ext = match.groups()
            current_file_date = datetime.datetime.strptime(date, '%Y%m%d')
            if log_name is None:
                log_name = os.path.join(path_to_file, file_name)
                log_date = current_file_date
            if current_file_date > log_date:
                log_name = os.path.join(path_to_file, file_name)
                log_date = current_file_date
    return last_file(name=log_name, date=log_date)


def parse_log_files(log_file):
    """Parses rows from log file"""
    if log_file.endswith('.gz'):
        log = gzip.open(log_file, 'rb')
    else:
        log = open(log_file)
    with log:
        for line in log:
            try:
                yield line.decode()
            except AttributeError:
                yield line


def get_url_and_time(line):
    """Extracts time and url from line of log file"""
    try:
        list_of_values = line.split(' ')
        url = list_of_values[7].strip()
        time = float(list_of_values[-1].strip())
    except Exception:
        return None, None

    return url, time


def extract_line_from_log_file(log_file,tresh=0.8):
    """Extracts information from log file lines """
    url_stats = collections.defaultdict()
    sum_urls = 0
    sum_time = 0
    sum_all = 0
    for line in log_file:
        url, time = get_url_and_time(line)
        if url and time:
            sum_urls += 1
            sum_time += time
            url_stats[url] = url_stats.get(url, list()) + [time]
        sum_all += 1
    if sum_urls / sum_all < tresh:
        raise Exception("There are too many mistakes in log file line")
    result = []
    for url, time in url_stats.items():
        result.append({
            'url': url,
            'count': len(time),
            'count_perc': round(len(time) / sum_urls, 2),
            'time_sum': sum(time),
            'time_perc': round(sum(time) / sum_time, 2),
            'time_avg': round(sum(time)/len(time), 2),
            'time_max': max(time),
            'time_med': count_median(time)
        })
    result.sort(key=operator.itemgetter('time_sum'), reverse=True)
    return result


def make_report_1(data_to_report, file_name, template_file):
    """Generates report"""
    template_report = string.Template('$json_table').substitute(json_table = json.dumps(data_to_report))
    try:
        with open(file_name, 'w') as f:
            f.write(template_report)
    except Exception as e:
        logging.info('Problem with writing file: {}'.format(e))


def make_report(data_to_report, file_name, template_file):
    with open(template_file, 'r') as tf:
        template = tf.read()
    template = template.replace('$table_json', json.dumps(data_to_report))
    try:
        with open(file_name, 'w') as f:
            f.write(template)
    except Exception as e:
        logging.info('Problem with writing file: {}'.format(e))


def main(config):
    last_file = get_last_log_file(config['LOG_DIR'])
    if os.path.isfile(last_file.name):
        report_file = os.path.join(config['REPORT_DIR'],
                                   'report_{}.html'.format(last_file.date.strftime('%Y-%m-%d')))
        if not os.path.exists(report_file):
            result = extract_line_from_log_file(parse_log_files(last_file.name))
            if result:
                make_report(result[0:config['REPORT_SIZE']], report_file, config['TEMPLATE_FILE'])
                logging.info('Report is created')
            else:
                logging.info('Something went wrong with extracting lines')
        else:
            logging.info('{} logfile is already analyzed'.format(report_file))
    else:
        logging.info('Program did not find relevant log files')


if __name__ == "__main__":
    arg = argparse.ArgumentParser()
    arg.add_argument('--config', type=str, dest='config', nargs='?',
                     default='configs/cfg')
    args = arg.parse_args()

    if os.path.isfile(args.config):
        config.update(get_dict_from_config(args.config))

        logging.basicConfig(format=u'[%(asctime)s] %(levelname).1s %(message)s',
                            datefmt='%Y.%m.%d %H:%M:%S',
                            filename=config.get('LOG_FILE'),
                            filemode='a',
                            level=logging.INFO)
        try:
            main(config)
        except Exception as e:
            logging.exception(e)
    else:
        raise NameError('This {} config file is not correct'.format(args.config))