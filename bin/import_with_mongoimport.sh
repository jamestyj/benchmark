#!/bin/bash
#
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

# Wrapper script for importing the CSV data set downloaded from the Big Data
# Benchmark with mongoimport.
#
# See script usage (e.g. run `./import_with_mongoimport.sh`) for details.

function usage() {
    local me=`basename $0`
    echo "Usage: $me [options]"
    echo
    echo "Imports the 'Big Data Benchmark' (http://bit.ly/1azQ4B6) CSV data"
    echo "set (rankings and uservisits) from local .deflate files."
    echo ""
    echo "The .deflate files can be downloaded from Amazon S3 with the"
    echo "'download_data_set.sh' script, and are expected to be in the 'data/'"
    echo "subdirectory (which is the default anyway)."
    echo ""
    echo "Requires MongoDB to running locally on the default port (27017),"
    echo "'inflate.py' to be in the same directory, and 'mongoimport' to be in"
    echo "the system PATH."
    echo
    echo "Options:"
    echo "  --size SIZE    data set size, can be 'tiny' (default), '1node', or"
    echo "                 '5nodes'"
    echo "  --help         show this help message and exit"
}

size=tiny
while [ $# -gt 0 ]; do
    case "$1" in
        --size   ) shift; size=$1;;
        -h|--help) usage; exit 1;;
        *        ) break;;
    esac
    shift
done

for dir in rankings uservisits; do
    case $dir in
        rankings  ) f='pageURL,pageRank,avgDuration';;
        uservisits) f="sourceIP,destURL,visitDate,adRevenue,userAgent,"
                    f="${f}countryCode,languageCode,searchWord,duration"
    esac
    ./inflate.py data/$size/$dir/*.deflate | \
        mongoimport --db bigDataBenchmark-$size --collection $dir --fields $f \
            --type csv --stopOnError --drop
done
