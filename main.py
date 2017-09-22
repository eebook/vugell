#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import uuid
from ebooklib import epub
from elasticsearch import Elasticsearch

from style.style import STYLE
from plugins.picture import PicturePlugin
from utils import make_bucket, put_file

_index = os.getenv('ES_INDEX', 'rss')
_type = os.getenv('ES_TYPE', 'http://www.ruanyifeng.com/blog/atom.xml')
_id = os.getenv('ES_ID', '2017-09-20')
ESHOSTPORT = os.getenv('ESHOSTPORT', 'http://192.168.199.121:9200')

es = Elasticsearch([ESHOSTPORT])


def get_metadata():
    return es.get(index='eebook', doc_type='metadata', id='http://www.ruanyifeng.com/blog/atom.xml')


def main():
    make_bucket('images')
    metadata = get_metadata()
    print('Building the book, got metadata: {}'.format(metadata))

    book = epub.EpubBook()

    # add metadata
    unique_id = uuid.uuid4()
    print('Book identifier id: {}'.format(str(unique_id)))
    book.set_identifier(str(unique_id))
    book.set_title(metadata['_source']['title'])
    book.set_language('zh')
    book.add_author('ee-book')

    # intro chapter
    c1 = epub.EpubHtml(title='Introduction', file_name='intro.xhtml', lang='zh')
    c1.content = metadata['_source']['title']

    # about chapter
    c2 = epub.EpubHtml(title='About this book', file_name='about.xhtml')
    c2.content = 'About this book'

    dsl_body = {
        "query": {
            "bool": {
                "must": [
                    {
                        "terms": {
                            "dayTimestamp": ["2017-09-20"]
                        }
                    }
                ]
            }
        }
    }

    content_result = es.search(index=_index, doc_type=_type+':content', body=dsl_body)
    content = content_result['hits']['hits']

    # add chapters to the book
    book.add_item(c1)
    book.add_item(c2)

    section = [c1, c2]
    book_spine = ['nav', c1, c2]

    for item in content:
        chapter = epub.EpubHtml(title=item['_source']['title'], file_name=item['_source']['title']+'.xhtml')
        chapter.content = item['_source']['content']
        print('Add chapter: {}'.format(item['_source']['title']))
        section.append(chapter)
        book_spine.append(chapter)
        book.add_item(chapter)

    # create table of contents
    book.toc = (epub.Link('intro.xhtml', 'Introduction', 'intro'),
                 (epub.Section('Articles'),
                  tuple(section)
                 )
                )
    # add navigation files
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    # define css style

    # add css file
    nav_css = epub.EpubItem(uid="style_nav", file_name="style/nav.css", media_type="text/css", content=STYLE)
    book.add_item(nav_css)

    # create spine
    book.spine = book_spine

    # epub options
    opts = {'plugins': [PicturePlugin()]}

    # create epub file
    epub_name = 'ee-bookorg-' + metadata['_source']['title'] + '.epub'
    file_path = '/src/' + epub_name
    epub.write_epub('/src/' + epub_name, book, opts)

    # Make a bucket with the make_bucket API call.
    make_bucket('books')
    # else:
        # Put an object 'pumaserver_debug.log' with contents from 'pumaserver_debug.log'.
    put_file('books', epub_name, file_path)


# Will refactoring later

if __name__ == '__main__':
    main()
