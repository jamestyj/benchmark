#!/usr/bin/env python
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

"""Inflates/decompresses .deflate files with zlib to STDOUT.

See usage output for details (e.g. run `./inflate.py -h`).
"""

import argparse
import zlib

desc = """Inflates/decompresses .deflate files to STDOUT.

For example, to visually inspect a deflated text file called
'my-file.deflate', execute the following command:

    ./inflate.py my-file.deflate

Deflated CSV can be imported directly by piping to the appropriate
program. For example, to import into MongoDB:

    ./inflate.py data/tiny/rankings/000000_0.deflate | \\
            mongoimport --db $DB_NAME --type csv --stopOnError --drop \\
                        --collection rankings \\
                        --fields 'pageURL,pageRank,avgDuration'
"""
parser = argparse.ArgumentParser(description=desc,
        formatter_class=argparse.RawDescriptionHelpFormatter)
parser.add_argument('files', metavar='FILE', nargs='+',
        help='file to deflate')
args = parser.parse_args()

for fname in args.files:
    with open(fname, 'r') as f:
        print(zlib.decompress(f.read()))
