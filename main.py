#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import uuid
from ebooklib import epub
from elasticsearch import Elasticsearch
from minio import Minio
from minio.error import (ResponseError, BucketAlreadyOwnedByYou,
                         BucketAlreadyExists)

from style.style import STYLE
from plugins.picture import PicturePlugin

_index = os.getenv('ES_INDEX', 'rss')
_type = os.getenv('ES_TYPE', 'http://www.ruanyifeng.com/blog/atom.xml')
_id = os.getenv('ES_ID', '2017-09-20')
ESHOSTPORT = os.getenv('ESHOSTPORT', 'http://192.168.199.121:9200')
S3_API_PROTOCAL = os.getenv('S3_API_PROTOCAL', 'http')
S3_API_ENDPOINT = os.getenv('S3_API_ENDPOINT', '192.168.199.121:9000')
S3_SECRET_KEY = os.getenv('S3_SECRET_KEY', 'A4gkNz9x494EI+OUttx9UTta1ymkzHR0ZhBCZ1B1')
S3_ACCESS_KEY = os.getenv('S3_ACCESS_KEY', '60TC9MKTRD8A8U3U7686')

es = Elasticsearch([ESHOSTPORT])
minioClient = Minio(S3_API_ENDPOINT, access_key=S3_ACCESS_KEY, secret_key=S3_SECRET_KEY, secure=False)


def get_metadata():
    return es.get(index='eebook', doc_type='metadata', id='http://www.ruanyifeng.com/blog/atom.xml')


def main():
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
    try:
        minioClient.make_bucket("books", location="us-east-1")
    except BucketAlreadyOwnedByYou as err:
        pass
    except BucketAlreadyExists as err:
        pass
    except ResponseError as err:
        raise
    else:
        # Put an object 'pumaserver_debug.log' with contents from 'pumaserver_debug.log'.
        try:
            minioClient.fput_object('books', epub_name, file_path)
        except ResponseError as err:
            print(err)


# Will refactoring later

if __name__ == '__main__':
    main()

    from container import ImageContainer
    image_container = ImageContainer('/src/tmp')
    # image_container.add('http://test.jpg')
    image_container.add('http://www.ruanyifeng.com/blogimg/asset/2017/bg2017091801.jpg')
    image_container.add('http://www.ruanyifeng.com/blogimg/asset/2017/bg2017091804.png')

    print(image_container.get_filename_list())
    print('save_path???{}'.format(image_container.save_path))
    # image_container.download('http://www.ruanyifeng.com/blogimg/asset/2017/bg2017091801.jpg')
    # image_container.start_download()
