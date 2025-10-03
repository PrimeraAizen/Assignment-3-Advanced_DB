#!/usr/bin/env python3
"""
MongoDB Sharding Distribution Analysis
This script connects to your sharded MongoDB cluster and analyzes data distribution
"""

from pymongo import MongoClient
from collections import defaultdict
import json

# Connection strings
MONGOS_URI = "mongodb://localhost:27017/"
SHARD1_URI = "mongodb://localhost:27118/"
SHARD2_URI = "mongodb://localhost:27128/"


def analyze_cluster():
    """Analyze the sharded cluster configuration and data distribution"""

    print("=" * 60)
    print("MongoDB Sharding Analysis")
    print("=" * 60)

    try:
        # Connect to mongos router
        client = MongoClient(MONGOS_URI)
        admin_db = client.admin

        # 1. Check cluster status
        print("\n1. CLUSTER CONFIGURATION")
        print("-" * 60)

        shards_info = admin_db.command("listShards")
        print(f"Number of shards: {len(shards_info['shards'])}")
        for shard in shards_info["shards"]:
            print(f"  - {shard['_id']}: {shard['host']}")

        # 2. Database information
        print("\n2. DATABASE STATUS")
        print("-" * 60)

        db = client["logs"]
        db_stats = db.command("dbStats")
        print(f"Database: logs")
        print(f"  Collections: {db_stats['collections']}")
        print(f"  Data Size: {db_stats['dataSize'] / 1024 / 1024:.2f} MB")
        print(f"  Storage Size: {db_stats['storageSize'] / 1024 / 1024:.2f} MB")
        print(f"  Indexes: {db_stats['indexes']}")
        print(f"  Index Size: {db_stats['indexSize'] / 1024 / 1024:.2f} MB")

        # 3. Collection sharding status
        print("\n3. COLLECTION SHARDING STATUS")
        print("-" * 60)

        coll_stats = db.command("collStats", "logs")
        print(f"Collection: logs")
        print(f"  Sharded: {coll_stats.get('sharded', False)}")

        if coll_stats.get("sharded"):
            print(f"  Shard Key: {coll_stats.get('shardKey', 'N/A')}")
            print(f"  Total Documents: {coll_stats.get('count', 0):,}")
            print(f"  Average Document Size: {coll_stats.get('avgObjSize', 0)} bytes")

            # 4. Distribution across shards
            print("\n4. DATA DISTRIBUTION BY SHARD")
            print("-" * 60)

            if "shards" in coll_stats:
                total_docs = coll_stats.get("count", 0)
                for shard_name, shard_data in coll_stats["shards"].items():
                    count = shard_data.get("count", 0)
                    size = shard_data.get("size", 0)
                    percentage = (count / total_docs * 100) if total_docs > 0 else 0

                    print(f"\n  {shard_name}:")
                    print(f"    Documents: {count:,} ({percentage:.2f}%)")
                    print(f"    Size: {size / 1024 / 1024:.2f} MB")
                    print(f"    Avg Doc Size: {shard_data.get('avgObjSize', 0)} bytes")
        else:
            print("  ⚠️  Collection is NOT sharded!")
            total_docs = db.logs.count_documents({})
            print(f"  Total Documents: {total_docs:,}")

        # 5. Chunk distribution
        print("\n5. CHUNK DISTRIBUTION")
        print("-" * 60)

        config_db = client["config"]
        chunks = list(config_db.chunks.find({"ns": "logs.logs"}))

        if chunks:
            chunk_dist = defaultdict(int)
            for chunk in chunks:
                chunk_dist[chunk["shard"]] += 1

            print(f"Total Chunks: {len(chunks)}")
            for shard, count in sorted(chunk_dist.items()):
                percentage = count / len(chunks) * 100
                print(f"  {shard}: {count} chunks ({percentage:.2f}%)")

            # Show chunk ranges
            print("\n6. CHUNK RANGES (First 10)")
            print("-" * 60)
            for i, chunk in enumerate(chunks[:10], 1):
                print(f"  Chunk {i}:")
                print(f"    Shard: {chunk['shard']}")
                print(f"    Range: {chunk['min']} -> {chunk['max']}")
        else:
            print("  No chunks found. Collection may not be sharded yet.")

        # 7. Connect to individual shards
        print("\n7. DIRECT SHARD VERIFICATION")
        print("-" * 60)

        shard_connections = [
            ("Shard 1 (shard1ReplSet)", SHARD1_URI),
            ("Shard 2 (shard2ReplSet)", SHARD2_URI),
        ]

        for shard_name, uri in shard_connections:
            try:
                shard_client = MongoClient(uri)
                shard_db = shard_client["logs"]
                count = shard_db.logs.count_documents({})
                print(f"\n  {shard_name}:")
                print(f"    URI: {uri}")
                print(f"    Documents: {count:,}")

                if count > 0:
                    sample_doc = shard_db.logs.find_one()
                    if sample_doc:
                        sample_doc.pop("_id", None)
                        print(f"    Sample: {json.dumps(sample_doc, indent=6)}")

                shard_client.close()
            except Exception as e:
                print(f"  ⚠️  Could not connect to {shard_name}: {e}")

        # 8. Balancer status
        print("\n8. BALANCER STATUS")
        print("-" * 60)

        balancer_status = admin_db.command("balancerStatus")
        print(f"  Mode: {balancer_status.get('mode', 'unknown')}")
        print(f"  Currently Running: {balancer_status.get('inBalancerRound', False)}")
        print(f"  Currently Enabled: {balancer_status.get('mode') != 'off'}")

        client.close()

        print("\n" + "=" * 60)
        print("Analysis Complete!")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nMake sure:")
        print("  1. MongoDB cluster is running (docker-compose up -d)")
        print("  2. pymongo is installed (pip install pymongo)")
        print("  3. Sharding is properly configured")


if __name__ == "__main__":
    analyze_cluster()
