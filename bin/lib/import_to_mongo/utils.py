# The MIT License (MIT)
#
# Copyright (c) 2013 James Tan <jamestyj@gmail.com>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import datetime
import locale
import sys
import threading

def log(msg):
    """Uses sys.stdout.write instead of print to be 'thread-safe'"""
    thread_name = threading.current_thread().name
    timestamp   = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    if thread_name == 'MainThread':
        sys.stdout.write('%s %s\n' % (timestamp, msg))
    else:
        sys.stdout.write('%s %s %s\n' % (timestamp, thread_name, msg))

def num_fmt(number):
    locale.setlocale(locale.LC_ALL, 'en_US')
    return locale.format('%d', number, grouping=True)

def sizeof(obj):
    return sizeof_fmt(len(obj))

def sizeof_fmt(num):
    for x in ['bytes', 'KB', 'MB', 'GB', 'TB']:
        if num < 1024.0:
            return "%3.1f %s" % (num, x)
        num /= 1024.0
