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

# Script for downloading the Big Data Benchmark data set from Amazon S3.
#
# See script usage (e.g. run `./download_data_set.sh`) for details.

function usage() {
    local self=`basename $0`
    echo "Usage: $self [--size SIZE]"
    echo
    echo "Downloads the 'Big Data Benchmark' (http://bit.ly/1azQ4B6) data set"
    echo "from Amazon S3."
    echo ""
    echo "The corresponding .deflate files will be downloaded from Amazon S3"
    echo "and stored locally in the 'data/' directory, to be consumed by the"
    echo "other tools here."
    echo ""
    echo "Requires the Amazon AWS CLI tools (http://aws.amazon.com/cli/) to be"
    echo "installed and configured."
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

S3_URL=s3://big-data-benchmark/pavlo/text-deflate/$size
for data_set in rankings uservisits crawl; do
    dir=data/$size/$data_set
    mkdir -p $dir
    aws s3 cp $S3_URL/$data_set $dir --recursive
done
