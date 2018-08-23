#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import shutil
from ebooklib import epub
from ebooklib.plugins.base import BasePlugin
from container import ImageContainer
from lxml import html, etree


class PicturePlugin(BasePlugin):
    NAME = 'PicturePlugin'

    def __init__(self):
        self.img_tmp_path = os.getenv("IMG_TMP_PATH", '/src/tmp/')
        self.error_pic = os.getenv("ERROR_PIC_PATH", '/src/assets/pic_error.png')

    def html_before_write(self, book, chapter):
        utf8_parser = html.HTMLParser(encoding='utf-8')

        image_container = ImageContainer(self.img_tmp_path)
        tree = html.document_fromstring(str(chapter.content), parser=utf8_parser)
        root = tree.getroottree()
        if len(root.find('body')) == 0:
            print('Ops, no body in this chapter, chapter content: {}'.format(chapter.content))
            return

        body = tree.find('body')

        for _pic_link in body.xpath("//img"):
            href = str(_pic_link.get('src'))
            if href.startswith('http'):
                image_container.add(href)
                _pic_link.set('src', '.'+self.img_tmp_path+image_container.container[href])

        image_container.start_download()
        filename_list = image_container.get_filename_list()
        for item in filename_list:
            try:
                f = open(self.img_tmp_path + item, 'rb')
            except FileNotFoundError as e:
                print('Handle pictures, Error: {}'.format(e))
                print('Copy pic_error to {}'.format(self.img_tmp_path + item))
                shutil.copyfile(self.error_pic, self.img_tmp_path + item)
                f = open(self.img_tmp_path + item, 'rb')
            finally:
                image = epub.EpubImage()
                image.file_name = self.img_tmp_path + item
                image.content = f.read()
                book.add_item(image)


        chapter.content = etree.tostring(tree, pretty_print=True, encoding='utf-8')
