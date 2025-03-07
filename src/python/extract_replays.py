#!/usr/bin/env python3
"""
Download Pokemon Showdown replays.
This script can be run directly or imported and called from a notebook.
"""

import os, json, requests
import argparse
from datetime import datetime
from typing import List, Dict, Optional, Union, Any

# Directory where data will be stored
# Get the absolute path to the project root directory
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
BASE_DIR = os.path.join(PROJECT_ROOT, "data")
REPLAYS_DIR = os.path.join(BASE_DIR, "replays")
LADDER_DIR = os.path.join(BASE_DIR, "ladder")

# Default formats to scrape replays for
DEFAULT_FORMATS = [
    "gen9ou", 
    "gen9vgc2024regh",        # Current active VGC format (Regulation H)
    "gen9vgc2025regg",        # Current active VGC format (Regulation G)
    "gen9randombattle"
]

# Default maximum number of pages to fetch (safety to avoid infinite loop)
DEFAULT_MAX_PAGES = 55

def fetch_replay_page(format_id: str, before_ts: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Fetch a page of replay search results for a format, optionally with a 'before' timestamp.
    
    Args:
        format_id: The format ID to fetch replays for (e.g., 'gen9vgc2024regh')
        before_ts: Optional timestamp to get replays before this time
        
    Returns:
        List of replay data dictionaries
    """
    params = {"format": format_id}
    if before_ts:
        params["before"] = before_ts
    url = "https://replay.pokemonshowdown.com/search.json"
    print(f"Fetching replays from {url} with params {params}")
    resp = requests.get(url, params=params, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    print(f"Got response with {len(data) if isinstance(data, list) else 'non-list'} items")
    return data

def setup_directories() -> None:
    """Create necessary directories if they don't exist."""
    os.makedirs(REPLAYS_DIR, exist_ok=True)
    os.makedirs(LADDER_DIR, exist_ok=True)

def load_state() -> Dict[str, Any]:
    """Load or initialize state (last seen timestamps per format)."""
    state_path = os.path.join(PROJECT_ROOT, "state.json")
    if os.path.exists(state_path):
        with open(state_path, "r") as f:
            return json.load(f)
    return {}  # e.g., {"gen8ou": 1670000000, ...}

def save_state(state: Dict[str, Any]) -> None:
    """Save the state to disk."""
    state_path = os.path.join(PROJECT_ROOT, "state.json")
    with open(state_path, "w") as f:
        json.dump(state, f)

def find_oldest_timestamp(format_id: str) -> Optional[int]:
    """
    Find the oldest timestamp in a format's replays.
    
    First checks if the oldest timestamp is stored in state.json.
    If not found there, scans the replay directories to find it.
    
    Args:
        format_id: The format ID to search for (e.g., 'gen9vgc2024regh')
        
    Returns:
        The oldest timestamp found, or None if no replays exist
    """
    # First check if we have the oldest timestamp in state.json
    state = load_state()
    oldest_key = f"{format_id}_oldest"
    if oldest_key in state:
        print(f"Found oldest timestamp for {format_id} in state.json: {state[oldest_key]}")
        return state[oldest_key]
    
    # If not in state.json, scan directories
    print(f"No oldest timestamp found in state.json for {format_id}, scanning directories...")
    
    format_dir = os.path.join(REPLAYS_DIR, format_id)
    if not os.path.exists(format_dir):
        return None
    
    # First, find the oldest date folder
    date_dirs = []
    for date_dir in os.listdir(format_dir):
        date_path = os.path.join(format_dir, date_dir)
        if os.path.isdir(date_path):
            try:
                # Convert folder name to date object
                folder_date = datetime.strptime(date_dir, "%Y-%m-%d").date()
                date_dirs.append((folder_date, date_dir))
            except ValueError:
                # Skip folders that don't match the date format
                continue
    
    if not date_dirs:
        return None
    
    # Sort by date and get the oldest
    date_dirs.sort()  # Sort by date
    oldest_date_str = date_dirs[0][1]
    print(f"Oldest date folder for {format_id}: {oldest_date_str}")
    
    # Now check the replays in the oldest folder to find the oldest timestamp
    oldest_date_path = os.path.join(format_dir, oldest_date_str)
    oldest_ts = None
    
    # Check each replay file in the oldest folder
    for replay_file in os.listdir(oldest_date_path):
        if not replay_file.endswith('.json'):
            continue
        
        replay_path = os.path.join(oldest_date_path, replay_file)
        try:
            with open(replay_path, 'r') as f:
                replay_data = json.load(f)
                # Extract timestamp from replay data
                if 'uploadtime' in replay_data:
                    ts = replay_data['uploadtime']
                    if oldest_ts is None or ts < oldest_ts:
                        oldest_ts = ts
        except (json.JSONDecodeError, KeyError, FileNotFoundError):
            # Skip files with issues
            continue  
    
    return oldest_ts

def download_replay(replay_id: str, format_id: str, replay_date: str) -> bool:
    """
    Download a single replay and save it to disk.
    
    Args:
        replay_id: The ID of the replay to download
        format_id: The format ID of the replay
        replay_date: The date of the replay in YYYY-MM-DD format
        
    Returns:
        True if successful, False otherwise
    """
    # Create format/date directory structure
    format_dir = os.path.join(REPLAYS_DIR, format_id, replay_date)
    os.makedirs(format_dir, exist_ok=True)
    
    rep_url = f"https://replay.pokemonshowdown.com/{replay_id}.json"
    print(f"Downloading replay from {rep_url}")
    try:
        r = requests.get(rep_url, timeout=10)
        r.raise_for_status()
    except Exception as e:
        print(f"Error downloading replay {replay_id}: {e}")
        return False
    
    # Save replay JSON
    fname = os.path.join(format_dir, f"{replay_id}.json")
    with open(fname, "wb") as f:
        f.write(r.content)
    print(f"Saved replay to {fname}")
    return True

def extract_replays(formats: List[str] = DEFAULT_FORMATS, direction: str = 'newer', max_pages: int = DEFAULT_MAX_PAGES) -> Dict[str, int]:
    """
    Extract replays for the specified formats and direction.
    
    Args:
        formats: List of format IDs to extract replays for
        direction: 'newer' to get replays newer than last seen, 'older' to get replays older than oldest seen
        max_pages: Maximum number of pages to fetch per format (safety to avoid infinite loop)
        
    Returns:
        Dictionary with statistics about the extraction
    """
    # Setup
    setup_directories()
    state = load_state()
    today = datetime.utcnow().strftime("%Y-%m-%d")
    stats = {"formats_processed": 0, "replays_downloaded": 0, "errors": 0}
    
    for fmt in formats:
        print(f"Collecting {direction} replays for format: {fmt}")
        stats["formats_processed"] += 1
        
        if direction == 'newer':
            # Get newer replays (default behavior)
            reference_ts = state.get(fmt)  # timestamp of last fetched battle for this format
            new_reference_ts = reference_ts  # we will update this if we find newer
        else:
            # Get older replays
            # Find the oldest timestamp we have for this format
            reference_ts = find_oldest_timestamp(fmt)
            if reference_ts:
                print(f"Found oldest timestamp for {fmt}: {reference_ts} ({datetime.fromtimestamp(reference_ts).strftime('%Y-%m-%d %H:%M:%S')})")
            else:
                print(f"No existing replays found for {fmt}, will download newest replays first")
                # If no replays exist yet, default to getting newest replays
                direction = 'newer'
                reference_ts = None
            new_reference_ts = None  # For older direction, we'll track the oldest timestamp
        
        page = 0
        before_ts = reference_ts if direction == 'older' else None
        new_replay_ids = []
        replay_dates = {}  # Dictionary to store replay ID -> date mapping
        done = False

        while page < max_pages and not done:
            try:
                data = fetch_replay_page(fmt, before_ts)
                # API returns a list directly, not a dictionary with a 'replays' key
                replays = data if isinstance(data, list) else data.get("replays", [])
                print(f"Found {len(replays)} replays on page {page}")
                if not replays:
                    print("No replays found, breaking loop")
                    break  # no data, possibly no battles or end of list
                
                for rep in replays:
                    r_time = rep.get("uploadtime")
                    
                    # Store the date for this replay based on its timestamp
                    replay_date = datetime.fromtimestamp(r_time).strftime("%Y-%m-%d")
                    replay_dates[rep["id"]] = replay_date
                    
                    if direction == 'newer':
                        # For newer direction, stop when we reach already seen replays
                        if reference_ts and r_time <= reference_ts:
                            # We've reached or passed the last seen battle, stop here
                            done = True
                            break
                        # Track the max timestamp seen (which will be the first page's first item ideally)
                        if not new_reference_ts or r_time > new_reference_ts:
                            new_reference_ts = r_time
                    else:
                        # For older direction, we want to continue past the oldest timestamp
                        # but we need to track the new oldest timestamp
                        if not new_reference_ts or r_time < new_reference_ts:
                            new_reference_ts = r_time
                    
                    # This is a replay we need to fetch
                    new_replay_ids.append(rep["id"])
                    
                # Prepare for next page if needed
                if done or len(replays) < 51:  # 51 indicates more pages, if less, we are at end
                    break
                # Set 'before' to the uploadtime of the last replay in this page to get older ones
                before_ts = replays[-1]["uploadtime"]
                page += 1
            except Exception as e:
                print(f"Error fetching page {page} for {fmt}: {e}")
                stats["errors"] += 1
                break

        # Download each new replay JSON
        print(f"Found {len(new_replay_ids)} new replay IDs to download")
        for rid in new_replay_ids:
            # Get the date for this replay from our mapping
            replay_date = replay_dates.get(rid, today)  # Default to today if not found
            
            success = download_replay(rid, fmt, replay_date)
            if success:
                stats["replays_downloaded"] += 1
            else:
                stats["errors"] += 1
        
        # Update state
        if direction == 'newer' and new_reference_ts and (not reference_ts or new_reference_ts > reference_ts):
            state[fmt] = new_reference_ts
            print(f"Updated last_seen for {fmt} to {new_reference_ts}")
        elif direction == 'older' and new_reference_ts:
            # For older direction, we store the oldest timestamp in a different key
            oldest_key = f"{fmt}_oldest"
            state[oldest_key] = new_reference_ts
            print(f"Updated oldest timestamp for {fmt} to {new_reference_ts}")

    # Save updated state
    save_state(state)
    return stats

def main():
    """Main function to run when script is executed directly."""
    parser = argparse.ArgumentParser(description='Download Pokemon Showdown replays')
    parser.add_argument('--direction', choices=['newer', 'older'], default='newer',
                        help='Download direction: "newer" gets replays newer than last seen, "older" gets replays older than oldest seen')
    parser.add_argument('--formats', nargs='+', default=DEFAULT_FORMATS,
                        help=f'List of formats to download replays for. Default: {DEFAULT_FORMATS}')
    parser.add_argument('--max-pages', type=int, default=DEFAULT_MAX_PAGES,
                        help=f'Maximum number of pages to fetch per format. Default: {DEFAULT_MAX_PAGES}')
    args = parser.parse_args()
    
    stats = extract_replays(formats=args.formats, direction=args.direction, max_pages=args.max_pages)
    
    print("\nExtraction complete!")
    print(f"Formats processed: {stats['formats_processed']}")
    print(f"Replays downloaded: {stats['replays_downloaded']}")
    print(f"Errors encountered: {stats['errors']}")
    
    return 0

if __name__ == "__main__":
    main()






