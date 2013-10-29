db_name = 'bigDataBenchmark'
db = connect('localhost:27017/' + db_name)

// Assume and check that we've loaded the 'tiny' data set properly.
actual_count= db.userVisits.count()
expected_count = 10000
assert(
  actual_count == expected_count,
  "db.userVisits.count() returns " + actual_count + ", should be " + expected_count
)
projection = { _id: 0, pageURL: 1, pageRank: 1 }

print("----------------------------")
print("Query 2 - Aggregation query")
print("----------------------------")
print("SQL:")
print("  SELECT SUBSTR(sourceIP, 1, X), SUM(adRevenue) FROM uservisits GROUP BY SUBSTR(sourceIP, 1, X)")
print()
print("MongoDB query:")
print("  db.userVisits.aggregate(")

query = [
  { $project: {
      _id: 0,
      adRevenue: 1,
      sourceIP_group: { $substr: [ '$sourceIP', 0, 'X' ] }
    }
  },
  { $group: {
      _id: '$sourceIP_group',
      totalRevenue: { $sum: '$adRevenue' }
    }
  },
  { $project: {
      _id: 0,
      sourceIP_group: '$_id',
      totalRevenue: 1
    }
  },
  { $limit: 5 }
]

printjson(query)

print("  )")
print()

db.userVisits.ensureIndex({ sourceIP: 1 })

query[0]['$project']['sourceIP_group']['$substr'][2] = 7
printjson(db.userVisits.aggregate(query))

query[0]['$project']['sourceIP_group']['$substr'][2] = 9
printjson(db.userVisits.aggregate(query))

query[0]['$project']['sourceIP_group']['$substr'][2] = 11
printjson(db.userVisits.aggregate(query))
