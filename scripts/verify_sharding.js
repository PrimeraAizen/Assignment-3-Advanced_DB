// MongoDB Sharding Verification Script
// Run with: mongosh --host localhost:27017 < verify_sharding.js

print("=====================================");
print("MongoDB Sharding Verification");
print("=====================================\n");

// 1. Check cluster status
print("1. Cluster Status:");
print("-----------------------------------");
sh.status();

// 2. List all shards
print("\n2. Available Shards:");
print("-----------------------------------");
db.adminCommand({ listShards: 1 }).shards.forEach(shard => {
    printjson(shard);
});

// 3. Check if database is sharded
print("\n3. Database Sharding Status:");
print("-----------------------------------");
use logs;
const dbStats = db.stats();
print("Database: logs");
print("  Data Size: " + (dbStats.dataSize / 1024 / 1024).toFixed(2) + " MB");
print("  Storage Size: " + (dbStats.storageSize / 1024 / 1024).toFixed(2) + " MB");
print("  Collections: " + dbStats.collections);
print("  Objects: " + dbStats.objects);

// 4. Check collection sharding
print("\n4. Collection Sharding Details:");
print("-----------------------------------");
const collStats = db.logs.stats();
print("Collection: logs");
print("  Sharded: " + (collStats.sharded ? "YES" : "NO"));
if (collStats.sharded) {
    print("  Shard Key: " + JSON.stringify(collStats.shardKey || "N/A"));
    print("  Total Documents: " + collStats.count);
    print("  Total Size: " + (collStats.size / 1024 / 1024).toFixed(2) + " MB");

    // Show distribution
    print("\n  Distribution by Shard:");
    if (collStats.shards) {
        Object.keys(collStats.shards).forEach(shardName => {
            const shardInfo = collStats.shards[shardName];
            print("    " + shardName + ":");
            print("      Documents: " + shardInfo.count);
            print("      Size: " + (shardInfo.size / 1024 / 1024).toFixed(2) + " MB");
            print("      Avg Doc Size: " + (shardInfo.avgObjSize || 0) + " bytes");
        });
    }
}

// 5. Check chunk distribution
print("\n5. Chunk Distribution:");
print("-----------------------------------");
use config;
const chunks = db.chunks.aggregate([
    { $match: { ns: "logs.logs" } },
    {
        $group: {
            _id: "$shard",
            chunkCount: { $sum: 1 }
        }
    },
    { $sort: { _id: 1 } }
]).toArray();

if (chunks.length > 0) {
    chunks.forEach(chunk => {
        print("  " + chunk._id + ": " + chunk.chunkCount + " chunk(s)");
    });
} else {
    print("  No chunks found. Collection may not be sharded yet.");
}

// 6. Show chunk ranges
print("\n6. Chunk Ranges:");
print("-----------------------------------");
use config;
db.chunks.find({ ns: "logs.logs" }).sort({ min: 1 }).forEach(chunk => {
    print("  Shard: " + chunk.shard);
    print("    Range: " + JSON.stringify(chunk.min) + " -> " + JSON.stringify(chunk.max));
});

// 7. Query routing test
print("\n7. Query Routing Test:");
print("-----------------------------------");
use logs;
const explainResult = db.logs.find({}).limit(1).explain("executionStats");
print("  Query executed across shards:");
if (explainResult.queryPlanner && explainResult.queryPlanner.winningPlan) {
    if (explainResult.queryPlanner.winningPlan.shards) {
        explainResult.queryPlanner.winningPlan.shards.forEach(shard => {
            print("    - " + shard.shardName);
        });
    }
}

// 8. Balance status
print("\n8. Balancer Status:");
print("-----------------------------------");
const balancerStatus = sh.getBalancerState();
print("  Balancer Active: " + balancerStatus);

use config;
const isBalancerRunning = db.locks.findOne({ _id: "balancer" });
if (isBalancerRunning && isBalancerRunning.state > 0) {
    print("  Balancer is currently running");
} else {
    print("  Balancer is idle");
}

print("\n=====================================");
print("Verification Complete!");
print("=====================================");
