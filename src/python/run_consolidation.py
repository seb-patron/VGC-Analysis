import argparse
from consolidate_json_files import consolidate_json_files

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Consolidate Pokemon Showdown JSON replay files into parquet format')
    
    parser.add_argument('--input-dir', type=str, 
                        default='data/replays/gen9vgc2025regg/raw',
                        help='Directory containing the raw JSON files')
    
    parser.add_argument('--output-dir', type=str, 
                        default='data/replays/gen9vgc2025regg/consolidated',
                        help='Directory to save consolidated parquet files')
    
    parser.add_argument('--chunk-size', type=int, default=1000,
                        help='Number of files to process in each chunk (default: 1000)')
    
    args = parser.parse_args()
    
    print(f"Starting consolidation with chunk size: {args.chunk_size}")
    print(f"Input directory: {args.input_dir}")
    print(f"Output directory: {args.output_dir}")
    
    consolidate_json_files(
        args.input_dir,
        args.output_dir,
        args.chunk_size
    ) 