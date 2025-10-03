# MongoDB Sharded Cluster with Auto-Sharding

This project sets up a production-ready MongoDB sharded cluster using Docker Compose with **automatic sharding configuration** for the `logs` database.

## Architecture

- **3 Config Servers** (replica set for metadata)
- **2 Shards** (replica sets for data distribution)
- **1 Mongos Router** (query router on port 27017)
- **Auto-sharding** (automatic collection sharding on startup)

## Prerequisites

- **Docker** and **Docker Compose**
- **Python 3** (for data generation and parsing)

## Quick Start

### 1. Start the Cluster

```bash
# Start all services
docker-compose up -d

# Wait for initialization (IMPORTANT!)
sleep 90

# Verify auto-sharding configured
docker logs sharding-setup
```

You should see:
```
✅ Sharding enabled on logs database
✅ Hashed index created on _id
✅ Collection logs.logs is now sharded
✅ Ready to receive data
```

### 2. Generate and Import Test Data

```bash
# Generate test data (100,000 records)
python generate_test_data.py 100000

# Parse CSV to JSON
python parser.py test_100000.csv output.json

# Import data (will automatically distribute across shards!)
docker cp output.json db-mongos-1:/tmp/output.json
docker exec db-mongos-1 mongoimport \
  --db logs \
  --collection logs \
  --file /tmp/output.json \
  --jsonArray
```

### 3. Verify Sharding

```bash
# Quick verification
./quick_test.sh

# Or manually check distribution
docker exec db-mongos-1 mongosh --eval "
  db.getSiblingDB('logs').logs.getShardDistribution()
"
```

Expected output:
```
Shard shard1ReplSet: ~50,000 docs (50%)
Shard shard2ReplSet: ~50,000 docs (50%)
```

## Key Features

### Automatic Sharding Configuration

The cluster includes a `sharding-setup` service that automatically:
1. Enables sharding on the `logs` database
2. Creates a hashed index on `_id`
3. Shards the `logs.logs` collection
4. Prepares the cluster for automatic data distribution

**This happens automatically when you start the cluster!**

### Data Validation

The `parser.py` script validates each row with regex patterns:
- **URL validation**: Valid HTTP/HTTPS URLs
- **IP address validation**: Valid IPv4 addresses
- **Timestamp validation**: ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ)
- **Invalid rows** are reported and excluded from output

## Project Structure

```
├── docker-compose.yml          # Cluster configuration
├── parser.py                   # CSV to JSON parser with validation
├── generate_test_data.py       # Test data generator
├── quick_test.sh               # Quick sharding verification
├── setup_and_import.sh         # Automated import script
├── scripts/
│   ├── auto_shard_logs.js     # Auto-sharding configuration (used by docker-compose)
│   ├── test_sharding.sh       # Detailed sharding tests
│   ├── verify_sharding.js     # JavaScript verification script
│   └── analyze_sharding.py    # Python analysis with statistics
└── TESTING_SHARDING.md         # Comprehensive testing guide
```

## Available Scripts

| Script | Purpose |
|--------|---------|
| `generate_test_data.py` | Generate test datasets of any size |
| `parser.py` | Parse and validate CSV to JSON with regex |
| `quick_test.sh` | Quick sharding status check |
| `setup_and_import.sh` | Complete setup and import workflow |
| `scripts/test_sharding.sh` | Detailed sharding analysis and verification |
| `scripts/verify_sharding.js` | JavaScript-based verification |
| `scripts/analyze_sharding.py` | Python analysis with percentages |

## Connecting to the Cluster

### Via MongoDB Shell (mongosh)

```bash
# Connect to mongos router
docker exec -it db-mongos-1 mongosh

# Check sharding status
sh.status()

# View data distribution
use logs
db.logs.getShardDistribution()
```

### Via Python

```python
from pymongo import MongoClient

# Connect to mongos
client = MongoClient('mongodb://localhost:27017/')
db = client['logs']

# Query data (automatically routed to correct shard)
count = db.logs.count_documents({})
print(f"Total documents: {count}")
```

## Important Notes

### Data Distribution

- Data **automatically distributes** across shards when imported
- Uses **hashed sharding** on `_id` for even distribution
- No manual intervention required

### Import Timing

⚠️ **IMPORTANT:** Wait for the cluster to fully initialize before importing data!

```bash
docker-compose up -d
sleep 90  # Wait for sharding-setup to complete
# Now import data
```

If you import too quickly, the collection may not be sharded yet.

### Verifying Sharding

Always check via **mongos** (not individual shards):

```bash
# ✅ CORRECT (via mongos)
docker exec db-mongos-1 mongosh --eval "
  db.getSiblingDB('logs').logs.countDocuments()
"

# ❌ WRONG (direct to shard - may include orphaned docs)
docker exec db-shard1-1 mongosh --eval "
  db.getSiblingDB('logs').logs.countDocuments()
"
```

## Troubleshooting

### Collection Not Sharded

```bash
# Check if auto-sharding completed
docker logs sharding-setup

# Manually shard if needed
docker exec db-mongos-1 mongosh --eval "
  sh.enableSharding('logs');
  db.getSiblingDB('logs').logs.createIndex({ _id: 'hashed' });
  sh.shardCollection('logs.logs', { _id: 'hashed' });
"
```

### Data All on One Shard

**Cause:** Data was imported before sharding was configured.

**Solution:**
```bash
# Drop collection
docker exec db-mongos-1 mongosh --eval "
  db.getSiblingDB('logs').logs.drop()
"

# Restart sharding setup
docker restart sharding-setup

# Re-import data
docker cp output.json db-mongos-1:/tmp/output.json
docker exec db-mongos-1 mongoimport \
  --db logs --collection logs \
  --file /tmp/output.json --jsonArray
```

