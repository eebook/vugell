#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import requests
import shutil

from ebooklib import epub
from utils import hex_md5, print_in_single_line, Control, put_file, redis_client, get_file


class ImageContainer(object):
    """
    Picture href pool, and some tool functions
    """

    def __init__(self, save_path=''):
        self.save_path = save_path
        self.container = {}
        if not os.path.exists(self.save_path):
            os.mkdir(self.save_path)
        return

    def set_save_path(self, save_path):
        self.save_path = save_path
        return

    def add(self, href):
        filename = self.generate_filename(href)
        self.container[href] = filename
        return self.get_filename(href)

    def generate_filename(self, href):
        """
        md5 encoded filename
        """
        filename = hex_md5(href) + '.jpg'
        return filename

    def get_filename(self, href):
        image = self.container.get(href)
        if image:
            return image
        return ''

    def get_filename_list(self):
        return self.container.values()

    def download(self, href):
        filename = self.container[href]

        if os.path.isfile(self.save_path + '/' + filename):
            return

        # TODO: query redis, if exist, download from minio
        redis_cache = redis_client.get(href)
        file_path = self.save_path + '/' + filename
        if redis_cache:
            print('Got cache of {}, filename: {}'.format(href, filename))
            print('Download from minio...')
            get_file('images', filename, file_path)
        else:
            print('No cache! Downloading picture: {}'.format(href))

            try:
                result = requests.get(href, stream=True)
            except Exception as e:
                print('Unknown exception: {}'.format(e))
                return
            if result.status_code == 200:
                with open(file_path, 'wb') as f:
                    result.raw.decode_content = True
                    shutil.copyfileobj(result.raw, f)
                    put_file('images', filename, file_path)
                    redis_client.set(href, filename, ex=86400*15)
            else:
                print('Ops, Got error downloading {}'.format(href))

    def start_download(self):
        argv = {
            'function': self.download,
            'iterable': self.container,
        }
        Control.control_center(argv, self.container)
