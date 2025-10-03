# Testing MongoDB Sharding

This guide explains how to verify that sharding works properly and how data is distributed across shards.

## Prerequisites

1. **Start the cluster:**
   ```bash
   docker-compose up -d
   ```

2. **Wait for initialization** (about 30-60 seconds for all services to be healthy)

## Method 1: Quick Shell Test (Recommended)

Run the bash script:
```bash
chmod +x scripts/test_sharding.sh
docker exec -it db-mongos-1 bash /scripts/test_sharding.sh
```

This will show you:
- Cluster status
- Shard list
- Data distribution
- Chunk information
- Document counts per shard

## Method 2: JavaScript Verification Script

Run the JavaScript verification:
```bash
docker exec -i db-mongos-1 mongosh < scripts/verify_sharding.js
```

This provides detailed information about:
- Cluster configuration
- Sharding status
- Chunk distribution
- Query routing
- Balancer status

## Method 3: Python Analysis Script

If you have Python and pymongo installed:

1. Install pymongo:
   ```bash
   pip install pymongo
   ```

2. Run the analysis:
   ```bash
   python scripts/analyze_sharding.py
   ```

This gives you a comprehensive analysis including percentages and statistics.

## Method 4: Manual Verification via mongosh

### Step 1: Connect to mongos
```bash
docker exec -it db-mongos-1 mongosh
```

### Step 2: Check cluster status
```javascript
sh.status()
```

This shows:
- All shards in the cluster
- Databases and collections
- Sharding configuration

### Step 3: Check if database is sharded
```javascript
use logs
db.stats()
```

### Step 4: Check collection sharding details
```javascript
db.logs.getShardDistribution()
```

This shows:
- Number of documents per shard
- Data size per shard
- Percentage distribution

### Step 5: View chunk distribution
```javascript
use config
db.chunks.aggregate([
  { $match: { ns: "logs.logs" } },
  { $group: { _id: "$shard", count: { $sum: 1 } } }
])
```

### Step 6: Check individual shard document counts

Connect to Shard 1:
```bash
docker exec -it db-shard1-1 mongosh
use logs
db.logs.countDocuments()
db.logs.findOne()  # See a sample document
```

Connect to Shard 2:
```bash
docker exec -it db-shard2-1 mongosh
use logs
db.logs.countDocuments()
db.logs.findOne()  # See a sample document
```

## Understanding the Results

### What to Look For:

1. **Shard Status**
   - You should see 2 shards: `shard1ReplSet` and `shard2ReplSet`
   - Both should show as active

2. **Data Distribution**
   - Documents should be distributed between both shards
   - The distribution depends on your shard key
   - With hash-based sharding, distribution should be roughly even
   - With range-based sharding, distribution depends on your data

3. **Chunk Distribution**
   - Chunks are the units of data migration
   - Multiple chunks allow for better load balancing
   - Initially might have 1-2 chunks, which split as data grows

4. **Expected Distribution Patterns**
   
   **Hash Sharding (e.g., on `_id`):**
   - Nearly 50/50 distribution
   - Example: Shard1: 5000 docs, Shard2: 5000 docs
   
   **Range Sharding (e.g., on `timestamp`):**
   - Distribution based on ranges
   - Newer data might be on one shard
   - Example: Shard1: 3000 docs, Shard2: 7000 docs

## Common Issues and Solutions

### Issue: "Collection is not sharded"
**Solution:** Enable sharding on the collection:
```javascript
use logs
sh.enableSharding("logs")
sh.shardCollection("logs.logs", { _id: "hashed" })
```

### Issue: "All data is on one shard"
**Cause:** Collection might not have enough data to split chunks
**Solution:** 
- Insert more data (MongoDB splits chunks at 64MB by default)
- Or manually split chunks for testing:
```javascript
sh.splitAt("logs.logs", { _id: ObjectId("some-id-in-the-middle") })
```

### Issue: "No shards listed"
**Cause:** Cluster setup didn't complete
**Solution:** 
```bash
docker-compose down
docker-compose up -d
# Wait 60 seconds
docker logs cluster-setup
```

## Verifying Sharding Works

### Test 1: Document Count Verification
```bash
# Total via mongos
docker exec -it db-mongos-1 mongosh --eval "db.getSiblingDB('logs').logs.countDocuments()"

# Shard 1
docker exec -it db-shard1-1 mongosh --eval "db.getSiblingDB('logs').logs.countDocuments()"

# Shard 2
docker exec -it db-shard2-1 mongosh --eval "db.getSiblingDB('logs').logs.countDocuments()"
```

The sum of shard counts should equal the mongos count.

### Test 2: Query Routing
```javascript
// In mongos
use logs
db.logs.find({ _id: ObjectId("specific-id") }).explain()
```

Look for `shards` in the output - shows which shard(s) were queried.

### Test 3: Insert and Watch Distribution
```javascript
// Insert test documents
for (let i = 0; i < 1000; i++) {
  db.logs.insertOne({
    URL: "http://example.com/page" + i,
    IP: "192.168.1." + (i % 256),
    timeStamp: new Date().toISOString(),
    timeSpent: Math.floor(Math.random() * 1000)
  })
}

// Check distribution
db.logs.getShardDistribution()
```

## Performance Testing

To verify sharding improves performance:

```javascript
// Test query performance across shards
use logs
db.logs.find({}).explain("executionStats")
```

Look for:
- `executionTimeMillis` - query execution time
- `totalDocsExamined` - documents scanned
- `shards` - which shards participated

## Summary

A properly working sharded cluster should show:
- ✅ Multiple shards listed and active
- ✅ Data distributed across shards (not all on one)
- ✅ Chunks properly assigned
- ✅ Sum of shard documents = total mongos documents
- ✅ Queries routing to appropriate shards

If all these conditions are met, your sharding is working correctly!
