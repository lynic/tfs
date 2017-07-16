#!/usr/bin/env python

from arctic import Arctic
from pandas import DataFrame

from common import Config
from common import ThreadPool


config = Config('/etc/config.yaml')
store = Arctic("{}:{}".format(config['mongodb']['server'], config['mongodb']['port']))

begin_date = '2001-01-01'

def get_stock_ids():
    lib = store.get_library('Stocks_Daily.hfq')
    return lib.list_symbols()

def get_total_dates():
    index_lib = store.get_library('Stocks_Daily.index')
    index_datas = index_lib.read('000001').data
    index_datas = index_datas.loc[index_datas['date'] > begin_date]
    index_dates = index_datas[['date']]
    return index_dates

def get_stock_datas(stock_id):
    hfq_lib = store.get_library('Stocks_Daily.hfq')
    stock_datas = hfq_lib.read(stock_id).data
    stock_datas = stock_datas.loc[stock_datas.index > begin_date]
    return stock_datas

def store_normalize_data(datas):
    lib_name = 'Stocks_Daily.norm'
    try:
        norm_lib = store.get_library(lib_name)
    except Exception as ex:
        print("Initialize {}".format(lib_name))
        store.initialize_library(lib_name)
        norm_lib = store[lib_name]
    stock_id = datas['code'][0]
    print('Storing {}'.format(stock_id))
    norm_lib.write(stock_id, datas)

def read_normalize_data(stock_id):
    lib_name = 'Stocks_Daily.norm'
    try:
        norm_lib = store.get_library(lib_name)
        stock_datas = norm_lib.read(stock_id).data
    except Exception as ex:
        return None
    return stock_datas

def normalize_stock(stock_id, index_dates):
    assert isinstance(index_dates, DataFrame)
    # Use norm datas directly if exists
    norm_datas = read_normalize_data(stock_id)
    if norm_datas is not None and len(norm_datas) == len(index_dates):
        return None
    print('Handling {}'.format(stock_id))
    if norm_datas is not None:
        stock_datas = norm_datas
    else:
        stock_datas = get_stock_datas(stock_id)
    stock_id = stock_datas['code'][0]
    # Not yet IPO
    for date in index_dates.loc[index_dates['date'] < stock_datas.index[0]]['date'].tolist():
        new_row = DataFrame([{'open': 0.0, 'close': 0.0, 'high': 0.0,
                             'low': 0.0, 'volume': 0.0, 'code': stock_id, 'date': date}],
                            index=[0])
        new_row.set_index('date', inplace=True)
        stock_datas = stock_datas.append(new_row)
    stock_datas.sort_index(inplace=True)
    # suspend trade days
    diff_dates = set(index_dates.loc[index_dates['date'] >= stock_datas.index[0]]['date'].tolist()) - set(stock_datas.index.tolist())
    for date in diff_dates:
        last_close = stock_datas.loc[stock_datas.index < date]['close'][-1]
        new_row = DataFrame([
            {'open': last_close, 'close': last_close, 'high': last_close,
             'low': last_close, 'volume': 0.0, 'code': stock_id, 'date': date}], index=[0])
        new_row.set_index('date', inplace=True)
        stock_datas = stock_datas.append(new_row)
        stock_datas.sort_index(inplace=True)
    assert len(index_dates) == len(stock_datas)
    store_normalize_data(stock_datas)
    return stock_datas

if __name__ == '__main__':
    stocks = get_stock_ids()
    dates = get_total_dates()
    # import ipdb;ipdb.set_trace()
    # norm_datas = normalize_stock('000078', dates)
    pool = ThreadPool(4)
    for stock_id in stocks:
        pool.add_task(normalize_stock, stock_id, dates)
    pool.run()
