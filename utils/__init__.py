#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import hashlib
import requests
import redis

from eventlet.greenpool import GreenPool
from minio import Minio
from minio.error import (ResponseError, BucketAlreadyOwnedByYou,
                         BucketAlreadyExists)
S3_API_PROTOCAL = os.getenv('S3_API_PROTOCAL', 'http')
S3_API_ENDPOINT = os.getenv('S3_API_ENDPOINT', '192.168.199.121:9000')
S3_SECRET_KEY = os.getenv('S3_SECRET_KEY', 'gYRY3qyw5w12a6oHNZLVhIzm1ARGjT2Zx6piMWQq')
S3_ACCESS_KEY = os.getenv('S3_ACCESS_KEY', 'US2TMDXZEEBVOZCKRVQ2')
REDIS_HOST = os.getenv('REDIS_HOST', '192.168.199.121')
REDIS_PORT = os.getenv('REDIS_PORT', 6379)
minio_client = Minio(S3_API_ENDPOINT, access_key=S3_ACCESS_KEY,
                    secret_key=S3_SECRET_KEY, secure=False)
redis_client = redis.Redis(REDIS_HOST, REDIS_PORT)


debug = False


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
            pass
        return


def make_bucket(bucket):
    try:
        minio_client.make_bucket(bucket,)
    except BucketAlreadyOwnedByYou as err:
        print('BucketAlreadyOwnedByYou')
    except BucketAlreadyExists as err:
        print('Bucket already exist')
    except ResponseError as err:
        raise


def put_file(bucket, filename, file_path):
    try:
        minio_client.fput_object(bucket, filename, file_path)
        print('Filename: {} (Bucket: {}) has been successfully uploaded\n'.format(filename, bucket))
    except ResponseError as err:
        print(err)


def get_file(bucket, filename, file_path):
    try:
        minio_client.fget_object(bucket, filename, file_path)
        print('Filename: {} (Bucket: {}) has been successfully downloaded\n'.format(filename, bucket))
    except ResponseError as err:
        print(err)
