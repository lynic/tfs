#!/usr/bin/env python
# -*- coding: utf-8 -*-

import tushare as ts
import arctic
import six

from common import Config

# indexes = [{'code': '000001', 'name': 'sh'}, {'code': '399001', 'name': 'sz'}, {'code': '399005', 'name': 'zx'}, {'code': '399006', 'name': 'cy'}]

if __name__ == '__main__':
    config = Config('/etc/config.yaml')
    store = arctic.Arctic(config['mongodb']['server'], config['mongodb']['port'])

    lib_name = 'Stocks_Daily.index'
    try:
        library = store.get_library(lib_name)
    except Exception as ex:
        print(six.text_type(ex))
        print('Initilize library %s' % lib_name) 
        store.initialize_library(lib_name)
        library = store[lib_name]

    df = ts.get_index()
    indexes = df['code'].tolist()
    for index in indexes:
        print('Handle %s %s' % (lib_name, index))
        data = ts.get_k_data(index, index=True, start='1990-01-01')
        library.write(index, data)
