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

import argparse

def parse_args():
    desc = """
Imports the 'Big Data Benchmark' (http://bit.ly/1azQ4B6) data set into MongoDB.

The data set is imported into MongoDB from one of the following sources:

  1) Local .deflate files (--local_files).
     These files are created by the `download_data_set.sh` tool and are in the
     'data/' subdirectory. This local cache of the raw data set is useful for
     re-populating MongoDB for testing different schemas, etc., as the
     bottleneck is often the network when downloading from S3.

  2) Directly from Amazon S3 (default).
     This eliminates the need to download the entire data set (of a specific
     size) before running the import. It's faster if you will only intend to
     import once and uses significant less disk space as data is imported
     on-the-fly.
     The number of download threads (default 1) is configurable via the
     --download_threads option. Downloads and imports are done in different
     threads so they do not block each other, though the bottleneck is often
     still on the download side, depending on your setup and network.

  The number of import threads (default 1) is configurable for both cases via
  the --import_threads option.

Note that because MongoDB does not support joins, the schema for the
'uservisits' collection (table in SQL terms) includes the 'pageRank' attribute
for query 3.

See README.md for details.
"""
    parser = argparse.ArgumentParser(description=desc,
            formatter_class=argparse.RawDescriptionHelpFormatter)

    parser.add_argument('--size', default='tiny', help=("data set size, can be "
            "'tiny' (default), '1node', or '5nodes'"))
    parser.add_argument('--local_files', action='store_true', default=False,
            help="use local (pre-downloaded) files instead of Amazon S3")
    parser.add_argument('--verbose', action='store_true', default=False,
            help="enable verbose logging (default: false)")

    group = parser.add_argument_group('MongoDB options')
    group.add_argument('--host', default='localhost',
            help="host name (default: 'localhost')")
    group.add_argument('--port', type=int, default=27017,
            help="port number (default: 27017)")
    group.add_argument('--drop_db', action='store_true', default=False,
            help='drop database before importing (default: false)')
    group.add_argument('--drop_collection', action='store_true', default=False,
            help='drop collection before importing (default: false)')
    parser.add_argument_group(group)

    group = parser.add_argument_group('Threading options')
    group.add_argument('--download_threads', type=int, default=1,
            help="number of download threads (default: 1)")
    group.add_argument('--import_threads', type=int, default=1,
            help="number of import threads (default: 1)")
    group.add_argument('--separate_threads', action='store_true',
            default=False, help="use separate download and import threads (default: false")
    parser.add_argument_group(group)

    group = parser.add_argument_group('Additional options')
    group.add_argument('--batch_size', type=int, default=500,
            help='insert batch size (default: 500)')
    group.add_argument('--skip_rankings', action='store_true', default=False,
            help='skip rankings data set (default: false)')
    group.add_argument('--skip_uservisits', action='store_true', default=False,
            help='skip uservisits data set (default: false)')
    group.add_argument('--skip_crawls', action='store_true', default=False,
            help='skip crawls (documents) data set (default: false)')
    group.add_argument('--only_uservisits', action='store_true', default=False,
            help='use only uservisits data set (default: false)')
    parser.add_argument_group(group)

    opts = parser.parse_args()

    if opts.separate_threads:
        print("Using %d threads for both download and import" %
                opts.download_threads)
    else:
        print("Using %d download and %d import threads" % (opts.download_threads,
                opts.import_threads))
    return opts
