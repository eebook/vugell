#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

def str2bool(v):
    return v and v.lower() in ("yes", "true", "t", "1")

ES_INDEX = os.getenv('ES_INDEX', 'rss')
ES_TYPE = os.getenv('URL', 'http://www.ruanyifeng.com/blog/atom.xml')
CREATED_BY = os.getenv('CREATED_BY', 'knarfeh')
EEBOOK_URL = os.getenv('URL', 'http://www.ruanyifeng.com/blog/atom.xml')
CONTENT_SIZE = int(os.getenv('CONTENT_SIZE', 30))

EPUB_NAME_FOR_DEBUG = os.getenv('EPUB_NAME_FOR_DEBUG', None)

S3_API_ENDPOINT = os.getenv('S3_API_ENDPOINT')
S3_API_PROTOCAL = os.getenv('S3_API_PROTOCAL')
S3_ACCESS_KEY = os.getenv('S3_ACCESS_KEY')
S3_SECRET_KEY = os.getenv('S3_SECRET_KEY')

EPUB_S3_ACCESS_KEY = os.getenv('EPUB_S3_ACCESS_KEY')
EPUB_S3_SECRET_KEY = os.getenv('EPUB_S3_SECRET_KEY')

REDIS_HOST = os.getenv('REDIS_HOST')
REDIS_PORT = os.getenv('REDIS_PORT')

IS_PUBLIC = str2bool(os.getenv('IS_PUBLIC', False))
CONTENT_IS_MARKDOWN = str2bool(os.getenv('CONTENT_IS_MARKDOWN'))
