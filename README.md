# MongoDB Sharded Cluster Setup

This project sets up a MongoDB sharded cluster using Docker Compose. The cluster includes:
- 3 config servers (as a replica set)
- 2 shards (each as a single-node replica set)
- 1 mongos router
- Automated initialization scripts

## Prerequisites

1. **Python 3**: Required for running custom scripts (e.g., `parser.py`)
2. **Docker**: Latest version installed
3. **Docker Compose**: Version 1.25.0 or higher

## Getting Started

### 1. Build and start the cluster

```bash
# Build the services (if needed)
docker-compose build

# Start all services in detached mode
docker-compose up -d
```

### 2. Monitor startup progress

```bash
# Check service status
docker-compose ps

# View logs for all services
docker-compose logs -f

# View logs for a specific service
docker-compose logs -f mongos
```

The cluster will take 2-5 minutes to fully initialize. The setup services (`config-setup`, `shard1-setup`, `shard2-setup`, `cluster-setup`) will run automatically to configure the cluster.

## Connecting to the Cluster

### 1. Connect via mongosh (MongoDB Shell)

```bash
mongosh "mongodb://localhost:27017"
```

### 2. Connect from Python

```python
from pymongo import MongoClient

# Connect to the mongos router
client = MongoClient('mongodb://localhost:27017/')

# Access a database
db = client['mydatabase']

# Access a collection
collection = db['mycollection']
```

### 3. Verify cluster status

```bash
# Connect to mongos
mongosh "mongodb://localhost:27017"
```

Then in the MongoDB shell:

```javascript
// Check sharding status
sh.status()

// Check config server status
use config
db.shards.find()

// List all databases
show dbs
```

### 4. Basic sharding operations

```javascript
// Enable sharding for a database
sh.enableSharding("mydatabase")

// Shard a collection using hashed sharding
sh.shardCollection("mydatabase.mycollection", { "_id": "hashed" })

// Insert test data
use mydatabase
for (let i = 0; i < 1000; i++) { 
    db.mycollection.insert({ value: i, data: "test" + i }) 
}

// Check data distribution across shards
db.mycollection.getShardDistribution()
```

## Cluster Architecture

| Component          | Host Port | Container Port | Internal Address              |
|--------------------|-----------|----------------|-------------------------------|
| **mongos**         | 27017     | 27017          | mongos:27017                  |
| **Config Server 1**| 27119     | 27017          | db-config1-1:27017            |
| **Config Server 2**| 27120     | 27017          | db-config2-1:27017            |
| **Config Server 3**| 27121     | 27017          | db-config3-1:27017            |
| **Shard 1**        | 27118     | 27017          | db-shard1-1:27017             |
| **Shard 2**        | 27128     | 27017          | db-shard2-1:27017             |

### Network

All services are connected via a Docker bridge network named `db_mongo-cluster`.

### Data Persistence

Data is persisted in Docker volumes:
- `db_config1_data`, `db_config2_data`, `db_config3_data` - Config server data
- `db_shard1_data`, `db_shard2_data` - Shard data

## Management Commands

### Stop the cluster

```bash
docker-compose down
```

### Stop and remove all data

```bash
# Warning: This will delete all data permanently
docker-compose down -v
```

### Restart the cluster (persists data)

```bash
docker-compose restart
```

### View resource usage

```bash
docker stats
```

## Troubleshooting

### Issue: Initialization containers fail

**Solution**: Check logs of setup containers:

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
