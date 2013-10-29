# Big Data Benchmark - Tools and MongoDB support

**Table of Contents**  *generated with [DocToc](http://doctoc.herokuapp.com/)*

- [1. Introduction](#1-introduction)
    - [1.1 Disclaimer](#11-disclaimer)
    - [1.2 Feedback and contributions](#12-feedback-and-contributions)
- [2. Benchmark queries in MongoDB](#2-benchmark-queries-in-mongodb)
    - [2.1 Query 1 - Scan query](#21-query-1---scan-query)
        - [2.1.1 Schema](#211-schema)
        - [2.1.2 Query](#212-query)
        - [2.1.3 Index](#213-index)
    - [2.2 Query 2 - Aggregation query](#22-query-2---aggregation-query)
        - [2.2.1 Schema](#221-schema)
        - [2.2.2 Query](#222-query)
        - [2.2.3 Index](#223-index)
    - [2.3 Query 3 - Join query](#23-query-3---join-query)
        - [2.3.1 Schema](#231-schema)
        - [2.3.2 Query](#232-query)
        - [2.3.3 Index](#233-index)
    - [2.4 Query 4 - User defined query](#24-query-4---user-defined-query)
        - [2.4.1 Schema](#241-schema)
        - [2.4.2 Query](#242-query)
- [3. Data set tools](#3-data-set-tools)
    - [3.1 `download_data_set.sh`](#31-download_data_setsh)
        - [3.1.1 Installation](#311-installation)
        - [3.1.2 Sample output](#312-sample-output)
    - [3.2. `inflate.py`](#32-inflatepy)
    - [3.3 `import_with_mongoimport.sh`](#33-import_with_mongoimportsh)
    - [3.4 `import_to_mongo.py`](#34-import_to_mongopy)
        - [3.4.1 Installation](#341-installation)
        - [3.4.2 Sample output](#342-sample-output)
        - [3.4.3 Code](#343-code)
- [4. Running it yourself](#4-running-it-yourself)
    - [4.1 Loading the data set](#41-loading-the-data-set)
        - [4.1.1 On local system](#411-on-local-system)
        - [4.1.2 On Amazon EC2](#412-on-amazon-ec2)
            - [4.1.2.1 EC2 setup for `1node` data set](#4121-ec2-setup-for-1node-data-set)
            - [4.1.2.2 EC2 setup for `5nodes` data set](#4122-ec2-setup-for-5nodes-data-set)

## 1. Introduction

This fork of the [code](https://github.com/amplab/benchmark) for the [Big Data
Benchmark](https://amplab.cs.berkeley.edu/benchmark/) adds MongoDB support and
a number of general tools that can be used to download, inspect, and load the
benchmark data set to other databases.

### 1.1 Disclaimer

This is done in my spare time on a best-effort basis, and not officially
supported by me or any organization. It's really more for me to play around
with the different technologies here (e.g. Python, MongoDB, and Amazon Web
Services).

As most are aware, MongoDB is very different from the other tools in this
benchmark (e.g. Hadoop, Hive, Spark, and Shark), so a direct comparison doesn't
really make sense. The interesting parts (at least for me) figuring out how to
load such data sets into MongoDB, how to run the equivalent queries, what the
trade-offs are, tweaking performance, etc.

### 1.2 Feedback and contributions

Please use Github Issues to file bug reports and feature requests. Pull
requests for both code and documentation contributions are very welcomed.

## 2. Benchmark queries in MongoDB

The benchmark runs four different types of SQL queries to see how each data
store performs. MongoDB has its own query API and does not use SQL, so we need
to map these accordingly. In addition, the way MongoDB works requires a couple
of schema tweaks for queries 3 and 4.

The following resources provide a pretty good overview for those new to
MongoDB:

  * [Introduction to MongoDB](http://docs.mongodb.org/manual/core/introduction/)
  * [MongoDB fundamentals](http://docs.mongodb.org/manual/faq/fundamentals/)
  * [SQL to MongoDB mapping chart](http://docs.mongodb.org/manual/reference/sql-comparison/)

### 2.1 Query 1 - Scan query

#### 2.1.1 Schema

This is a simple query on the `rankings` table/collection. The SQL schema is:

```sql
pageURL     VARCHAR(300)
pageRank    INT
avgDuration INT
```

And the corresponding MongoDB schema is:

```js
{ 'pageURL':     STRING,
  'avgDuration': INT,
  'pageRank':    INT }
```

MongoDB requires a `_id` field as primary key in every collection, and
implicitly creates it with an
[ObjectID](http://docs.mongodb.org/manual/reference/object-id/) if necessary. So the actual schema looks like this:

```js
{ '_id':         ObjectID,
  'pageURL':     STRING,
  'avgDuration': INT,
  'pageRank':    INT }
```

The primary key `_id` must be unique, and in this case so is `pageURL`. Hence
we can simplify the schema slightly and save [12
bytes](http://docs.mongodb.org/manual/reference/glossary/#term-objectid) per
record/document by storing `pageURL` in `_id`. We then also get the unique
constraint for free:

```js
{ '_id':         STRING,  // pageURL instead of ObjectID
  'avgDuration': INT,
  'pageRank':    INT }
```

#### 2.1.2 Query

The SQL query from the benchmark, where `X` is an integer, is:

```sql
SELECT pageURL, pageRank FROM rankings WHERE pageRank > X
```

The direct map to MongoDB is:

```js
db.rankings.find({ 'pageRank': { '$gt': X } }, { '_id': 0, 'pageURL': 1, 'pageRank': 1 })
```

The MongoDB query that matches our optimized schema (which was described in the
previous section) is:

```js
db.rankings.find({ 'pageRank': { '$gt': X } }, { 'pageRank': 1 })
```

Executing this in the Mongo shell with the benchmark data set returns results
like this:


```js
{ '_id':      "hxewpbthwbsqaoizoasasdsadavvnnss",  // pageURL
  'pageRank': 70
}
{  '_id':     "safsdfsadfdfaasdf",
  'pageRank': 12
}
{ '_id':      "zvsadfsgaskdghsadfasdsdasd",
  'pageRank': 5
}
...
```

Refer to the following links for more details on the MongoDB query syntax:

  * [Tutorial - Query documents](http://docs.mongodb.org/manual/tutorial/query-documents/)
  * [Read operations](http://docs.mongodb.org/manual/core/read-operations/)

#### 2.1.3 Index

Indexes (among other things) are critical for performant queries in large data
sets. In this case, we can create an index with the following command to allow
[covered queries](http://docs.mongodb.org/manual/tutorial/create-indexes-to-support-queries/#create-indexes-that-support-covered-queries):

```js
db.rankings.ensureIndex({ '_id': 1, 'pageRank': 1 })
```

### 2.2 Query 2 - Aggregation query

#### 2.2.1 Schema

This is an aggregation query on the `uservisits` table/collection. The SQL
schema is:

```sql
sourceIP     VARCHAR(116)
destURL      VARCHAR(100)
visitDate    DATE
adRevenue    FLOAT
userAgent    VARCHAR(256)
countryCode  CHAR(3)
languageCode CHAR(6)
searchWord   VARCHAR(32)
duration     INT
```

And the corresponding MongoDB schema is:

```js
{ '_id':          ObjectId,
  'languageCode': STRING,
  'countryCode':  STRING,
  'destURL':      STRING,
  'visitDate':    STRING,    // e.g. '1978-10-17'
  'searchWord':   STRING,
  'duration':     INT,
  'userAgent':    STRING,
  'sourceIP':     STRING,
  'adRevenue':    FLOAT
}
```


#### 2.2.2 Query

The SQL query from the benchmark, where `X` is an integer, is:

```sql
SELECT SUBSTR(sourceIP, 1, X), SUM(adRevenue) FROM uservisits GROUP BY SUBSTR(sourceIP, 1, X)
```

The corresponding MongoDB query (using the [aggregation
framework](http://docs.mongodb.org/manual/core/aggregation-introduction/)) is:

```js
db.uservisits.aggregate([
    { '$project': { '_id': 0, 'adRevenue': 1, 'sourceIP_group': { '$substr': [ '$sourceIP', 0, X ] } } },
    { '$group':   { '_id': '$sourceIP_group', 'totalRevenue': { '$sum': '$adRevenue' } } }
])
```

Executing this in the Mongo shell with the benchmark data set returns results
like this:

```js
{ 'result': [
      { '_id': "151.93.", 'totalRevenue': 0.12406796 },
      { '_id': "209.149", 'totalRevenue': 0.1138975  },
      { '_id': "66.64.1", 'totalRevenue': 0.58491534 },
      ...
  ],
  'ok': 1
}
```

Note that for MongoDB version 2.4 and below there is a [16MB
limit](http://docs.mongodb.org/manual/reference/limits/#BSON%20Document%20Size)
on the aggregation result set, hence you'll want to limit the number of results
when querying large data sets (e.g. adding a `{ $limit: 1000 }` in the
aggregation query pipeline). This limitation is [resolved in version 2.6 and
above](http://docs.mongodb.org/master/release-notes/2.6/#aggregation-operations-now-return-cursors).

#### 2.2.3 Index

Create an index to speed up this query with the following command:

```js
db.uservisits.ensureIndex({ 'sourceIP': 1 })
```

### 2.3 Query 3 - Join query

#### 2.3.1 Schema

The join query operates on the `rankings` and `uservisits` tables/collections
that have been explained in the previous sections, so we won't repeat the
schemas here.

However, joins are not supported in MongoDB, so we need to either change the
schema to pre-join at insert time, or join it in the application layer. In this
case, we went with pre-joining as it only adds a single integer field to the
`uservisits` collection:

```js
{ '_id':          ObjectId,
  'languageCode': STRING,
  'countryCode':  STRING,
  'destURL':      STRING,
  'visitDate':    STRING,    // e.g. '1978-10-17'
  'searchWord':   STRING,
  'duration':     INT,
  'userAgent':    STRING,
  'sourceIP':     STRING,
  'adRevenue':    FLOAT,
  'pageRank':     INT        // New field here, from the rankings collection
}
```

#### 2.3.2 Query

The join query is a more complicated as it pulls and aggregates data from two
tables. The SQL query, where `X` is a date string, is:

```sql
SELECT sourceIP, totalRevenue, avgPageRank
FROM
(SELECT sourceIP,
        AVG(pageRank) as avgPageRank,
        SUM(adRevenue) as totalRevenue
    FROM Rankings AS R, UserVisits AS UV
    WHERE R.pageURL = UV.destURL
    AND UV.visitDate BETWEEN Date('1980-01-01') AND Date(X)
    GROUP BY UV.sourceIP)
ORDER BY totalRevenue DESC LIMIT 1
```

The corresponding MongoDB query with the modified schema (pre-joined with
`pageRank` field) is:

```js
db.uservisits.aggregate([
    { '$match': { 'visitDate': { '$gt': '1980-01-01', '$lt': X } } },
    { '$group': { '_id': '$sourceIP',
                'totalRevenue': { '$sum':   '$adRevenue'   },
                'avgPageRank':  { '$avg':   '$pageRank'    },
                'visitDate':    { '$first': '$visitDate' } } },
    { '$sort': { 'totalRevenue': -1 } },
    { '$limit': 1 },
    { '$project': { '_id': 0, 'sourceIP': '$_id', 'totalRevenue': 1, 'avgPageRank': 1 } }
])
```

Executing this in the Mongo shell with the benchmark data set returns results
like this:

```js
{ 'result': [ { 'sourceIP':  '155.43.143.48', 'totalRevenue': 1.9997925, 'avgPageRank': 14 ],
  'ok': 1
}
```

#### 2.3.3 Index

Create an index to speed up this query with the following command:

```js
db.uservisits.ensureIndex({ 'visitDate': 1 })
```

### 2.4 Query 4 - User defined query

#### 2.4.1 Schema

This schema is a bit more unusual as it's stored as just a blob of unstructured
text. The SQL command to create the table (for Shark) is:

```sql
CREATE EXTERNAL TABLE documents (line STRING) STORED AS TEXTFILE
LOCATION "/user/shark/benchmark/crawl";
```

MongoDB has a size limitation of [16MB per
document](http://docs.mongodb.org/manual/reference/limits/#BSON%20Document%20Size),
so we'll need to store it a bit differently. The approach we went with here is
to parse the text blob during import and split it into one document per URL:

```js
{ '_id':  STRING,  // URL
  'html': STRING   // HTML text blob
}
```

#### 2.4.2 Query

The SQL user defined query runs the [url_count.py](runner/udf/url_count.py)
Python script as part of the query operation:

```sql
CREATE TABLE url_counts_partial AS
SELECT TRANSFORM (line)
    USING "python /root/url_count.py" as (sourcePage, destPage, cnt)
FROM documents;
CREATE TABLE url_counts_total AS
SELECT SUM(cnt) AS totalCount, destPage
FROM url_counts_partial
GROUP BY destPage;
```

Among the frameworks tested in the benchmark, this is supported by Shark and
Hive only. The MongoDB version will be added here soon.

## 3. Data set tools

This section describes a couple of tools written to inspect and work with the
benchmark data set. They are useful for downloading a copy or sample of the
benchmark data locally, for inspection and perhaps import to other databases.

All these tools are in the `bin/` subdirectory.

### 3.1 `download_data_set.sh`

[download_data_set.sh](bin/download_data_set.sh) is a small bash tool that
downloads the data set files from Amazon S3. Here's an example of its help
output:

```
> ./download_data_set.sh --help
Usage: download_data_set.sh [--size SIZE]

Downloads the 'Big Data Benchmark' (http://bit.ly/1azQ4B6) data set
from Amazon S3.

The corresponding .deflate files will be downloaded from Amazon S3
and stored locally in the 'data/' directory, to be consumed by the
other tools here.

Requires the Amazon AWS CLI tools (http://aws.amazon.com/cli/) to be
installed and configured.

Options:
  --size SIZE    data set size, can be 'tiny' (default), '1node', or
                 '5nodes'
  --help         show this help message and exit
```

#### 3.1.1 Installation

The script relies on the [AWS Command Line
Interface](http://aws.amazon.com/cli/) (CLI) to download files from Amazon S3,
which can be installed with [Pip](http://www.pip-installer.org), e.g.:

```
> pip install awscli
```

You'll also need to configure your environment variables to contain your AWS
credentials. For example, add the following lines to your `~/.bashrc` or
equivalent:

```bash
export AWS_DEFAULT_REGION='YOUR_PREFERRED_EC2_REGION'   # e.g. 'eu-west-1'
export AWS_ACCESS_KEY_ID='<YOUR_AWS_ACCESS_KEY>'
export AWS_SECRET_ACCESS_KEY='<YOUR_AWS_SECRET_KEY>'
```

For more details, refer to the [AWS CLI getting started
guide](http://docs.aws.amazon.com/cli/latest/userguide/cli-chap-getting-started.html).

#### 3.1.2 Sample output

If you run the script without any options, it downloads the `tiny` data set
(.deflate) into the `data/` subdirectory. For example:

```
> cd bin/
> ./download_data_set.sh
download: s3://big-data-benchmark/pavlo/text-deflate/tiny/rankings/000000_0.deflate to data/tiny/rankings/000000_0.deflate
download: s3://big-data-benchmark/pavlo/text-deflate/tiny/rankings/000004_0.deflate to data/tiny/rankings/000004_0.deflate
...
download: s3://big-data-benchmark/pavlo/text-deflate/tiny/uservisits/000000_0.deflate to data/tiny/uservisits/000000_0.deflate
download: s3://big-data-benchmark/pavlo/text-deflate/tiny/uservisits/000008_0.deflate to data/tiny/uservisits/000008_0.deflate
...
download: s3://big-data-benchmark/pavlo/text-deflate/tiny/crawl/000000_0.deflate to data/tiny/crawl/000000_0.deflate
download: s3://big-data-benchmark/pavlo/text-deflate/tiny/crawl/000001_0.deflate to data/tiny/crawl/000001_0.deflate
...
```

Note that the file numbers may not be in sequence as they are downloaded in
parallel. These files are now on your local file system:

```
> ls -lhR data/tiny
total 0
drwxr-xr-x  341 jamestyj  staff    11K 31 Oct 18:27 crawl
drwxr-xr-x   12 jamestyj  staff   408B 31 Oct 18:26 rankings
drwxr-xr-x   12 jamestyj  staff   408B 31 Oct 18:27 uservisits

data/tiny/crawl:
total 6936
-rw-r--r--  1 jamestyj  staff    11K 27 May 22:22 000000_0.deflate
...
-rw-r--r--  1 jamestyj  staff   8.0K 27 May 22:27 000338_0.deflate

data/tiny/rankings:
total 160
-rw-r--r--  1 jamestyj  staff   4.8K 27 May 22:22 000000_0.deflate
...
-rw-r--r--  1 jamestyj  staff   4.4K 27 May 22:22 000009_0.deflate

data/tiny/uservisits:
total 872
-rw-r--r--  1 jamestyj  staff    41K 27 May 22:22 000000_0.deflate
...
-rw-r--r--  1 jamestyj  staff    43K 27 May 22:22 000009_0.deflate
>
```

You can choose which data set to download with the `--size` option, but do note
[their size](https://amplab.cs.berkeley.edu/benchmark/#running)! Only the
deflated (compressed) data set are downloaded though, so `tiny`, `1node`, and
`5nodes` uses 3.9 MB, 13 GB, and (estimated) 63 GB respectively on disk. This
gets decompressed and when imported into the database, so be sure that you have
sufficient free disk space.

### 3.2. `inflate.py`

[inflate.py](bin/inflate.py) is a small Python script for decompressing the
.deflate files that we've downloaded with the `download_data_set.sh` script.
Sample help output:

```
> ./inflate.py --help
usage: inflate.py [-h] FILE [FILE ...]

Inflates/decompresses .deflate files to STDOUT.

For example, to visually inspect a deflated text file called
'my-file.deflate', execute the following command:

    ./inflate.py my-file.deflate

Deflated CSV can be imported directly by piping to the appropriate
program. For example, to import into MongoDB:

    ./inflate.py data/tiny/rankings/000000_0.deflate | \
            mongoimport --db $DB_NAME --type csv --stopOnError --drop \
                        --collection rankings \
                        --fields 'pageURL,pageRank,avgDuration'

positional arguments:
  FILE        file to deflate

optional arguments:
  -h, --help  show this help message and exit
```

Sample run output:

```
> ./inflate.py data/tiny/rankings/000000_0.deflate | head
nbizrgdziebsaecsecujfjcqtvnpcnxxwiopmddorcxnlijdizgoi,665,16
jakofwkgdcxmaaqphkefckecrnsmqtbybrorlfoorfwuzslduxfpiptfyzbjzwcjitndchuptnmnwhbowwshlundckhusummi,187,29
kvhuvcjzcudugtidficcrnaxwikdaahttrfjfnfuxmasilbupuxcmkvlraebhkvfeycexgsyhtefvymctz,120,20
rcajacqehfdmpykymvmbiscwpabihuyaijbucgwaixtwdrkegfpbofgnwpbfjxjtdnvhyjflyidz,111,97
brailztgjgjrffrxfoxtfrlupszcinjvocprnfirtkijgpwrrgy,107,54
oiavraahcejwugzssvrzakqseqkbfwvmhhqjdmxzjlqimypmsglukddrsaalbnnt,96,14
asesbkwwybjipvugqiiacidbrspqmfxppw,89,51
sshlgtsaolmuliksiukgyfxwczfqvbhjceimgnrgdwgaqiarvujwblpbnphggnys,90,92
quklyshfdvzgeefoozkihfnltayefkvhgnxipcfch,86,2
fkxmjzufvktnoqroyrcoyfblpfdoigfqbubjjoxmgcruvizwdzbmrzvtgvenwp,64,38
```

### 3.3 `import_with_mongoimport.sh`

[import_with_mongoimport.sh](bin/import_with_mongoimport.sh) is another small
bash script that imports the `rankings` and `uservisits` data sets directly
into MongoDB using the `mongoimport` tool. Sample help output:

```
> ./import_with_mongoimport.sh --help
Usage: import_with_mongoimport.sh [options]

Imports the 'Big Data Benchmark' (http://bit.ly/1azQ4B6) CSV data
set (rankings and uservisits) from local .deflate files.

The .deflate files can be downloaded from Amazon S3 with the
'download_data_set.sh' script, and are expected to be in the 'data/'
subdirectory (which is the default anyway).

Requires MongoDB to running locally on the default port (27017),
'inflate.py' to be in the same directory, and 'mongoimport' to be in
the system PATH.

Options:
  --size SIZE    data set size, can be 'tiny' (default), '1node', or
                 '5nodes'
  --help         show this help message and exit
```

Sample run output:

```
> ./import_with_mongoimport.sh
connected to: 127.0.0.1
Tue Nov  5 17:34:05.345 dropping: bigDataBenchmark-tiny.rankings
Tue Nov  5 17:34:05.403 check 9 1200
Tue Nov  5 17:34:05.409 imported 1200 objects
connected to: 127.0.0.1
Tue Nov  5 17:34:05.441 dropping: bigDataBenchmark-tiny.uservisits
Tue Nov  5 17:34:06.026 check 9 10000
Tue Nov  5 17:34:06.026 imported 10000 objects
```

Importing local CSV files with `mongoimport` is fast, but because we need to
modify the `uservisits` schema (e.g. add the `pageRank` field) for query 3,
it's not really useful. In addition, it can't directly import the `crawls` data
set into the `documents` collection because it's not in CSV format.

### 3.4 `import_to_mongo.py`

[import_to_mongo.py](bin/import_to_mongo.py) is the main tool, written in
Python, for importing the data set into MongoDB with the schema that we need
for the benchmark queries. It was written to address the shortcomings of the
`import_with_mongoimport.sh` script, and also supports direct import from
Amazon S3. The download and import code are executed in different threads so
they don't block each other.

Sample help output:

```
> ./import_to_mongo.py --help
usage: import_to_mongo.py [-h] [--size SIZE] [--local_files] [--verbose]
                          [--host HOST] [--port PORT] [--drop_db]
                          [--drop_collection]
                          [--download_threads DOWNLOAD_THREADS]
                          [--import_threads IMPORT_THREADS]
                          [--batch_size BATCH_SIZE] [--skip_rankings]
                          [--skip_uservisits] [--skip_crawls]
                          [--only_uservisits]

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

optional arguments:
  -h, --help            show this help message and exit
  --size SIZE           data set size, can be 'tiny' (default), '1node', or
                        '5nodes'
  --local_files         use local (pre-downloaded) files instead of Amazon S3
  --verbose             enable verbose logging (default: false)

MongoDB options:
  --host HOST           host name (default: 'localhost')
  --port PORT           port number (default: 27017)
  --drop_db             drop database before importing (default: false)
  --drop_collection     drop collection before importing (default: false)

Threading options:
  --download_threads DOWNLOAD_THREADS
                        number of download threads (default: 1)
  --import_threads IMPORT_THREADS
                        number of import threads (default: 1)

Additional options:
  --batch_size BATCH_SIZE
                        insert batch size (default: 500)
  --skip_rankings       skip rankings data set (default: false)
  --skip_uservisits     skip uservisits data set (default: false)
  --skip_crawls         skip crawls (documents) data set (default: false)
  --only_uservisits     use only uservisits data set (default: false)
```

#### 3.4.1 Installation

Install the required dependencies by running the following command:

```
pip install boto pymongo pylru
```

You'll also need to configure your environment variables to contain your AWS
credentials. For example, add the following lines to your `~/.bashrc` or
equivalent:

```bash
export AWS_DEFAULT_REGION='YOUR_PREFERRED_EC2_REGION'   # e.g. 'eu-west-1'
export AWS_ACCESS_KEY_ID='<YOUR_AWS_ACCESS_KEY>'
export AWS_SECRET_ACCESS_KEY='<YOUR_AWS_SECRET_KEY>'
```

#### 3.4.2 Sample output

```
> ./import_to_mongo.py
Using 1 download and 1 import threads
2013-11-05 17:52:43 Using database 'bigDataBenchmark-tiny'
2013-11-05 17:52:43 Importing into collection 'rankings'
2013-11-05 17:52:44 Thread-1 000000_0.deflate: Downloaded 4.8 KB in 0.1s (37.1 KB/s)
2013-11-05 17:52:44 Thread-1 000001_0.deflate: Downloaded 4.9 KB in 0.1s (37.1 KB/s)
2013-11-05 17:52:44 Thread-2 000000_0.deflate: Imported 120 docs (798 per sec)
2013-11-05 17:52:46 Thread-2 000009_0.deflate: Imported 120 docs (51,947 per sec)
...
2013-11-05 17:52:46 Importing into collection 'uservisits'
2013-11-05 17:52:47 Thread-3 000000_0.deflate: Downloaded 41.4 KB in 0.4s (101.4 KB/s)
2013-11-05 17:52:47 Thread-2 000000_0.deflate: Imported 995 docs (12,176 per sec)
...
2013-11-05 17:52:49 Importing into collection 'documents'
2013-11-05 17:52:50 Thread-5 000000_0.deflate: Downloaded 11.0 KB in 0.1s (83.4 KB/s)
2013-11-05 17:52:50 Thread-4 000000_0.deflate: Imported 0 docs (0 per sec)
...
```

#### 3.4.3 Code

Some parts of the code might be interesting to look at from an implementation
perspective, and to see how things are done under the hood. In particular, the
following two files (both relatively well documented):

  * [importworker.py](bin/lib/import_to_mongo/importworker.py) - Code executed
    by the import thread, which defaults to one thread but can be configured to
    more (though usually the bottleneck is the download). See the documentation
    within the code for details.

  * [mongobatcher.py](bin/lib/import_to_mongo/mongobatcher.py) - Class that
    implements a simple but effective batch insert mechanism.

## 4. Running it yourself

The most interesting part is, of course, running all these yourself. It's a
good way to understand in detail what the benchmark does and how MongoDB works
for this kind of data set, as well as the trade-offs and quirks.

### 4.1 Loading the data set

#### 4.1.1 On local system

Here's a list of recommended steps to load the `1node` data set locally:

  1. [Install MongoDB](http://docs.mongodb.org/manual/installation) and run it
     with the default settings (e.g. on port `27017` - not required but keeps
     things simple).

  1. **Optional, but recommended**: Download and cache the `tiny` (3.9 MB) and
     `1node` (13 GB) compressed data sets locally. This is recommended for
     working offline and re-importing from the local cache to try out different
     schemas (downloading from Amazon S3 is slow).
       * Install and configure the [dependencies for
         download_data_set.sh](#31-download_data_setsh).
       * Download both data sets, e.g.:

         ```bash
         cd bin
         ./download_data_set.sh
         ./download_data_set.sh --size 1node
         ```

  1. Install and configure the [dependencies for
     import_to_mongo.py](#34-import_to_mongopy).

  1. Import both data sets:
       * If you performed the optional step to cached the compressed data files
         locally, run the following:

         ```bash
         ./import_to_mongo.py --local
         ./import_to_mongo.py --local --size 1node
         ```
       * Otherwise omit the `--local` option:

         ```bash
         ./import_to_mongo.py
         ./import_to_mongo.py --size 1node
         ```

#### 4.1.2 On Amazon EC2

Running the test on Amazon EC2 is more useful for comparing the results, and
it's easier to tweak different hardware and system settings, among other
things.

We use [Vagrant](http://www.vagrantup.com/) and
[Chef](http://www.opscode.com/chef/) to automate the setup and configuration of
the Amazon EC2 instances. Here are the steps:

 1. [Install Vagrant](http://docs.vagrantup.com/v2/installation/).

 1. Install the Vagrant AWS plugin. We want to use EBS optimized EC2 instances,
    which is not yet supported in the current stable release of the Vagrant AWS
    plugin. Hence we'll need to install it from Git:

    ```bash
    git clone git@github.com:mitchellh/vagrant-aws.git
    gem install bundler
    bundle install
    rake build
    vagrant plugin install pkg/vagrant-aws-0.5.0.dev.gem
    ```

    Note that you need install `git` and `ruby` first if they are not already
    installed on your system.

For more information on bulk loading and running MongoDB in EC2, refer to the
following links:

  * https://wiki.mongodb.com/display/cs/Guide+to+perform+Bulk+Load(s)+with+MongoDB+on+EC2
  * http://docs.mongodb.org/ecosystem/platforms/amazon-ec2/

##### 4.1.2.1 EC2 setup for `1node` data set

For the `1node` data set we spin up two EC2 instances:

  1. `benchmark` instance: This contains a Git checkout of the code at
     github.com/jamestyj/benchmark, and it used to import the data set into
     MongoDB.

  1. `mongodb` instance: This contains a running and fully configured MongoDB
     instance. It uses provisioned IOPS on multiple volumes, so be wary of the
     associated usage costs! Tweak the configuration in
     [Vagrantfile](vagrant-1node/Vagrantfile) accordingly to fit your
     needs and budget.

Here are the steps:

```
cd vagrant-1node
./up
```

It can take about 10 minutes before the instances are up and running. Then you
can SSH into the MongoDB instance by running:

```
vagrant ssh mongodb
```

Note the host name in the prompt. Now SSH to the `benchmark` instance and run
the import:

```
vagrant ssh benchmark
cd benchmark
./import_to_mongo.py --host <HOSTNAME> --size 1node
```

##### 4.1.2.2 EC2 setup for `5nodes` data set

Coming soon...
