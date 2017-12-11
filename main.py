#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import uuid
from ebooklib import epub

from style.style import STYLE
from plugins.picture import PicturePlugin
from utils import (make_bucket, put_file, get_metadata, es, put_book_info_2_es,
                   presigned_get_object, create_book_resource, str2bool, md2html)

_INDEX = os.getenv('ES_INDEX', 'rss')
_TYPE = os.getenv('URL', 'http://www.ruanyifeng.com/blog/atom.xml')
_ID = os.getenv('ES_ID', '2017-09-24')
CREATED_BY = os.getenv('CREATED_BY', 'knarfeh')
EEBOOK_URL = os.getenv('URL', 'http://www.ruanyifeng.com/blog/atom.xml')
IS_PUBLIC = str2bool(os.getenv('IS_PUBLIC'))
CONTENT_IS_MARKDOWN = str2bool(os.getenv('CONTENT_IS_MARKDOWN'))
CONTENT_SIZE = int(os.getenv('CONTENT_SIZE', 30))

EPUB_NAME_FOR_DEBUG = os.getenv('EPUB_NAME_FOR_DEBUG', None)


def main():
    make_bucket('images')
    metadata = get_metadata(_id=EEBOOK_URL)
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

    # about chapter, TODO, get from _INDEX/_TYPE/
    c2 = epub.EpubHtml(title='About this book', file_name='about.xhtml')
    c2.content = 'About this book'

    dsl_body = {
        "query": metadata['_source']['query']
    }
    # TODO: pretty print
    print("dsl_body???{}".format(dsl_body))

    # TODO: Separate by volumes
    content_result = es.search(index=_INDEX, doc_type=_TYPE+':content', body=dsl_body, size=CONTENT_SIZE, from_=0)
    content = content_result['hits']['hits']

    # add chapters to the book
    book.add_item(c1)
    book.add_item(c2)

    section = [c1, c2]
    book_spine = ['nav', c1, c2]

    for item in content:
        chapter = epub.EpubHtml(title=item['_source']['title'], file_name=item['_source']['title']+'.xhtml')
        title_html = '<h1>' + item['_source']['title'] + '</h1>'
        author_html = '<p>Author: ' + item['_source']['author'] + '</p>'
        if isinstance(item['_source']['content'], list):
            content = ''
            for sub_item in item['_source']['content']:
                sub_author = '<hr><p>Author: ' + sub_item['author'] + '</p>'
                sub_content = sub_item['content']
                content += (sub_author+str(sub_content))
            chapter.content = title_html + content
        else:
            chapter.content =  title_html + author_html + item['_source']['content']
        chapter.content = md2html(chapter.content, CONTENT_IS_MARKDOWN)
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
    epub_name = 'ee-bookorg-' + metadata['_source']['title'] + '-' + CREATED_BY + '.epub' if EPUB_NAME_FOR_DEBUG is None else EPUB_NAME_FOR_DEBUG
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
        'id': book_uuid,
        'title': epub_name,
        'type': 'eebook',
        'tags': [
            {
                'name': _INDEX,
                'title': _INDEX,
                'count': 1,
            },
            {
                'name': 'yawnwoem',
                'title': 'yawnwoem',
                'count': 1,
            },
        ],
        'created_by': CREATED_BY,
        'created_time': 'create_time',  # TODO
        'updated_time': 'updated_time',
        'url': EEBOOK_URL,
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


if __name__ == '__main__':
    main()
