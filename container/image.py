#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import requests
import shutil
from utils import hex_md5, print_in_single_line


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

        print_in_single_line('Downloading picture: {}'.format(href))
        result = requests.get(href, stream=True)
        if result.status_code == 200:
            with open(self.save_path + '/' + filename, 'wb') as f:
                result.raw.decode_content = True
                shutil.copyfileobj(result.raw, f)
