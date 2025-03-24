
# Data Compaction Strategy for Pokemon Showdown Replay Analysis


## Overview

This document outlines a possible strategy for compacting processed Pokemon Showdown replay data as the dataset grows over time. The approach balances storage efficiency with query performance while maintaining the ability to process new data incrementally.


## The Small Files Problem

When using a timestamp-based directory structure with frequent processing runs, you'll eventually face the "small files problem":
- Each processing run creates a new directory with parquet files
- Reading across many small files is less efficient than reading fewer larger files
- Spark job scheduling has overhead per file
- File system metadata operations become more expensive


## Benefits of Compaction

1. **Improved Query Performance**: Fewer, larger files are more efficient for Spark to process
2. **Reduced Storage Overhead**: Parquet files have metadata overhead per file
3. **Simplified Management**: Easier to manage fewer directories
4. **Optimized File Sizes**: Repartitioning creates right-sized files for your cluster


## When to Consider Compaction

Consider implementing data compaction when:
1. You have more than 100 timestamp directories
2. Query performance begins to degrade (queries taking significantly longer)
3. Storage usage becomes inefficient (many small files with high metadata overhead)
4. You want to archive older data while maintaining access to it



## Compaction Implementation
The compaction process involves:
1. Reading all parquet files from multiple timestamp directories
2. Combining them into a single, optimized dataset
3. Writing the combined dataset to a new directory with proper partitioning
4. Optionally removing the original directories after successful compaction


```python
from datetime import datetime
import os
import shutil
from pyspark.sql import SparkSession

def compact_processed_data(spark, data_type="replay_ids", days_to_keep_separate=7):
    """
    Compact processed data files to improve query performance.
    
    Args:
        spark: Active SparkSession
        data_type: Type of data to compact ("replay_ids" or "replays")
        days_to_keep_separate: Number of recent days to exclude from compaction
    """
    base_path = f"../../data/processed/{data_type}/"
    
    # List all timestamp directories
    all_dirs = [d for d in os.listdir(base_path) if os.path.isdir(os.path.join(base_path, d))]
    all_dirs.sort()  # Sort chronologically
    
    # Keep recent days separate
    current_date = datetime.now().strftime("%Y-%m-%d")
    recent_dirs = [d for d in all_dirs if d.startswith(current_date) or 
                  any(d.startswith(datetime.now().replace(day=datetime.now().day-i).strftime("%Y-%m-%d")) 
                      for i in range(1, days_to_keep_separate+1))]
    
    # Directories to compact
    compact_dirs = [d for d in all_dirs if d not in recent_dirs]
    
    if not compact_dirs:
        print("No directories to compact")
        return
    
    print(f"Compacting {len(compact_dirs)} directories, keeping {len(recent_dirs)} recent directories separate")
    
    # Create compact timestamp
    compact_timestamp = datetime.now().strftime("%Y-%m-%d_compact")
    compact_path = os.path.join(base_path, compact_timestamp)
    
    # Read all data to compact
    compact_paths = [os.path.join(base_path, d) for d in compact_dirs]
    all_data = spark.read.parquet(*compact_paths)
    
    # For replay_ids, deduplicate to ensure we have unique IDs
    if data_type == "replay_ids":
        all_data = all_data.distinct()
    
    # Write as a single optimized set of files
    # Adjust partition count based on data size (rule of thumb: aim for ~128MB per partition)
    estimated_size_gb = all_data.count() * 100 / 1_000_000_000  # Rough estimate assuming 100 bytes per row
    partition_count = max(10, int(estimated_size_gb * 10))  # At least 10 partitions
    
    print(f"Writing compacted data with {partition_count} partitions")
    all_data.repartition(partition_count).write.mode("overwrite").parquet(compact_path)
    
    # Optionally remove old directories after successful compaction
    for old_dir in compact_dirs:
        old_path = os.path.join(base_path, old_dir)
        print(f"Removing old directory: {old_path}")
        shutil.rmtree(old_path)
    
    print(f"Compaction complete. Data available at {compact_path}")
```