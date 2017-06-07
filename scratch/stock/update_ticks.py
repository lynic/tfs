
import tushare as ts
import arctic
import six
import traceback
import time

from common import Config
from common import ArgParser
from common import ThreadPool
from common import Store


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

def get_dates(stock_id):
    config = Config('/etc/config.yaml')
    store = arctic.Arctic(config['mongodb']['server'], config['mongodb']['port'])
    library = store.get_library('Stocks_Daily.none')
    try:
        datas = library.read(stock_id).data
    except Exception as ex:
        traceback.print_exc()
        return None
    if datas.empty:
        return None
    return datas.index.tolist()

def update_ticks(stock_id, src='tt'):
    config = Config('/etc/config.yaml')
    # tick_store = Store(
    #     config['mongodb']['server'], config['mongodb']['port'],
    #     'stock-ticks', stock_id)
    store = arctic.Arctic(config['mongodb']['server'], config['mongodb']['port'])
    dates = get_dates(stock_id)
    if not dates:
        return
    lib_name = 'Stocks_Ticks_%s.%s' % (src, stock_id)
    library = get_library(lib_name)
    stored_dates = library.list_symbols()
    for date in dates:
        if date in stored_dates:
            continue
        # No need to fetch data before 2004
        if int(date.split('-')[0]) < 2004:
            continue
        print('Trying to get %s %s' % (stock_id, date))
        # import ipdb;ipdb.set_trace()
        try:
            print("sleep")
            time.sleep(3)
            data = ts.get_tick_data(stock_id, date=date, src=src)
        except Exception as ex:
            traceback.print_exc()
            continue
        if data is None or len(data) == 3:
            # No ticks today
            continue
        print('Storing %s %s' % (stock_id, date))
        library.write(date, data)

if __name__ == '__main__':
    parser = ArgParser()
    parser.add('--all', action='store_true')
    parser.add('--stock')
    parser.add('--debug', action='store_true', default=False)
    parser.add('--src', choices=['tt', 'nt', 'sn'], default='tt')
    # import ipdb;ipdb.set_trace()
    pool = ThreadPool(4, debug=parser['debug'])
    if parser['stock']:
        update_ticks(parser['stock'], src=parser['src'])
    elif parser['all']:
        stock_ids = ts.get_stock_basics().index.tolist()
        for stock_id in stock_ids:
            pool.add_task(update_ticks, stock_id, parser['src'])
            # update_ticks(stock_id)
    pool.run()
