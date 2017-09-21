#!/usr/bin/env python3
# -*- coding: utf-8 -*-


from ebooklib.plugins.base import BasePlugin


class PicturePlugin(BasePlugin):
    NAME = 'PicturePlugin'

    def html_before_write(self, book, chapter):
        from lxml import html, etree

        utf8_parser = html.HTMLParser(encoding='utf-8')
        # print('chapter.content???{}'.format(chapter.content))
        tree = html.document_fromstring(str(chapter.content), parser=utf8_parser)
        root = tree.getroottree()

        if len(root.find('body')) != 0:
            body = tree.find('body')

            for _pic_link in body.xpath("//img/@src"):
                if str(_pic_link).startswith('http'):
                    print('pic link???{}'.format(_pic_link))

        chapter.content = etree.tostring(tree, pretty_print=True, encoding='utf-8')
