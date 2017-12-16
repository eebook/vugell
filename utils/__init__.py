#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
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

S3_API_ENDPOINT = os.getenv('S3_API_ENDPOINT')
S3_API_PROTOCAL = os.getenv('S3_API_PROTOCAL')
S3_ACCESS_KEY = os.getenv('S3_ACCESS_KEY')
S3_SECRET_KEY = os.getenv('S3_SECRET_KEY')
REGION_NAME = os.getenv('S3_REGION_NAME')

REDIS_HOST = os.getenv('REDIS_HOST')
REDIS_PORT = os.getenv('REDIS_PORT')
redis_client = redis.Redis(REDIS_HOST, REDIS_PORT)
minio_client = Minio(S3_API_ENDPOINT, access_key=S3_ACCESS_KEY,
                     secret_key=S3_SECRET_KEY, secure=True)

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


def make_bucket(bucket):
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
