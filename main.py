#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import uuid
import boto3
import sys
from ebooklib import epub

from style.style import STYLE
from plugins.picture import PicturePlugin
from utils import (minio_make_bucket, put_file, get_metadata, es, put_book_info_2_es,
                   presigned_get_object, create_book_resource, str2bool, md2html,
                   invalid_xml_remove)
import configs

def make_book_with_metadata(_metadata, _book_uuid):
    print('Building the book, got metadata: {}'.format(_metadata))

    book = epub.EpubBook()
    # add metadata
    print('Book identifier id: {}'.format(str(_book_uuid)))
    book.set_identifier(str(_book_uuid))
    book.set_title(_metadata['_source']['title'])
    book.set_language('zh')
    book.add_author('ee-book')

    # intro chapter
    c1 = epub.EpubHtml(title='Introduction', file_name='intro.xhtml', lang='zh')
    c1.content = _metadata['_source']['title']

    # about chapter, TODO, get from _INDEX/_TYPE/
    c2 = epub.EpubHtml(title='About this book', file_name='about.xhtml')
    c2.content = 'About this book'
    query = {
        'bool': {
            'must':[
                {
                    "terms": {
                        "dayTimestamp": [configs.DAY_TIME_STAMP]
                    }
                }
            ]
        }
    }
    query = _metadata['_source'].get('query') or query
    dsl_body = {
        "query": query
    }

    # TODO: Separate by volumes
    content_result = es.search(index=configs.ES_INDEX, doc_type=configs.ES_TYPE+':content', body=dsl_body, size=configs.CONTENT_SIZE, from_=0)
    content = content_result['hits']['hits']

    # add chapters to the book
    book.add_item(c1)
    book.add_item(c2)

    section = [c1, c2]
    book_spine = ['nav', c1, c2]

    for item in content:
        title = invalid_xml_remove(item['_source'].get('title') or 'No Title')
        if title is None or title == "":
            title = "No Title"
        print('Add chapter: {}'.format(title))
        chapter = epub.EpubHtml(title=title, file_name=title + '.xhtml')
        title_html = '<h1>' + title + '</h1>'
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
        chapter.content = md2html(chapter.content, configs.CONTENT_IS_MARKDOWN)
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
    opts = {}
    if str2bool(os.getenv("REPLACE_PICTURE", "true")):        
        opts = {'plugins': [PicturePlugin()]}

    # create epub file
    epub_name = 'ee-bookorg-' + _metadata['_source']['title'] + '-' + configs.CREATED_BY + '.epub' if configs.EPUB_NAME_FOR_DEBUG is None else configs.EPUB_NAME_FOR_DEBUG
    epub.write_epub('./' + epub_name, book, opts)
    return epub_name

def main():
    if configs.DEBUG_MODE is not True:
        minio_make_bucket('webeebook')
    else:
        print("DEBUG mode")
    metadata = get_metadata(_id=configs.EEBOOK_URL)
    book_uuid = uuid.uuid4()
    epub_name = make_book_with_metadata(metadata, book_uuid)
    file_path = '/src/' + epub_name

    if configs.DEBUG_MODE is not True:
        # TODO: size restriction
        s3 = boto3.client(
            's3',
            aws_access_key_id=configs.EPUB_S3_ACCESS_KEY,
            aws_secret_access_key=configs.EPUB_S3_SECRET_KEY
        )
        s3.upload_file(file_path, 'webeebook', 'books/'+epub_name)
        content_string = 'attachment; filename="' + epub_name + '"'
        download_url = presigned_get_object(bucket='webeebook',
                                            filename='books/'+epub_name,
                                            expire_days=1,
                                            content_string=content_string)
    else:
        download_url = 'DEBUG_MODE'

    # TODO, send book metadata to es, include book_name, created_by, book_basic_info,
    # TODO: update book href in each es doc, so we can search with book content
    # Just copy github, project->book, code->book content
    book_info_body = {
        'id': book_uuid,
        'title': epub_name,
        'type': 'eebook',
        'tags': [
            {
                'name': configs.ES_INDEX,
                'title': configs.ES_INDEX,
                'count': 1,
            },
            {
                'name': 'yawnwoem',
                'title': 'yawnwoem',
                'count': 1,
            },
        ],
        'created_by': configs.CREATED_BY,
        'created_time': 'create_time',  # TODO
        'updated_time': 'updated_time',
        'url': configs.EEBOOK_URL,
        'download_url': download_url
    }
    if configs.DEBUG_MODE is not True:
        response = create_book_resource(epub_name, str(book_uuid), configs.IS_PUBLIC)
        if response.status_code != 201:
            print("Got error...")
            print("status code: {}, response: {}".format(response.status_code, response.text))
            return

    put_book_info_2_es(book_id=book_uuid, body=book_info_body)
    print('Successfully send book information to ee-book, book_id: {}, name: {}'.format(
        book_uuid, epub_name))


if __name__ == '__main__':
    main()
