#!/usr/bin/env python3
"""
Download Pokemon Showdown ladder rankings.
This script can be run directly or imported and called from a notebook.
"""

import os, json, requests
import argparse
from datetime import datetime
from typing import List, Dict, Any, Optional

# Directory where data will be stored
# Get the absolute path to the project root directory
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
BASE_DIR = os.path.join(PROJECT_ROOT, "data")
REPLAYS_DIR = os.path.join(BASE_DIR, "replays")
LADDER_DIR = os.path.join(BASE_DIR, "ladder")

# Default formats to fetch ladder data for
DEFAULT_FORMATS = [
    "gen9ou", 
    "gen9vgc2024regh",        # Current active VGC format (Regulation H)
    "gen9vgc2025regg",        # Current active VGC format (Regulation G)
    "gen9randombattle"
]

def setup_directories() -> None:
    """Create necessary directories if they don't exist."""
    os.makedirs(REPLAYS_DIR, exist_ok=True)
    os.makedirs(LADDER_DIR, exist_ok=True)

def fetch_ladder_data(format_id: str) -> Optional[Dict[str, Any]]:
    """
    Fetch ladder data for a specific format.
    
    Args:
        format_id: The format ID to fetch ladder data for (e.g., 'gen9vgc2024regh')
        
    Returns:
        The ladder data as a dictionary, or None if the fetch failed
    """
    url = f"https://pokemonshowdown.com/ladder/{format_id}.json"
    print(f"Attempting to fetch ladder data for {format_id} from {url}...")
    
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        
        # Check if the response contains actual ladder data
        data = resp.json()
        if isinstance(data, dict) and "toplist" in data and len(data["toplist"]) > 0:
            print(f"Found {len(data['toplist'])} players on the ladder for {format_id}")
            return data
        else:
            print(f"Ladder for {format_id} exists but has no players")
            return None
    except Exception as e:
        print(f"Failed to get ladder for {format_id}: {e}")
        return None

def save_ladder_data(format_id: str, data: bytes, date_str: Optional[str] = None) -> str:
    """
    Save ladder data to a file.
    
    Args:
        format_id: The format ID the ladder data is for
        data: The raw ladder data as bytes
        date_str: Optional date string in YYYY-MM-DD format (defaults to today)
        
    Returns:
        The path to the saved file
    """
    if date_str is None:
        date_str = datetime.utcnow().strftime("%Y-%m-%d")
    
    ladder_day_dir = os.path.join(LADDER_DIR, date_str)
    os.makedirs(ladder_day_dir, exist_ok=True)
    
    ladder_file = os.path.join(ladder_day_dir, f"ladder_{format_id}.json")
    with open(ladder_file, "wb") as f:
        f.write(data)
    
    print(f"Saved ladder data for {format_id} to {ladder_file}")
    return ladder_file

def extract_ladder_rankings(formats: List[str] = DEFAULT_FORMATS, date_str: Optional[str] = None) -> Dict[str, int]:
    """
    Extract ladder rankings for the specified formats.
    
    Args:
        formats: List of format IDs to extract ladder rankings for
        date_str: Optional date string in YYYY-MM-DD format (defaults to today)
        
    Returns:
        Dictionary with statistics about the extraction
    """
    # Setup
    setup_directories()
    
    if date_str is None:
        date_str = datetime.utcnow().strftime("%Y-%m-%d")
    
    stats = {"formats_processed": 0, "ladders_downloaded": 0, "errors": 0}
    
    for fmt in formats:
        stats["formats_processed"] += 1
        
        try:
            resp = requests.get(f"https://pokemonshowdown.com/ladder/{fmt}.json", timeout=10)
            resp.raise_for_status()
            
            # Check if the response contains actual ladder data
            data = resp.json()
            if isinstance(data, dict) and "toplist" in data and len(data["toplist"]) > 0:
                print(f"Found {len(data['toplist'])} players on the ladder for {fmt}")
                
                # Save ladder JSON to file
                save_ladder_data(fmt, resp.content, date_str)
                stats["ladders_downloaded"] += 1
            else:
                print(f"Ladder for {fmt} exists but has no players")
                stats["errors"] += 1
        except Exception as e:
            print(f"Failed to get ladder for {fmt}: {e}")
            stats["errors"] += 1
    
    return stats

def main():
    """Main function to run when script is executed directly."""
    parser = argparse.ArgumentParser(description='Download Pokemon Showdown ladder rankings')
    parser.add_argument('--formats', nargs='+', default=DEFAULT_FORMATS,
                        help=f'List of formats to download ladder rankings for. Default: {DEFAULT_FORMATS}')
    parser.add_argument('--date', type=str, default=None,
                        help='Date to use for the ladder rankings (YYYY-MM-DD format). Defaults to today.')
    args = parser.parse_args()
    
    stats = extract_ladder_rankings(formats=args.formats, date_str=args.date)
    
    print("\nExtraction complete!")
    print(f"Formats processed: {stats['formats_processed']}")
    print(f"Ladders downloaded: {stats['ladders_downloaded']}")
    print(f"Errors encountered: {stats['errors']}")
    
    return 0

if __name__ == "__main__":
    main()