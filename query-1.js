db_name = 'bigDataBenchmark'
db = connect('localhost:27017/' + db_name)

// Assume and check that we've loaded the 'tiny' data set properly.
assert(db.rankings.count() == 1200, "db.rankings.count() should return 1200")

projection = { _id: 0, pageURL: 1, pageRank: 1 }

print("--------------------")
print("Query 1 - Scan query")
print("--------------------")
print("SQL:")
print("  SELECT pageURL, pageRank FROM rankings WHERE pageRank > X")
print()
print("MongoDB query:")
print("  db.rankings.count(")
print("    { pageRank: { $gt: X } },")
print("    { _id: 0, pageURL: 1, pageRank: 1 }")
print("  )")

db.rankings.ensureIndex({ pageRank: 1 })

assert(
    db.rankings.count({ pageRank: { $gt: 1000 } }, projection) == 0,
    "There should be 0 URLs with page rank > 1000"
)
assert(
    db.rankings.count({ pageRank: { $gt: 100 } }, projection) == 45,
    "There should be 45 URLs with page rank > 100"
)
assert(
    db.rankings.count({ pageRank: { $gt: 10 } }, projection) == 1200,
    "There should be 1200 URLs with page rank > 10"
)
