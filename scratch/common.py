#!/usr/bin/env python
# -*- coding: utf-8 -*-

from six.moves import urllib
from bs4 import BeautifulSoup
import time
import traceback
import re
from multiprocessing import Pool as mPool
# from pathos.multiprocessing import ProcessingPool as mPool
from multiprocessing.dummy import Pool as mtPool
import pymongo
import signal
import argparse
import yaml
import configparser
import smtplib
from email.mime.text import MIMEText
import json
import pandas as pd

signal.signal(signal.SIGINT, signal.SIG_IGN)


def get_web(url, retry=3, timeout=7, encoding='GB2312'):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows; U; '
                      'Windows NT 6.1; en-US; rv:1.9.1.6) '
                      'Gecko/20091201 Firefox/3.5.6',
    }
    soup = None
    try_count = 0
    while 1:
        try:
            req = urllib.request.Request(url, headers=headers)
            rsp = urllib.request.urlopen(req, timeout=timeout)
            html = rsp.read()
            # soup = BeautifulSoup(html, "html.parser", from_encoding=encoding)
            soup = BeautifulSoup(html, "html.parser")
            rsp.close()
            break
        # except (urllib2.URLError, socket.timeout) as ex:
        except Exception as ex:
            traceback.print_exc()
            time.sleep(timeout)
            if try_count >= retry:
                break
            try_count += 1

    return soup


class Pool(object):
    def __init__(self, processes=1, debug=False, pool_func=mPool):
        if not debug:
            self._pool = pool_func(processes=processes)
        else:
            self._pool = None
        self.tasks = []
        self.results = []
        self.debug = debug

    def add_task(self, func, *args):
        if self.debug:
            task = (func, args)
        else:
            task = self._pool.apply_async(func, args=args)
        self.tasks.append(task)

    def run(self):
        if not self.debug:
            self._pool.close()
            try:
                self._pool.join()
            except KeyboardInterrupt:
                self._pool.terminate()
            self.results = [task.get() for task in self.tasks]
        else:
            for func, args in self.tasks:
                self.results.append(func(*args))
        return self.results

    def extend_results(self):
        ret = []
        for result in self.results:
            ret.extend(result)
        return ret


class ThreadPool(Pool):
    def __init__(self, processes=1, debug=False):
        super(ThreadPool, self).__init__(processes=processes, debug=debug, pool_func=mtPool)


class Store(object):
    def __init__(self, db_host, db_port, db_name, db_collection, rebuild=False):
        self.db_host = db_host
        self.db_port = db_port
        self.db_name = db_name
        self.db_collection = db_collection
        self.client = pymongo.MongoClient(db_host, db_port)
        self.db = self.client[db_name]
        if rebuild and db_collection in self.db.collection_names():
            self.db.drop_collection(db_collection)
        self.collection = self.db[db_collection]

    def put(self, value):
        val = value
        if isinstance(value, pd.DataFrame):
            val = value.to_dict()
        if val.get('_id'):
            obj_id = val.pop('_id')
            # obj_id = self.collection.update_one({'_id': obj_id}, {'$set': value})
            obj_id = self.collection.replace_one({'_id': obj_id}, val)
        else:
            obj_id = self.collection.insert_one(val).inserted_id
        return obj_id

    def get(self, filter=None, df=False):
        obj = list(self.collection.find(filter=filter))
        if df:
            return [pd.DataFrame.from_dict(i) for i in obj]
        else:
            return obj

    def put_df(self, df):
        ret = self.collection.insert_many(df.to_dict())
        return ret

    def get_df(self):
        obj = list(self.collection.find(filter=filter))

class Config(object):
    def __init__(self, file_path):
        self.file_path = file_path
        with open(file_path, 'r') as ff:
            self.file_content = ff.read()
        if file_path.endswith('ini'):
            self.type = 'ini'
            self.content = self._parse_ini(self.file_content)
        else:
            self.type = 'yaml'
            self.content = yaml.safe_load(self.file_content)

    def _parse_ini(self, content):
        config = configparser.ConfigParser()
        config.read_string(content)
        ret = {}
        for sk, sv in config.items():
            ret[sk] = dict(sv.items())
        return ret

    def __getitem__(self, key):
        return self.content.get(key)


class ArgParser(object):
    def __init__(self):
        self.parser = argparse.ArgumentParser()
        self.args = None

    def add(self, name, dest=None, nargs=None, action=None,
            default=None, choices=None):
        params = {
            'dest': dest,
            'action': action,
            'default': default,
        }
        if nargs:
            params['nargs'] = nargs
        if choices:
            params['choices'] = choices
        self.parser.add_argument(name, **params)

    def __getitem__(self, key):
        if self.args is None:
            self.args = self.parser.parse_args()
        return getattr(self.args, key)


class Mail(object):
    def __init__(self, server, user, password):
        self.server = server
        self.user = user
        self.password = password
        self.client = smtplib.SMTP()
        self.client.connect(self.server)
        self.client.login(self.user, self.password)

    def send(self, receivers, subject, message):
        if not isinstance(receivers, list):
            receivers = [receivers]
        msg = MIMEText(message, _subtype='plain', _charset='utf-8')
        me = '%s <%s>' % (self.user, self.user)
        msg['From'] = me
        msg['To'] = ';'.join(receivers)
        msg['Subject'] = subject
        self.client.sendmail(self.user, receivers, msg.as_string())
