db_name = 'bigDataBenchmark'
db = connect('localhost:27017/' + db_name)

// Assume and check that we've loaded the 'tiny' data set properly.
assert(db.rankings.count() == 1200, "db.rankings.count() should return 1200")

actual_count= db.userVisits.count()
expected_count = 10000
assert(
  actual_count == expected_count,
  "db.userVisits.count() returns " + actual_count + ", should be " + expected_count
)

print("----------------------------")
print("Query 3 - Join query")
print("----------------------------")

// Index for covered query
print("Adding indexes to rankings collection...")
db.rankings.ensureIndex({ pageURL: 1, pageRank: 1 })

print("Dropping rankingsAndUserVisits collection (if exists)...")
db.rankingsAndUserVisits.drop()

print("Pre-joining rankings and userVisits collection to rankingsAndUserVisits...")
db.userVisits.find().forEach(
  function(doc) {
    doc['pageRank'] = db.rankings.findOne(
      { pageURL: doc['destURL'] },
      { _id: 0, pageRank: 1 }       // projection needed for covered query
    )['pageRank']
    db.rankingsAndUserVisits.insert(doc)
  }
)

print("Adding indexes to rankingsAndUserVisits collection...")
db.rankingsAndUserVisits.ensureIndex({ visitDate:    1 })

query = [
  { $match: { visitDate: { $gt: '1980-01-01', $lt: 'X' } } },
  { $group: {
      _id: '$sourceIP',
      totalRevenue: { $sum: '$adRevenue'   },
      avgPageRank:  { $avg: '$pageRank'    },
      visitDate:    { $first: '$visitDate' }
    }
  },
  { $sort: { totalRevenue: -1 } },
  { $limit: 1 }
]

print("Running queries...")

query[0]['$match']['visitDate']['$lt'] = '1980-04-01'
printjson(db.rankingsAndUserVisits.aggregate(query))

query[0]['$match']['visitDate']['$lt'] = '1983-04-01'
printjson(db.rankingsAndUserVisits.aggregate(query))

query[0]['$match']['visitDate']['$lt'] = '2010-04-01'
printjson(db.rankingsAndUserVisits.aggregate(query))
