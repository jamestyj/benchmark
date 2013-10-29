import Queue
import boto
import glob
import multiprocessing
import pymongo
import sys
import time
from downloadworker  import DownloadWorker
from importworker    import ImportWorker
from utils           import log, num_fmt, sizeof, sizeof_fmt

class Importer:
    def __init__(self, db, opts):
        self.db   = db
        self.opts = opts
        self.queue = multiprocessing.JoinableQueue()

    def import_data_set(self, data_set_name):
        collection_name = self._get_collection_name(data_set_name)

        if not self._check_collection(collection_name):
            return

        if data_set_name == 'uservisits':
            # Index for covered queries
            self.db.rankings.ensure_index([
                    ('_id',      pymongo.ASCENDING),
                    ('pageRank', pymongo.ASCENDING) ])

        if self.opts.local_files:
            for fname in self._get_files(data_set_name):
                with open(fname, 'r') as deflate_file:
                    deflated_csv = deflate_file.read()
                self.queue.put((fname.split('/')[-1], data_set_name, deflated_csv))
            worker_function = self._import_worker
        else:
            bucket = boto.connect_s3().get_bucket('big-data-benchmark')
            path   = "pavlo/text-deflate/%s/%s/" % (self.opts.size, data_set_name)
            for s3_key in bucket.get_all_keys(prefix=path):
                self.queue.put(s3_key)
            worker_function = self._download_and_import_worker

        for _ in xrange(self.opts.workers):
            process = multiprocessing.Process(target=worker_function)
            process.start()

        self.queue.join()

    def _import_worker(self):
        while True:
            try:
                (file_name, data_set_name, deflated_csv) = self.queue.get(block=False)
            except Queue.Empty:
                break
            ImportWorker(self.db, self.opts, file_name, data_set_name, deflated_csv)
            self.queue.task_done()

    def _download_and_import_worker(self):
        while True:
            try:
                s3_key = self.queue.get(block=False)
            except Queue.Empty:
                break
            (file_name, data_set_name, deflated_csv) = DownloadWorker(self.opts, s3_key).get_file()
            ImportWorker(self.db, self.opts, file_name, data_set_name, deflated_csv)
            self.queue.task_done()

    def _get_files(self, data_set_name):
        path  = 'data/%s/%s/*.deflate' % (self.opts.size, data_set_name)
        files = glob.glob(path)
        if len(files) == 0:
            log('ERROR: No data found at %s' % path)
            sys.exit(1)
        return files

    def _get_collection_name(self, data_set_name):
        if data_set_name == 'crawl':
            return 'documents'
        else:
            return data_set_name

    def _check_collection(self, collection_name):
        if self.opts.drop_collection:
            log("Dropping collection '%s'" % collection_name)
            self.db[collection_name].drop()

        count = self.db[collection_name].count()
        if count != 0:
            log("Skipping non-empty collection '%s' (%s docs)" %
                    (collection_name, num_fmt(count)))
            return False
        log("Importing into collection '%s'" % collection_name)
        return True
