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

import time
from utils import log, sizeof, sizeof_fmt

class DownloadWorker:

    """DownloadWorker thread class.

    Downloads the specified file from Amazon S3 without blocking data imports
    into MongoDB. Depending on your network connection, increasing the number
    of download threads may reduce overall import time.
    """

    def __init__(self, opts, s3_key):
        self.opts   = opts
        self.s3_key = s3_key

        key_tokens         = s3_key.key.split('/')
        self.file_name     = key_tokens[-1]
        self.data_set_name = key_tokens[-2]

    def get_file(self):
        if self.opts.verbose:
            log('%s: Downloading...' % self.file_name)

        start    = time.time()
        contents = self.s3_key.get_contents_as_string()
        elapsed  = time.time() - start
        speed    = len(contents) / elapsed
        log('%s: Downloaded %s in %.1fs (%s/s)' % (self.file_name,
                sizeof(contents), elapsed, sizeof_fmt(speed)))
        return self.file_name, self.data_set_name, contents
