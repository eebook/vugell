#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import re
import os
import json
import hashlib
import requests
from datetime import timedelta

import redis
import mistune
from eventlet.greenpool import GreenPool
from minio import Minio
from minio.error import (ResponseError, BucketAlreadyOwnedByYou,
                         BucketAlreadyExists)
from minio.policy import Policy
from elasticsearch import Elasticsearch
import configs

redis_client = redis.Redis(configs.REDIS_HOST, configs.REDIS_PORT)
minio_client = Minio(
    configs.S3_API_ENDPOINT,
    access_key=configs.S3_ACCESS_KEY,
    secret_key=configs.S3_SECRET_KEY,
    secure=False
)

ES_HOST_PORT = os.getenv('ES_HOST_PORT')
es = Elasticsearch([ES_HOST_PORT])
API_URL = os.getenv('GRYU_API_URL', 'http://192.168.199.121:18083')
API_VERSION = os.getenv("API_VERSION", "v1")
API_TOKEN = os.getenv('API_TOKEN')

debug = False
markdowner = mistune.Markdown()


def md2html(_content, _convert):
    if _convert is True:
        print('markdown to html')
        _content = markdowner(_content)
    return _content

def str2bool(v):
    return v and v.lower() in ("yes", "true", "t", "1")


def hex_md5(content):
    encrypt = hashlib.md5()
    encrypt.update(str(content).encode('utf-8'))
    return encrypt.hexdigest()


def print_in_single_line(text=''):
    try:
        sys.stdout.write('\r' + ' ' * 60 + '\r')
        sys.stdout.flush()
        sys.stdout.write(text)
        sys.stdout.flush()
    except:
        pass
    return


class Control(object):
    thread_pool = GreenPool()

    @staticmethod
    def control_center(argv, test_flag):
        # max_try = Config.max_try
        max_try = 3
        for try_time in range(max_try):
            if test_flag:     # When we debug, we can choose not to downlod picture.
                if debug:
                    Control.debug_single(argv)
                else:
                    Control.multi_thread(argv)
        return

    @staticmethod
    def debug_single(argv):
        for item in argv['iterable']:
            argv['function'](item)
        return

    @staticmethod
    def multi_thread(argv):
        try:
            for _ in Control.thread_pool.imap(argv['function'], argv['iterable']):
                pass
        except Exception as e:
            print('Something happend...{}'.format(e))
        return


def minio_make_bucket(bucket):
    try:
        minio_client.make_bucket(bucket,)
    except BucketAlreadyOwnedByYou as err:
        print('BucketAlreadyOwnedByYou')
    except BucketAlreadyExists as err:
        print('Bucket: {} already exist'.format(bucket))
    except ResponseError as err:
        raise


def put_file(bucket, filename, file_path):
    try:
        minio_client.fput_object(bucket, filename, file_path, metadata={"x-amz-acl": "public-read"})
        print('Filename: {} (Bucket: {}) has been successfully uploaded\n'.format(filename, bucket))
    except ResponseError as err:
        print(err)


def get_file(bucket, filename, file_path):
    try:
        minio_client.fget_object(bucket, filename, file_path)
        print('Filename: {} (Bucket: {}) has been successfully downloaded\n'.format(filename, bucket))
    except ResponseError as err:
        print(err)


def presigned_get_object(bucket, filename, expire_days, content_string):
    try:
        return minio_client.presigned_get_object(bucket,
                                                 filename,
                                                 expires=timedelta(days=expire_days),
                                                 response_headers={
                                                     'Content-Disposition': content_string,
                                                     'response-content-type': 'application/octet- stream'
                                                 })
    except ResponseError as err:
        print(err)


def get_metadata(_id):
    return es.get(index='eebook', doc_type='metadata', id=_id)


def create_book_resource(_name, _id, _is_public=False):
    url = "{}/{}/books/".format(API_URL, API_VERSION)
    payload = {
        "book_name": _name,
        "uuid": _id,
        "is_public": _is_public
    }
    headers = {
        "Authorization": "Token " + API_TOKEN,
        "content-type": "application/json"
    }
    r = requests.post(url, headers=headers, data=json.dumps(payload))
    return r


def put_book_info_2_es(book_id, body):
    es.create(index='eebook', doc_type='book', id=book_id, body=body)


def invalid_xml_remove(c):
    """
    https://gist.github.com/lawlesst/4110923
    http://stackoverflow.com/questions/1707890/fast-way-to-filter-illegal-xml-unicode-chars-in-python
    """
    illegal_unichrs = [ (0x00, 0x08), (0x0B, 0x1F), (0x7F, 0x84), (0x86, 0x9F),
                    (0xD800, 0xDFFF), (0xFDD0, 0xFDDF), (0xFFFE, 0xFFFF),
                    (0x1FFFE, 0x1FFFF), (0x2FFFE, 0x2FFFF), (0x3FFFE, 0x3FFFF),
                    (0x4FFFE, 0x4FFFF), (0x5FFFE, 0x5FFFF), (0x6FFFE, 0x6FFFF),
                    (0x7FFFE, 0x7FFFF), (0x8FFFE, 0x8FFFF), (0x9FFFE, 0x9FFFF),
                    (0xAFFFE, 0xAFFFF), (0xBFFFE, 0xBFFFF), (0xCFFFE, 0xCFFFF),
                    (0xDFFFE, 0xDFFFF), (0xEFFFE, 0xEFFFF), (0xFFFFE, 0xFFFFF),
                    (0x10FFFE, 0x10FFFF) ]

    illegal_ranges = ["%s-%s" % (chr(low), chr(high))
                  for (low, high) in illegal_unichrs
                  if low < sys.maxunicode]

    illegal_xml_re = re.compile(u'[%s]' % u''.join(illegal_ranges))
    if illegal_xml_re.search(c) is not None:
        # Replace with space
        return ' '
    else:
        return c
