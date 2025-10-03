#!/bin/bash

echo "======================================"
echo "MongoDB Sharding Test Script"
echo "======================================"
echo ""

echo "1. Checking Cluster Status..."
echo "======================================"
mongosh --host localhost:27017 --quiet --eval "sh.status()" 

echo ""
echo "2. Checking Shard List..."
echo "======================================"
mongosh --host localhost:27017 --quiet --eval "db.adminCommand({ listShards: 1 })"

echo ""
echo "3. Checking Database Sharding Status..."
echo "======================================"
mongosh --host localhost:27017 --quiet --eval "
use logs
db.stats()
"

echo ""
echo "4. Checking Collection Sharding Details..."
echo "======================================"
mongosh --host localhost:27017 --quiet --eval "
use logs
db.logs.getShardDistribution()
"

echo ""
echo "5. Document Count Per Shard..."
echo "======================================"
mongosh --host localhost:27017 --quiet --eval "
use logs
print('Total documents in collection: ' + db.logs.countDocuments());
"

echo ""
echo "6. Data Distribution by Shard..."
echo "======================================"
mongosh --host localhost:27017 --quiet --eval "
use config
db.chunks.aggregate([
  { \$match: { ns: 'logs.logs' } },
  { \$group: { _id: '\$shard', count: { \$sum: 1 } } },
  { \$sort: { _id: 1 } }
]).forEach(chunk => {
  print('Shard: ' + chunk._id + ' has ' + chunk.count + ' chunk(s)');
});
"

echo ""
echo "7. Detailed Chunk Information..."
echo "======================================"
mongosh --host localhost:27017 --quiet --eval "
use config
db.chunks.find({ ns: 'logs.logs' }).forEach(chunk => {
  print('Shard: ' + chunk.shard);
  print('  Min: ' + JSON.stringify(chunk.min));
  print('  Max: ' + JSON.stringify(chunk.max));
  print('  ---');
});
"

echo ""
echo "8. Sample Documents from Each Shard..."
echo "======================================"

echo "Connecting to Shard 1 (db-shard1-1)..."
mongosh --host db-shard1-1:27017 --quiet --eval "
use logs
print('Shard 1 document count: ' + db.logs.countDocuments());
if (db.logs.countDocuments() > 0) {
  print('Sample document:');
  printjson(db.logs.findOne());
} else {
  print('No documents on this shard');
}
"

echo ""
echo "Connecting to Shard 2 (db-shard2-1)..."
mongosh --host db-shard2-1:27017 --quiet --eval "
use logs
print('Shard 2 document count: ' + db.logs.countDocuments());
if (db.logs.countDocuments() > 0) {
  print('Sample document:');
  printjson(db.logs.findOne());
} else {
  print('No documents on this shard');
}
"

echo ""
echo "======================================"
echo "Test Complete!"
echo "======================================"
