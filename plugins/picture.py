#!/usr/bin/env python3
# -*- coding: utf-8 -*-


from ebooklib.plugins.base import BasePlugin
from container import ImageContainer


class PicturePlugin(BasePlugin):
    NAME = 'PicturePlugin'

    def html_before_write(self, book, chapter):
        from lxml import html, etree
        utf8_parser = html.HTMLParser(encoding='utf-8')

        image_container = ImageContainer('/src/tmp')
        # print('chapter.content???{}'.format(chapter.content))
        tree = html.document_fromstring(str(chapter.content), parser=utf8_parser)
        root = tree.getroottree()

        if len(root.find('body')) != 0:
            body = tree.find('body')

            for _pic_link in body.xpath("//img/@src"):
                if str(_pic_link).startswith('http'):
                    image_container.add(str(_pic_link))
                    # TODO: pic_link change to filename.jpg

        print('image list???{}'.format(image_container.get_filename_list()))
        image_container.start_download()

        chapter.content = etree.tostring(tree, pretty_print=True, encoding='utf-8')
