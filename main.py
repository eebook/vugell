#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import uuid
from ebooklib import epub

from style.style import STYLE
from plugins.picture import PicturePlugin
from utils import (make_bucket, put_file, get_metadata, es,
                   put_book_info_2_es, presigned_get_object, create_book_resource)

_index = os.getenv('ES_INDEX', 'rss')
_type = os.getenv('ES_TYPE', 'http://www.ruanyifeng.com/blog/atom.xml')
_id = os.getenv('ES_ID', '2017-09-24')
created_by = os.getenv('CREATED_BY', 'knarfeh')
IS_PUBLIC = os.getenv('IS_PUBLIC')
eebook_url = os.getenv('EEBOOK_URL', 'http://www.ruanyifeng.com/blog/atom.xml')


def main():
    make_bucket('images')
    metadata = get_metadata(_id=eebook_url)
    print('Building the book, got metadata: {}'.format(metadata))

    book = epub.EpubBook()

    # add metadata
    book_uuid = uuid.uuid4()
    print('Book identifier id: {}'.format(str(book_uuid)))
    book.set_identifier(str(book_uuid))
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
        "query": metadata['_source']['query']
    }
    print("dsl_body???{}".format(dsl_body))

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
    epub_name = 'ee-bookorg-' + metadata['_source']['title'] + '-' + created_by + '.epub'
    file_path = '/src/' + epub_name
    epub.write_epub('/src/' + epub_name, book, opts)

    # Make a bucket with the make_bucket API call.
    make_bucket('books')
    # else:
        # Put an object 'pumaserver_debug.log' with contents from 'pumaserver_debug.log'.
    put_file('books', epub_name, file_path)
    content_string = 'attachment; filename="' + epub_name + '"'
    download_url = presigned_get_object(bucket='books',
                                        filename=epub_name,
                                        expire_days=1,
                                        content_string=content_string)

    # TODO, send book metadata to es, include book_name, created_by, book_basic_info,
    # TODO: update book href in each es doc, so we can search with book content
    # Just copy github, project->book, code->book content
    book_info_body = {
        'uuid': book_uuid,
        'name': epub_name,
        # 'name': 'ee-bookorg-阮一峰的网络日志-rss-2017-10-04.epub',
        'type': _index,
        'tags': [_index, 'ruanyifeng'],
        'created_by': created_by,
        'created_time': 'create_time',
        'updated_time': 'updated_time',
        'eebook_url': eebook_url,
        'download_url': download_url
    }
    response = create_book_resource(epub_name, str(book_uuid), IS_PUBLIC)
    if response.status_code != 201:
        print("Got error...")
        print("status code: {}, response: {}".format(response.status_code, response.text))
        return
    put_book_info_2_es(book_id=book_uuid, body=book_info_body)
    print('Successfully send book information to ee-book, book_id: {}, name: {}'.format(
        book_uuid, epub_name))


# Will refactoring later

if __name__ == '__main__':
    main()
