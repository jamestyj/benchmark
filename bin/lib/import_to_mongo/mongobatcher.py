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

import pymongo
from utils import log

class MongoBatcher:
    """Batches inserts to a MongoDB collection.

    When doing bulk inserts like we are here during the import process,
    batching inserts significantly improves throughput.

    The inserts are flushed to the database when it hits the specified batch
    size, or when .flush() is called.
    """
    def __init__(self, db, collection_name, batch_size):
        self.db              = db
        self.collection_name = collection_name
        self.batch_size      = batch_size
        self.insert_batch    = []

    def insert(self, doc):
        self.insert_batch.append(doc)
        if len(self.insert_batch) >= self.batch_size:
            self.flush()

    def flush(self):
        if len(self.insert_batch) == 0:
            return
        try:
            self.db[self.collection_name].insert(self.insert_batch)
        except pymongo.errors.DuplicateKeyError as err:
            log(err)
        self.insert_batch = []
