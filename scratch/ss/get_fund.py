#!/usr/bin/env python
# -*- coding: utf-8 -*-

import six
import time
import traceback
import re
from pprint import pprint
from datetime import datetime
import json

from common import Pool
from common import ThreadPool
from common import get_web
from common import Store
from common import ArgParser
from common import Config
from common import Mail


def store_fund_detail(fund_detail):
    if not fund_detail:
        return
    config = Config('/etc/config.yaml')
    db = Store(config['mongodb']['server'], config['mongodb']['port'],
               'ss', 'fund_details')
    print('Storing fund_detail %s' % fund_detail['fundNo'])
    return db.put(fund_detail, key='fundNo')

def get_fund_detail(fund):
    print('Getting fund_detail %s' % fund['fundNo'])
    url = 'http://gs.amac.org.cn/amac-infodisc/res/pof/fund/%s' % fund['url']
    soup = get_web(url, encoding='UTF-8')
    if not soup:
        return {}
    content = soup.find('tbody').find_all('td')
    # datetime.strptime('2011-01-01', '%Y-%m-%d')
    # name = 'test'
    ret = {
        'name': content[1].get_text(),
        'fundNo': content[4].get_text(),
        'created_time': datetime.strptime(content[6].get_text(), '%Y-%m-%d'),
        'record_time': datetime.strptime(content[8].get_text(), '%Y-%m-%d'),
        'record_period': content[10].get_text(),
        'fund_type': content[12].get_text(),
        'currency': content[14].get_text(),
        'manager': content[16].get_text(),
        'manage_type': content[18].get_text(),
        'trustee': content[20].get_text(),
        'investment_area': content[22].get_text(),
        'status': content[24].get_text(),
        'update_time': datetime.strptime(content[26].get_text(), '%Y-%m-%d'),
        'notice': content[28].get_text(),
        'report_month': content[31].get_text(),
        'report_half_year': content[33].get_text(),
        'report_year': content[35].get_text(),
        'report_quarter': content[37].get_text(),
    }
    return ret

def store_fund(fund):
    print('Storing fund %s' % fund['fundNo'])
    config = Config('/etc/config.yaml')
    db = Store(config['mongodb']['server'], config['mongodb']['port'],
               'ss', 'fund_list')
    fund['putOnRecordDate'] = datetime.fromtimestamp((fund['putOnRecordDate'] or 0)/1e3)
    fund['establishDate'] = datetime.fromtimestamp((fund['establishDate'] or 0)/1e3)
    return db.put(fund, key='fundNo')

def _thread_fund_detail(fund):
    fund_detail = get_fund_detail(fund)
    store_fund_detail(fund_detail)

def get_all_funds(debug=False):
    print('Getting fund list')
    url = 'http://gs.amac.org.cn/amac-infodisc/api/pof/fund?page=0&size=100000'
    fund_list = get_web(url, data='{}', encoding='utf-8')
    config = Config('/etc/config.yaml')
    db = Store(config['mongodb']['server'], config['mongodb']['port'],
               'ss', 'fund_list')
    db2 = Store(config['mongodb']['server'], config['mongodb']['port'],
               'ss', 'fund_details')
    stored_fund = db.get_field(key='fundNo')
    sotred_fund_details = db2.get_field(key='fundNo')
    pool = ThreadPool(10, debug=debug)
    for fund in fund_list['content']:
        if fund['fundNo'] not in stored_fund:
            pool.add_task(store_fund, fund)
        if fund['fundNo'] not in sotred_fund_details:
            pool.add_task(_thread_fund_detail, fund)
    pool.run()
    # import ipdb;ipdb.set_trace()
    return fund_list['content']

if __name__ == '__main__':
    # Rebuild tmp storage
    publishers = []
    books = []
    config = Config('/etc/config.yaml')
    db2 = Store(config['mongodb']['server'], config['mongodb']['port'],
                'tmp', 'cheaper_books', rebuild=True)
    parser = ArgParser()
    parser.add('--debug', action='store_true', default=False)
    parser.add('--update', action='store_true')
    # import ipdb;ipdb.set_trace()
    funds = get_all_funds(debug=parser['debug'])

