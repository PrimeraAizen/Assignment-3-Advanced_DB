#!/bin/bash

echo "🔍 Quick Sharding Test"
echo "====================="

# Check if mongos is running
if ! docker ps | grep -q db-mongos-1; then
    echo "❌ Mongos container not running. Start with: docker-compose up -d"
    exit 1
fi

echo ""
echo "📊 Cluster Status:"
docker exec -it db-mongos-1 mongosh --quiet --eval "
const shards = db.adminCommand({ listShards: 1 });
print('Shards: ' + shards.shards.length);
shards.shards.forEach(s => print('  - ' + s._id + ': ' + s.host));
"

echo ""
echo "📈 Data Distribution:"
docker exec -it db-mongos-1 mongosh --quiet --eval "
use logs;
const collExists = db.getCollectionNames().includes('logs');
if (!collExists) {
  print('⚠️  Collection \"logs.logs\" does not exist yet');
  print('You need to import data first!');
  print('');
  print('Steps:');
  print('1. Parse CSV: python parser.py test.csv output.json');
  print('2. Import: docker exec -i db-mongos-1 mongosh < import_script.js');
} else {
  const stats = db.logs.stats();
  if (stats.sharded) {
    print('✅ Collection IS sharded');
    print('Shard Key: ' + JSON.stringify(stats.shardKey));
    print('Total Documents: ' + stats.count);
    print('');
    print('Distribution:');
    Object.keys(stats.shards).forEach(shard => {
      const s = stats.shards[shard];
      const pct = ((s.count / stats.count) * 100).toFixed(2);
      print('  ' + shard + ': ' + s.count + ' docs (' + pct + '%)');
    });
  } else {
    print('⚠️  Collection is NOT sharded');
    print('Total Documents: ' + db.logs.countDocuments());
    print('');
    print('To enable sharding:');
    print('1. sh.enableSharding(\"logs\")');
    print('2. sh.shardCollection(\"logs.logs\", { _id: \"hashed\" })');
  }
}
"

echo ""
echo "🔢 Verification (direct shard access):"
docker exec -it db-mongos-1 mongosh --quiet --eval "
use logs;
if (db.getCollectionNames().includes('logs')) {
  print('Checking document counts on each shard...');
  print('');
}
"

echo "Shard 1 count:"
docker exec -it db-shard1-1 mongosh --quiet --eval "db.getSiblingDB('logs').logs.countDocuments()" 2>/dev/null || echo "0 (or error accessing shard)"

echo "Shard 2 count:"
docker exec -it db-shard2-1 mongosh --quiet --eval "db.getSiblingDB('logs').logs.countDocuments()" 2>/dev/null || echo "0 (or error accessing shard)"

echo ""
echo "✅ Test complete!"
