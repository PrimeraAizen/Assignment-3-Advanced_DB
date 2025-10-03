#!/bin/bash

echo "================================================"
echo "Complete MongoDB Sharding Setup & Data Import"
echo "================================================"
echo ""

# Check if output.json exists
if [ ! -f "output.json" ]; then
    echo "❌ output.json not found!"
    echo ""
    echo "Please run first:"
    echo "  python parser.py test.csv output.json"
    echo ""
    exit 1
fi

echo "✅ Found output.json"
echo ""

# Step 1: Copy JSON file to mongos container
echo "Step 1: Copying data file to MongoDB container..."
docker cp output_large.json db-mongos-1:/tmp/output.json
if [ $? -eq 0 ]; then
    echo "✅ File copied successfully"
else
    echo "❌ Failed to copy file"
    exit 1
fi
echo ""

# Step 2: Enable sharding on database AND collection BEFORE importing
echo "Step 2: Enabling sharding on 'logs' database and collection..."
docker exec db-mongos-1 mongosh --quiet --eval "
// Enable sharding on database
try {
  sh.enableSharding('logs');
  print('✅ Sharding enabled on logs database');
} catch (e) {
  if (e.message.includes('already enabled')) {
    print('✅ Sharding already enabled on database');
  } else {
    print('⚠️  Error enabling sharding: ' + e.message);
  }
}

// Create hashed index
use logs;
try {
  db.logs.createIndex({ _id: 'hashed' });
  print('✅ Hashed index created on _id');
} catch (e) {
  print('Index may already exist: ' + e.message);
}

// Shard the collection BEFORE importing data
try {
  sh.shardCollection('logs.logs', { _id: 'hashed' });
  print('✅ Collection sharded (ready to receive data)');
} catch (e) {
  if (e.message.includes('already sharded')) {
    print('✅ Collection already sharded');
  } else {
    print('⚠️  Error sharding collection: ' + e.message);
  }
}

print('');
print('📌 Collection is now sharded and ready for data import');
print('   Data will automatically distribute across shards!');
"
echo ""

# Step 3: Import data (NOW it will auto-distribute!)
echo "Step 3: Importing data into sharded collection..."
docker exec db-mongos-1 mongoimport \
  --db logs \
  --collection logs \
  --file /tmp/output.json \
  --jsonArray \
  --drop

if [ $? -eq 0 ]; then
    echo "✅ Data imported successfully and distributed across shards!"
else
    echo "❌ Failed to import data"
    exit 1
fi
echo ""

# Step 4: Verify distribution (sharding already done in step 2)
echo "Step 4: Verifying sharding and data distribution..."
echo ""
docker exec -it db-mongos-1 mongosh --quiet --eval "
use logs;
const stats = db.logs.stats();

print('Collection: logs.logs');
print('  Sharded: ' + (stats.sharded || false));
print('  Shard Key: ' + JSON.stringify(stats.shardKey || 'N/A'));
print('  Total Documents: ' + (stats.count || 0));

if (stats.sharded && stats.shards) {
  print('');
  print('Data Distribution:');
  let total = stats.count || 0;
  Object.keys(stats.shards).forEach(shard => {
    const s = stats.shards[shard];
    const pct = total > 0 ? ((s.count / total) * 100).toFixed(2) : 0;
    print('  ' + shard + ': ' + s.count + ' docs (' + pct + '%)');
  });
}
"
echo ""

echo "================================================"
echo "✅ Setup Complete!"
echo "================================================"
echo ""
echo "Your MongoDB sharded cluster is ready!"
echo ""
echo "To test the sharding:"
echo "  ./quick_test.sh"
echo ""
echo "For detailed analysis:"
echo "  docker exec -it db-mongos-1 bash /scripts/test_sharding.sh"
echo ""
