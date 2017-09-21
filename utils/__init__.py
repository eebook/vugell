#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import hashlib
import requests

from eventlet.greenpool import GreenPool

debug = False


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


class Control(object):
    thread_pool = GreenPool()

    @staticmethod
    def control_center(argv, test_flag):
        # max_try = Config.max_try
        max_try = 3
        for try_time in range(max_try):
            if test_flag:     # When we debug, we can choose not to downlod picture.
                if debug:
                    Control.debug_single(argv)
                else:
                    Control.multi_thread(argv)
        return

    @staticmethod
    def debug_single(argv):
        for item in argv['iterable']:
            argv['function'](item)
        return

    @staticmethod
    def multi_thread(argv):
        try:
            for _ in Control.thread_pool.imap(argv['function'], argv['iterable']):
                pass
        except Exception as e:
            print('Something happend...{}'.format(e))
            pass
        return
