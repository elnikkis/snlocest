# coding: utf-8

'''
Gzipが読み込める
'''

import argparse
import gzip

from gettext import gettext as _


# argparse.FileTypeはnewlineに対応していないことに気付いた

class GzipFileType(argparse.FileType):
    '''argparse.FileTypeのgzipが読み込めるバージョン'''

    def __init__(self, mode='r', bufsize=-1, encoding=None, errors=None, compresslevel=9):
        super().__init__(mode=mode, bufsize=bufsize, encoding=encoding)
        self._compresslevel = compresslevel

    def __call__(self, string):
        if string.endswith('.gz'):
            if 't' in self._mode:
                args = (self._mode, self._compresslevel, self._encoding, self._errors)
            else:
                args = (self._mode, self._compresslevel)
            try:
                return gzip.open(string, *args)
            except OSError as e:
                message = _("can't open '%s': %s")
                raise ArgumentTypeError(message % (string, e))
        return super().__call__(string)
