import os
import json
import pandas as pd
from pathlib import Path
from datetime import datetime
import time

def consolidate_json_files(input_dir, output_dir, chunk_size=None):
    """
    Consolidate many small JSON files into fewer, larger parquet files.
    
    Args:
        input_dir: Directory containing JSON files to consolidate
        output_dir: Directory to save consolidated parquet files
        chunk_size: Optional number of files to process in each chunk (None = all)
    """
    start_time = time.time()
    print(f"Starting consolidation at: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start_time))}")
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Process data by day
    day_dirs = [d for d in os.listdir(input_dir) if os.path.isdir(os.path.join(input_dir, d))]
    print(f"Found {len(day_dirs)} day directories to process")
    
    # Track stats
    total_files_processed = 0
    total_days_processed = 0
    
    for day_dir in day_dirs:
        day_path = os.path.join(input_dir, day_dir)
        print(f"Processing {day_dir}...")
        
        # Get all JSON files in the directory
        json_files = [f for f in os.listdir(day_path) if f.endswith('.json')]
        if not json_files:
            print(f"  No JSON files found in {day_dir}, skipping")
            continue
            
        print(f"  Found {len(json_files)} JSON files")
        
        # Process files in chunks if specified
        if chunk_size:
            chunks = [json_files[i:i + chunk_size] for i in range(0, len(json_files), chunk_size)]
            print(f"  Processing in {len(chunks)} chunks of {chunk_size} files")
        else:
            chunks = [json_files]
        
        for chunk_idx, files_chunk in enumerate(chunks):
            # Gather all JSON data
            all_data = []
            for file_name in files_chunk:
                file_path = os.path.join(day_path, file_name)
                try:
                    with open(file_path, 'r') as f:
                        all_data.append(json.load(f))
                except json.JSONDecodeError:
                    print(f"  Error decoding JSON in file: {file_path}, skipping")
                except Exception as e:
                    print(f"  Error reading file {file_path}: {str(e)}, skipping")
            
            if not all_data:
                print(f"  No valid data in chunk {chunk_idx+1}, skipping")
                continue
                
            # Convert to pandas DataFrame
            df = pd.DataFrame(all_data)
            
            # Define output filename, adding chunk suffix if processing in chunks
            if len(chunks) > 1:
                output_file = os.path.join(output_dir, f"{day_dir}_chunk{chunk_idx+1}.parquet")
            else:
                output_file = os.path.join(output_dir, f"{day_dir}.parquet")
            
            # Save as parquet file
            df.to_parquet(output_file)
            print(f"  Saved {len(all_data)} records to {output_file}")
            
            total_files_processed += len(files_chunk)
        
        total_days_processed += 1
    
    end_time = time.time()
    duration = end_time - start_time
    print(f"Consolidation complete!")
    print(f"Processed {total_files_processed} files across {total_days_processed} days")
    print(f"Total time: {duration:.2f} seconds ({duration/60:.2f} minutes)")

if __name__ == "__main__":
    # Define paths
    input_directory = "data/replays/gen9vgc2025regg/raw"
    output_directory = "data/replays/gen9vgc2025regg/consolidated"
    
    # Run consolidation
    consolidate_json_files(input_directory, output_directory) 