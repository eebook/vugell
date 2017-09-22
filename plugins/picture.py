#!/usr/bin/env python3
# -*- coding: utf-8 -*-


from ebooklib import epub
from ebooklib.plugins.base import BasePlugin
from container import ImageContainer
from lxml import html, etree


class PicturePlugin(BasePlugin):
    NAME = 'PicturePlugin'

    def html_before_write(self, book, chapter):
        utf8_parser = html.HTMLParser(encoding='utf-8')

        image_container = ImageContainer('/src/tmp')
        tree = html.document_fromstring(str(chapter.content), parser=utf8_parser)
        root = tree.getroottree()

        if len(root.find('body')) != 0:
            body = tree.find('body')

            for _pic_link in body.xpath("//img"):
                href = str(_pic_link.get('src'))
                if href.startswith('http'):
                    image_container.add(href)
                    _pic_link.set('src', './src/tmp/'+image_container.container[href])

        image_container.start_download()
        filename_list = image_container.get_filename_list()
        for item in filename_list:
            with open('/src/tmp/' + item, 'rb') as f:
                image = epub.EpubImage()
                image.file_name = '/src/tmp/' + item
                image.content = f.read()
                book.add_item(image)

        chapter.content = etree.tostring(tree, pretty_print=True, encoding='utf-8')
