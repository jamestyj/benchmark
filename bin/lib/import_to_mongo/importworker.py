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

import pylru
import time
import zlib
from mongobatcher import MongoBatcher
from utils import log, num_fmt, sizeof, sizeof_fmt

class ImportWorker:

    """Import thread class.

    Imports the given deflated text blob into MongoDB. Depending on your system
    setup, increasing the number of threads from the defautl of 1 may reduce
    overall import time.

    The import algorithm is roughly like this:

    1. Inflate/decompress given deflated text blob with zlib. This is usually
       very fast (less than a second).

    2. Look at the data set name and diverge into one of the following two code
       paths:

       a. Generic CSV import - For the rankings and uservisits data sets, only
          difference being their schema. The rankings collection (table in SQL
          terms) has the following schema:

            { _id: 'pageURL',  pageRank: 123, avgDuration: 123 }

          This is identical to the SQL table schema, except that we store
          the pageURL in _id. MongoDB requires the _id field to be present and
          unique in every collection, hence by doing so we save a bit of space
          and get free uniqueness constraint to avoid duplicates (there
          shouldn't be any here).

          The uservisits collection has the following schema:

            { _id:        'ID',   sourceIP:     '111.111.111',
              destURL:    'xxx',  visitDate:    '2010-01-30',
              adRevenue:   123,   userAgent:    'xxx',
              countryCode: 123,   languageCode: 'XX',
              searchWord:  'xxx', duration:      123,
              pageRank:    xxx }

          This is the same as the SQL table schema but with the pageRank field
          added. This is needed for Query 3 as MongoDB does not support joins,
          so we'll either need to do that in the application or pre-join it
          like this.

       b. Crawl data set import - This contains unstructured HTML which we
          cannot directly store in MongoDB due to the 16MB limit for a single
          document. Hence we parse the HTML blob and split it into the
          following schema:

            { url : 'URL', html: 'HTML...' }

          Note that the crawl data set is imported in to the 'documents'
          collection, for consistency with the table names used in the
          benchmark.

    Performance tweaks:

    - Batching inserts. When doing bulk inserts like this import process, it's
      significantly faster to batch them rather than hitting the database
      individually for each insert (e.g. it reduces the network and other
      overheads). This is implemented by the MongoBatcher class
      (mongobatcher.py).

    - Caching pageRank lookups. We need to lookup the pageRank from the
      rankings collection when importing the uservisits data set (pre-joining).
      Caching this helps to improve throughput.
    """

    def __init__(self, db, opts, file_name, data_set_name, deflated_text):
        self.db            = db
        self.opts          = opts
        self.file_name     = file_name
        self.data_set_name = data_set_name

        if data_set_name == 'crawl':
            self.collection_name = 'documents'
        else:
            self.collection_name = data_set_name

        self.batcher = MongoBatcher(db, self.collection_name, opts.batch_size)
        self.cache   = pylru.lrucache(10000)

        self.crawl_url  = ''
        self.crawl_html = []

        self._import(deflated_text)

    def _inflate(self, deflated_text):
        start   = time.time()
        text    = zlib.decompress(deflated_text)
        elapsed = time.time() - start
        if self.opts.verbose:
            log('%s: Inflated from %s to %s in %fs' % (self.file_name,
                    sizeof(deflated_text), sizeof(text), elapsed))
        return text

    def _import(self, deflated_text):
        text  = self._inflate(deflated_text)
        log('%s: Importing...' % self.file_name)
        start = time.time()
        if self.data_set_name == 'crawl':
            count = self._import_crawl(text)
        else:
            count = self._import_csv(text)
        self.batcher.flush()
        elapsed = time.time() - start
        speed   = count / elapsed
        log('%s: Imported %s docs (%s per sec)' % (self.file_name,
                num_fmt(count), num_fmt(speed)))

    def _import_csv(self, text):
        count = 0
        for line in text.splitlines():
            count += 1
            c = line.split(',')
            if self.data_set_name == 'rankings':
                # We store 'pageURL' as '_id' to automatically ensure uniqueness
                # and avoid unnecessary disk space usage
                self.batcher.insert({
                        '_id'        : c[0],     'pageRank': int(c[1]),
                        'avgDuration': int(c[2]) })
            elif self.data_set_name == 'uservisits':
                self.batcher.insert({
                        'sourceIP'    : c[0],      'destURL'    : c[1],
                        'visitDate'   : c[2],      'adRevenue'  : float(c[3]),
                        'userAgent'   : c[4],      'countryCode': c[5],
                        'languageCode': c[6],      'searchWord' : c[7],
                        'duration'    : int(c[8]), 'pageRank'   : self._page_rank(c[1]) })
            else:
                raise Exception("Unknown data set: %s" % self.data_set_name)
        return count

    def _import_crawl(self, text):
        count = 0
        for line in text.splitlines():
            if (line[0:4] == "http" and len(line.split(" ")) == 5):
                if self.crawl_url != '':
                    count += 1
                    self.batcher.insert({
                            '_id' : self.crawl_url,
                            'html': '\n'.join(self.crawl_html) })
                self.crawl_url  = line.split(' ')[0]
                self.crawl_html = []
            self.crawl_html.append(line)
        return count

    def _page_rank(self, url):
        if url in self.cache:
            return self.cache[url]

        # Projection needed for covered query - e.g. a query that is answered
        # completely from the index
        self.cache[url] = int(self.db.rankings.find_one(
                { '_id': url }, { '_id': 0, 'pageRank': 1 })['pageRank'])

        return self.cache[url]
