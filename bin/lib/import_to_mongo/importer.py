import Queue
import boto
import glob
import pymongo
import sys
import threading
import time
from downloadworker import DownloadWorker
from importworker   import ImportWorker
from utils          import log, num_fmt, sizeof, sizeof_fmt

class Importer:
    def __init__(self, db, opts):
        self.db   = db
        self.opts = opts
        self.download_queue = Queue.Queue()
        self.import_queue   = Queue.Queue()

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
                self.import_queue.put((fname.split('/')[-1], data_set_name,
                        deflated_csv))

        else:
            for _ in xrange(self.opts.download_threads):
                if self.opts.separate_threads:
                    thread = threading.Thread(target=self._download_worker)
                else:
                    thread = threading.Thread(target=self._download_and_import_worker)
                thread.daemon = True
                thread.start()

            bucket = boto.connect_s3().get_bucket('big-data-benchmark')
            path   = "pavlo/text-deflate/%s/%s/" % ( self.opts.size, data_set_name)
            for s3_key in bucket.get_all_keys(prefix=path):
                self.download_queue.put(s3_key)

        if self.opts.separate_threads:
            for _ in xrange(self.opts.import_threads):
                thread = threading.Thread(target=self._import_worker)
                thread.daemon = True
                thread.start()

        self.download_queue.join()
        self.import_queue.join()

    def _download_worker(self):
        while True:
            s3_key = self.download_queue.get()
            self.import_queue.put(DownloadWorker(self.opts, s3_key).get_file())
            self.download_queue.task_done()

    def _import_worker(self):
        while True:
            (file_name, data_set_name, deflated_csv) = self.import_queue.get()
            ImportWorker(self.db, self.opts, file_name, data_set_name, deflated_csv)
            self.import_queue.task_done()

    def _download_and_import_worker(self):
        while True:
            s3_key = self.download_queue.get()
            (file_name, data_set_name, deflated_csv) = DownloadWorker(self.opts, s3_key).get_file()
            ImportWorker(self.db, self.opts, file_name, data_set_name, deflated_csv)
            self.download_queue.task_done()

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
