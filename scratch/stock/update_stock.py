#!/usr/bin/env python
# -*- coding: utf-8 -*-

import tushare as ts
import arctic
import six

from common import Config
from common import ArgParser
from common import ThreadPool

debug=False

def get_library(lib_name):
    config = Config('/etc/config.yaml')
    store = arctic.Arctic(config['mongodb']['server'], config['mongodb']['port'])
    try:
        library = store.get_library(lib_name)
    except Exception as ex:
        print(six.text_type(ex))
        print('Initilize library %s' % lib_name) 
        store.initialize_library(lib_name)
        library = store[lib_name]
    return library

def update_stock(stock_id, lib_name, update=False):
    config = Config('/etc/config.yaml')
    store = arctic.Arctic(config['mongodb']['server'], config['mongodb']['port'])
    library = store.get_library(lib_name)
    store_flag = True
    if update:
        print('Updating data of %s' % stock_id)
        old_data = library.read(stock_id).data
        new_data = ts.get_k_data(stock_id, autype=autype)
        if new_data.empty:
            return
        new_data.set_index('date', inplace=True)
        try:
            data = old_data.append(new_data)
            data.drop_duplicates(inplace=True)
            # Do not store data if no update
            if len(data) == len(old_data):
                store_flag = False
        except Exception as ex:
            print(six.text_type(ex))
    else:
        print('Building data of %s' % stock_id)
        data = ts.get_k_data(stock_id, autype=autype, start='1990-01-01')
        if data.empty:
            return
        data.set_index('date', inplace=True)
    if store_flag:
        print('Storing data of %s' % stock_id)
        library.write(stock_id, data)

if __name__ == '__main__':
    parser = ArgParser()
    parser.add('--autype')
    if parser['autype']:
        assert parser['autype'] in ['hfq', 'qfq', 'none']
        autype = parser['autype']
    else:
        autype = 'none'
    stocks = ts.get_stock_basics()
    stock_ids = stocks.index.tolist()

    lib_name = 'Stocks_Daily.%s' % autype
    library = get_library(lib_name)
    stored_ids = library.list_symbols()

    pool = ThreadPool(4, debug=debug)
    for stock_id in stock_ids:
        update = False
        if stock_id in stored_ids:
            update = True
        # update_stock(stock_id, library, update=update)
        pool.add_task(update_stock, stock_id, lib_name, update)
    pool.run()
