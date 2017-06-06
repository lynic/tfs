#!/usr/bin/env python
# -*- coding: utf-8 -*-

import six
from six.moves import urllib
# import urllib2
from bs4 import BeautifulSoup
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


debug=False
cheaper_books = []
# config = Config('/etc/config.yaml')

def get_book(book_id):
    print("Getting info of %s" % book_id)
    url = "http://www.duokan.com/book/%s" % book_id
    soup = get_web(url)
    if not soup:
        return {}
    contents = soup.find('div', {'class': 'desc'})
    title = contents.find('h3').get_text()
    _rate = contents.find('em', {'class': 'score'})
    if not _rate:
        rate = float(0)
    else:
        rate = float(_rate.get_text())
    try:
        _author = contents.find_all("td", {'class': 'author'})[0].find('a')
        if _author is None:
            _author = contents.find_all("td", {'class': 'author'})[0].find('span')
        author = _author.get_text()
        _author_id = _author.attrs.get('href')
        author_id = _author_id.split('/')[2] if _author_id else ''
    except IndexError:
        author = ''
        author_id = ''
    _publisher = contents.find('td', {"class", "published" }).find('a')
    publisher = _publisher.get_text()
    publisher_id = _publisher.attrs['href'].split('/')[2]
    _price = contents.find('div', {'class': 'price'})
    _current_price = _price.find("em").get_text()
    if _current_price == six.text_type(u"免费"):
        current_price = float(0)
        origin_price = float(0)
    else:
        current_price = float(_current_price.split(' ')[1])
    _origin_price = _price.find("del")
    if not _origin_price:
        origin_price = float(0)
    else:
        origin_price = float(_origin_price.get_text().split(' ')[1])
    ret = {
        'title': six.text_type(title),
        'book_id': book_id,
        'rate': rate,
        'author': six.text_type(author),
        'author_id': author_id,
        'publisher': six.text_type(publisher),
        'publisher_id': publisher_id,
        'current_price': current_price,
        'origin_price': origin_price,
        'lowest_price': current_price,
    }
    return ret

def get_books_by_publisher_page(publisher_id, page):
    print("Getting books from publisher %s page %s" % (publisher_id, page))
    url = "http://www.duokan.com/publisher/%s-%s" % (publisher_id, page)
    soup = get_web(url)
    current_books = soup.find_all('div', {"class": "book"})
    books = [i.find('a').attrs['href'].split('/')[2] for i in current_books]
    pool = ThreadPool(processes=7, debug=debug)
    tasks = []
    for book_id in books:
        pool.add_task(get_book, book_id)
    ret = pool.run()
    store_book(ret)
    return ret

def get_books_by_publisher(publisher_id):
    ret = []
    print("Getting books from publisher %s" % publisher_id)
    url = "http://www.duokan.com/publisher/%s" % publisher_id
    soup = get_web(url)
    _pages = soup.find('div', {"class": "u-page-go"})
    if not _pages:
        total_page = 1
    else:
        _pages = _pages.find_all('span')[2].get_text()
        total_page = int(re.search(r'\d+', _pages).group())
    pool = Pool(processes=4, debug=debug)
    tasks = []
    for page in range(1, total_page+1):
        pool.add_task(get_books_by_publisher_page, publisher_id, page)
    pool.run()
    books_info = pool.extend_results()
    return books_info

def store_book(books_info):
    def _db_put(put_func, value):
        print('Storing book %s' % value['book_id'])
        put_func(value)
    config = Config('/etc/config.yaml')
    db = Store(config['mongodb']['server'], config['mongodb']['port'],
               'duokan', 'books')
    for book in books_info:
        # pool.apply_async(db.put, args=(book,))
        if not book:
            continue
        need_store = True
        stored_book = db.get({'book_id': book['book_id']})
        if stored_book:
            stored_book = stored_book[0]
            if book['lowest_price'] < stored_book['lowest_price']:
                print('book "%s" has new lowest_price %s' % (
                    book['title'], book['lowest_price']))
                db3 = Store(
                    config['mongodb']['server'],
                    config['mongodb']['port'],
                    'tmp',
                    'cheaper_books')
                db3.put(book)
            else:
                need_store = False
            book['_id'] = stored_book['_id']
        if need_store:
            print('Storing book %s' % book['book_id'])
            db.put(book)

def get_publisher_list():
    publishers = []
    url = 'http://www.duokan.com/publishers'
    soup = get_web(url)
    contents = soup.find_all('div', {'class': 'list'})[1].find_all('li')
    # Ignore the last one cause it's corparation link
    for item in contents[:-1]:
        publisher_id = item.find('a').attrs['href'].split('/')[2]
        # print(publisher_id)
        publisher_name = item.find('img').attrs['alt']
        # print(publisher_name)
        publishers.append({
            'publisher_id': publisher_id,
            'publisher': publisher_name 
        })
    return publishers


if __name__ == '__main__':
    # Rebuild tmp storage
    publishers = []
    books = []
    config = Config('/etc/config.yaml')
    db2 = Store(config['mongodb']['server'], config['mongodb']['port'],
                'tmp', 'cheaper_books', rebuild=True)
    parser = ArgParser()
    parser.add('--publisher')
    parser.add('--all', action='store_true')
    parser.add('--favorite', action='store_true')
    parser.add('--book')
    if parser['all']:
        publishers = get_publisher_list()
    elif parser['favorite']:
        publishers = config['duokan']['favorite']
    elif parser['publisher']:
        publishers = [parser['publisher']]
    elif parser['book']:
        books = [parser['book']]
    for publisher in publishers:
        get_books_by_publisher(publisher)
    for book in books:
        get_book(book)
    cheaper_books = db2.get()
    if cheaper_books:
        mail = Mail(config['mail']['server'], config['mail']['user'],
                    config['mail']['password'])
        subject = 'Duokan %s' % datetime.now()
        mail.send(config['mail']['receiver'], subject, cheaper_books)