### Fresh Start

```bash
# Remove all data and start fresh
docker-compose down -v
docker-compose up -d
sleep 90
# Import data
```

## Testing

See [TESTING_SHARDING.md](TESTING_SHARDING.md) for comprehensive testing procedures and verification methods.

## Cluster Architecture

| Component | Host Port | Internal Address |
|-----------|-----------|------------------|
| Mongos Router | 27017 | mongos:27017 |
| Config Server 1 | 27119 | db-config1-1:27017 |
| Config Server 2 | 27120 | db-config2-1:27017 |
| Config Server 3 | 27121 | db-config3-1:27017 |
| Shard 1 | 27118 | db-shard1-1:27017 |
| Shard 2 | 27128 | db-shard2-1:27017 |

### Data Persistence

Data is stored in Docker volumes:
- `config1_data`, `config2_data`, `config3_data` - Config servers
- `shard1_data`, `shard2_data` - Shards

## Management Commands

```bash
# Stop cluster (keeps data)
docker-compose down

# Stop and remove all data
docker-compose down -v

# Restart cluster
docker-compose restart

# View logs
docker-compose logs -f

# View resource usage
docker stats
```

## Advanced Usage

### Manual Sharding Operations

```javascript
// Connect to mongos
docker exec -it db-mongos-1 mongosh

// Enable sharding on a database
sh.enableSharding("mydatabase")

// Shard a collection (range-based)
sh.shardCollection("mydatabase.mycollection", { "field": 1 })

// Shard a collection (hashed)
sh.shardCollection("mydatabase.mycollection", { "_id": "hashed" })

// Check shard distribution
db.mycollection.getShardDistribution()

// Move a chunk manually
sh.moveChunk("mydatabase.mycollection", { field: value }, "shard2ReplSet")
```

### Monitoring

```bash
# Check cluster status
docker exec db-mongos-1 mongosh --eval "sh.status()"

# Check balancer status
docker exec db-mongos-1 mongosh --eval "sh.getBalancerState()"

# View chunk distribution
docker exec db-mongos-1 mongosh --eval "
  use config;
  db.chunks.find({ ns: 'logs.logs' }).pretty()
"
```

## Performance Considerations

- **Chunk Size**: Default is 64 MB, can be adjusted for smaller datasets
- **Balancer**: Runs automatically to distribute data evenly
- **Indexes**: Create appropriate indexes on shard keys
- **Query Routing**: Queries with shard key route to specific shards (faster)
- **Broadcast Queries**: Queries without shard key scan all shards (slower)

## License

This project is for educational purposes.


```bash
docker-compose logs config-setup
docker-compose logs shard1-setup
docker-compose logs shard2-setup
docker-compose logs cluster-setup
```

The setup scripts are idempotent, so they won't fail if services are already initialized.

### Issue: Connection refused

**Solution**: Verify all services are healthy:

```bash
docker-compose ps
```

All services should show `(healthy)` status. If not, check individual service logs:

```bash
docker-compose logs db-config1-1
docker-compose logs mongos
```

### Issue: Slow startup

**Solution**: This is normal. The cluster initialization involves:
1. Starting MongoDB instances
2. Waiting for health checks
3. Initializing replica sets
4. Starting mongos router
5. Adding shards to the cluster

Wait 2-5 minutes for full initialization.

### Issue: Data persistence not working

**Solution**: Check that volumes exist:

```bash
docker volume ls | grep db_
```

You should see volumes for config servers and shards.

## Custom Scripts

The `./scripts` directory is mounted to `/scripts` in all containers. You can add:
- Custom initialization scripts
- Backup/restore scripts
- Data loading scripts
- Migration scripts

Example Python script usage:

```bash
# Run parser.py (requires Python 3)
python3 parser.py
```

## Advanced Configuration

### Adding More Shards

To add a third shard, edit `docker-compose.yml`:

1. Add a new shard service (similar to `db-shard2-1`)
2. Add a new setup service (similar to `shard2-setup`)
3. Update `cluster-setup` to add the new shard

### Enabling Authentication

For production use, add authentication by setting environment variables:

```yaml
environment:
  MONGO_INITDB_ROOT_USERNAME: admin
  MONGO_INITDB_ROOT_PASSWORD: your_secure_password
```

### Scaling Replica Sets

To add more members to each shard's replica set, add additional nodes and update the `rs.initiate()` commands in the setup scripts.

## Notes

- **Development Setup**: This configuration is optimized for development and testing.
- **Production**: For production, enable authentication, use TLS/SSL, and implement proper security measures.
- **Resource Usage**: The cluster uses approximately 2-3 GB of RAM when all services are running.
- **Data Persistence**: All data persists between restarts unless you use `docker-compose down -v`.

## Useful Commands Reference

```bash
# Start cluster
docker-compose up -d

# Stop cluster (keeps data)
docker-compose down

# Stop cluster (removes data)
docker-compose down -v

# View all logs
docker-compose logs

# View specific service logs
docker-compose logs -f mongos

# Check service status
docker-compose ps

# Restart a specific service
docker-compose restart mongos

# Execute command in a running container
docker-compose exec mongos mongosh --eval "sh.status()"

# Connect to MongoDB shell
mongosh "mongodb://localhost:27017"
```

## Project Files

- `docker-compose.yml` - Docker Compose configuration
- `parser.py` - Python script for data parsing
- `test.csv` - Test data file
- `output.json` - Output data file
- `README.md` - This file

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review MongoDB sharding documentation: https://docs.mongodb.com/manual/sharding/
3. Check Docker Compose logs for detailed error messages
