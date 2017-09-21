#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import hashlib
import requests


def hex_md5(content):
    encrypt = hashlib.md5()
    encrypt.update(str(content).encode('utf-8'))
    return encrypt.hexdigest()


def print_in_single_line(text=''):
    try:
        sys.stdout.write('\r' + ' ' * 60 + '\r')
        sys.stdout.flush()
        sys.stdout.write(text)
        sys.stdout.flush()
    except:
        pass
    return
