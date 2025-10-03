// Auto-configure sharding for logs database
// This script runs automatically when the cluster starts

print('========================================');
print('Configuring Sharding for logs Database');
print('========================================');
print('');

// Enable sharding on logs database
try {
    sh.enableSharding('logs');
    print('✅ Sharding enabled on logs database');
} catch (e) {
    if (e.message.includes('already enabled')) {
        print('✅ Sharding already enabled on logs database');
    } else {
        print('⚠️  Error enabling sharding: ' + e.message);
    }
}

// Check if collection exists
use logs;
const collExists = db.getCollectionNames().includes('logs');

if (!collExists) {
    print('ℹ️  Collection does not exist yet - creating and pre-sharding...');
    db.createCollection('logs');
}

// Create hashed index on _id
try {
    db.logs.createIndex({ _id: 'hashed' });
    print('✅ Hashed index created on _id');
} catch (e) {
    print('Index: ' + e.message);
}

// Shard the collection
try {
    sh.shardCollection('logs.logs', { _id: 'hashed' });
    print('✅ Collection logs.logs is now sharded');
    print('✅ Ready to receive data - it will auto-distribute across shards!');
} catch (e) {
    if (e.message.includes('already sharded')) {
        print('✅ Collection already sharded');
    } else {
        print('⚠️  Error sharding collection: ' + e.message);
    }
}

// Show current status
print('');
print('Current Sharding Configuration:');
print('========================================');

const stats = db.logs.stats();
const isSharded = stats.sharded || false;

print('Database: logs');
print('Collection: logs.logs');
print('Sharded: ' + isSharded);

if (isSharded) {
    print('Shard Key: ' + JSON.stringify(stats.shardKey));
    print('Status: ✅ Ready for data import');
    print('');
    print('When you import data, it will automatically');
    print('distribute across both shards (~50/50 split)');
} else {
    print('Status: ⚠️ Not sharded - check errors above');
}

print('');
print('========================================');
print('Auto-configuration Complete!');
print('========================================');
