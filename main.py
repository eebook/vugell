#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import uuid
import boto3
from ebooklib import epub

from style.style import STYLE
from plugins.picture import PicturePlugin
from utils import (make_bucket, put_file, get_metadata, es, put_book_info_2_es,
                   presigned_get_object, create_book_resource, str2bool, md2html)
import configs


def main():
    if configs.DEBUG_MODE is not True:
        make_bucket('webeebook')
    metadata = get_metadata(_id=configs.EEBOOK_URL)
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

    # TODO: Separate by volumes
    content_result = es.search(index=configs.ES_INDEX, doc_type=configs.ES_TYPE+':content', body=dsl_body, size=configs.CONTENT_SIZE, from_=0)
    content = content_result['hits']['hits']

    # add chapters to the book
    book.add_item(c1)
    book.add_item(c2)

    section = [c1, c2]
    book_spine = ['nav', c1, c2]

    for item in content:
        # TODO, remove invalid symbol in title
        title = item['_source'].get('title').replace('\b', '') or 'No title'
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
    opts = {'plugins': [PicturePlugin()]}

    # create epub file
    epub_name = 'ee-bookorg-' + metadata['_source']['title'] + '-' + configs.CREATED_BY + '.epub' if configs.EPUB_NAME_FOR_DEBUG is None else configs.EPUB_NAME_FOR_DEBUG
    file_path = '/src/' + epub_name
    epub.write_epub('/src/' + epub_name, book, opts)

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
