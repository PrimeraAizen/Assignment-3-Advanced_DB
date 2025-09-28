# MongoDB Sharded Cluster Setup

This project sets up a MongoDB sharded cluster using Docker Compose. The cluster includes:
- 3 config servers (as a replica set)
- 2 shards (each as a single-node replica set)
- 1 mongos router
- Automated initialization scripts

## Prerequisites
1. **Python 3**: Required for run the CSV to JSON converter
2. **Docker**: Latest version installed
3. **Docker Compose**: Version 1.25.0 or higher

## Getting Started


### 1. Start docker container (for the first task)
```bash
docker run -d \\n  --name mongodb \\n  -p 27017:27017 \\n  -e MONGO_INITDB_ROOT_USERNAME=admin \\n  -e MONGO_INITDB_ROOT_PASSWORD=secret \\n  mongo:latest
```

### 2. Run the test.py script:
```bash
python3 parser.py test.csv output.json
```

### 3. Copy the file to the docker container
```bash
docker cp output.json mongodb:/logs.json
```
### 4. Import the data from JSON:
```bash
docker exec -it mongodb mongoimport \
  --db webLogsDB \
  --collection logs \
  --file /logs.json \
  --jsonArray \
  --username admin \
  --password secret \
  --authenticationDatabase admin
```
### 5. Execute the queries in the queries.txt

### 6. Start the cluster (Second task)
```bash
# Build and start all services in detached mode
docker-compose build
docker-compose up -d
```

### 7. Monitor startup progress
```bash
# Check service status
docker-compose ps

# View logs for a specific service
docker-compose logs -f mongos
```

The cluster will take 2-5 minutes to fully initialize. The setup services (`config-setup`, `shard1-setup`, `shard2-setup`, `cluster-setup`) will run automatically to configure the cluster.

## Connecting to the Cluster

### 1. Connect via mongosh
```bash
mongosh "mongodb://localhost:27017"
```

### 2. Verify cluster status
```javascript
// Check sharding status
sh.status()

// Check config server status
use config
db.shards.find()
```

### 3. Basic operations
```javascript
// Enable sharding for a database
sh.enableSharding("mydatabase")

// Shard a collection
sh.shardCollection("mydatabase.mycollection", { "_id": "hashed" })

// Insert test data
use mydatabase
for (let i = 0; i < 1000; i++) { 
    db.mycollection.insert({ value: i, data: "test" + i }) 
}
```

## Cluster Structure
| Component          | Host Port | Container Port | Internal Address              |
|--------------------|-----------|----------------|-------------------------------|
| **mongos**         | 27017     | 27017          | mongos:27017                  |
| **Config Server 1**| 27119     | 27017          | db-config1-1:27017            |
| **Config Server 2**| 27120     | 27017          | db-config2-1:27017            |
| **Config Server 3**| 27121     | 27017          | db-config3-1:27017            |
| **Shard 1**        | 27118     | 27017          | db-shard1-1:27017             |
| **Shard 2**        | 27128     | 27017          | db-shard2-1:27017             |

## Management Commands

### Stop the cluster
```bash
docker-compose down
```

### Stop and remove all data
```bash
docker-compose down -v
```

### Restart the cluster (persists data)
```bash
docker-compose restart
```

## Troubleshooting
1. **Initialization issues**: Check logs of setup containers:
   ```bash
   docker-compose logs config-setup
   docker-compose logs cluster-setup
   ```
   
2. **Connection problems**: Verify all services are healthy:
   ```bash
   docker-compose ps
   ```

3. **Data persistence**: All MongoDB data is stored in Docker volumes (listed in `docker volume ls`)

## Custom Scripts
Any scripts placed in the `./scripts` directory will be mounted to `/scripts` in all containers. You can add:
- Custom initialization scripts
- Backup/restore scripts
- Data loading scripts

> **Note**: The cluster setup is optimized for development. For production use, consider adding authentication and proper security configurations.