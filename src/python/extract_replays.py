#!/usr/bin/env python3
"""
Download Pokemon Showdown replays.
This script can be run directly or imported and called from a notebook.
"""

import os, json, requests
import argparse
import logging
import traceback
import sys
from datetime import datetime
from typing import List, Dict, Optional, Union, Any

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('extract_replays.log')
    ]
)
logger = logging.getLogger('extract_replays')

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
    
    try:
        resp = requests.get(url, params=params, timeout=30)  # Increased timeout
        resp.raise_for_status()
        data = resp.json()
        return data
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error fetching replay page: {e}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error fetching replay page: {e}")
        raise

def setup_directories() -> None:
    """Create necessary directories if they don't exist."""
    os.makedirs(REPLAYS_DIR, exist_ok=True)
    os.makedirs(LADDER_DIR, exist_ok=True)

def load_state() -> Dict[str, Any]:
    """Load or initialize state (last seen timestamps per format)."""
    state_path = os.path.join(PROJECT_ROOT, "state.json")
    if os.path.exists(state_path):
        try:
            with open(state_path, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            logger.error(f"Error decoding state.json, creating new state")
            return {}
        except Exception as e:
            logger.error(f"Error loading state: {e}")
            return {}
    return {}  # e.g., {"gen8ou": 1670000000, ...}

def save_state(state: Dict[str, Any]) -> None:
    """Save the state to disk."""
    state_path = os.path.join(PROJECT_ROOT, "state.json")
    try:
        with open(state_path, "w") as f:
            json.dump(state, f)
        logger.debug(f"State saved successfully to {state_path}")
    except Exception as e:
        logger.error(f"Error saving state: {e}")
        logger.error(traceback.format_exc())

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
        logger.info(f"Found oldest timestamp for {format_id} in state.json: {state[oldest_key]}")
        return state[oldest_key]
    
    # If not in state.json, scan directories
    logger.info(f"No oldest timestamp found in state.json for {format_id}, scanning directories...")
    
    format_dir = os.path.join(REPLAYS_DIR, format_id)
    if not os.path.exists(format_dir):
        logger.info(f"No directory found for format {format_id}")
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
                logger.warning(f"Skipping directory with invalid date format: {date_dir}")
                continue
    
    if not date_dirs:
        logger.info(f"No date directories found for format {format_id}")
        return None
    
    # Sort by date and get the oldest
    date_dirs.sort()  # Sort by date
    oldest_date_str = date_dirs[0][1]
    logger.info(f"Oldest date folder for {format_id}: {oldest_date_str}")
    
    # Now check the replays in the oldest folder to find the oldest timestamp
    oldest_date_path = os.path.join(format_dir, oldest_date_str)
    oldest_ts = None
    
    # Check each replay file in the oldest folder
    replay_count = 0
    error_count = 0
    for replay_file in os.listdir(oldest_date_path):
        if not replay_file.endswith('.json'):
            continue
        
        replay_path = os.path.join(oldest_date_path, replay_file)
        try:
            with open(replay_path, 'r') as f:
                replay_data = json.load(f)
                replay_count += 1
                # Extract timestamp from replay data
                if 'uploadtime' in replay_data:
                    ts = replay_data['uploadtime']
                    if oldest_ts is None or ts < oldest_ts:
                        oldest_ts = ts
        except (json.JSONDecodeError, KeyError, FileNotFoundError) as e:
            # Skip files with issues
            error_count += 1
            logger.debug(f"Error reading replay file {replay_file}: {e}")
            continue  
    
    logger.info(f"Scanned {replay_count} replay files with {error_count} errors")
    if oldest_ts:
        logger.info(f"Found oldest timestamp: {oldest_ts} ({datetime.fromtimestamp(oldest_ts).strftime('%Y-%m-%d %H:%M:%S')})")
    else:
        logger.warning(f"No valid timestamps found in replay files")
    
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
    format_dir = os.path.join(REPLAYS_DIR, format_id, 'raw', replay_date)
    os.makedirs(format_dir, exist_ok=True)
    
    rep_url = f"https://replay.pokemonshowdown.com/{replay_id}.json"
    
    try:
        r = requests.get(rep_url, timeout=30)  # Increased timeout
        r.raise_for_status()
    except requests.exceptions.Timeout:
        logger.error(f"Timeout downloading replay {replay_id}")
        return False
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP error downloading replay {replay_id}: {e}")
        return False
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Connection error downloading replay {replay_id}: {e}")
        return False
    except requests.exceptions.RequestException as e:
        logger.error(f"Error downloading replay {replay_id}: {e}")
        return False
    
    # Save replay JSON
    fname = os.path.join(format_dir, f"{replay_id}.json")
    try:
        with open(fname, "wb") as f:
            f.write(r.content)
        return True
    except IOError as e:
        logger.error(f"Error saving replay {replay_id} to {fname}: {e}")
        return False

def batch_download_replays(replay_ids: List[str], format_id: str, replay_dates: Dict[str, str], today: str) -> Dict[str, int]:
    """
    Download a batch of replays and return statistics.
    
    Args:
        replay_ids: List of replay IDs to download
        format_id: The format ID of the replays
        replay_dates: Dictionary mapping replay IDs to dates
        today: Today's date string as fallback
        
    Returns:
        Dictionary with download statistics
    """
    stats = {"downloaded": 0, "errors": 0}
    
    if not replay_ids:
        return stats
    
    logger.info(f"Downloading {len(replay_ids)} replays for {format_id}")
    
    # Group by date for more efficient directory creation
    by_date = {}
    for rid in replay_ids:
        date = replay_dates.get(rid, today)
        if date not in by_date:
            by_date[date] = []
        by_date[date].append(rid)
    
    # Download replays by date
    for date, ids in by_date.items():
        # Create directory once per date
        # date_dir = os.path.join(REPLAYS_DIR, format_id, date)
        date_dir = os.path.join(REPLAYS_DIR, format_id, 'raw', date)
        os.makedirs(date_dir, exist_ok=True)
        
        # Log progress periodically
        log_interval = max(1, len(ids) // 10)  # Log approximately 10 times
        
        for i, rid in enumerate(ids):
            if i % log_interval == 0:
                logger.debug(f"Downloading replay {i+1}/{len(ids)} for {format_id} on {date}")
            
            success = download_replay(rid, format_id, date)
            if success:
                stats["downloaded"] += 1
            else:
                stats["errors"] += 1
    
    logger.info(f"Downloaded {stats['downloaded']} replays for {format_id} with {stats['errors']} errors")
    return stats

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
        logger.info(f"Collecting {direction} replays for format: {fmt}")
        stats["formats_processed"] += 1
        
        # Track state updates for this format
        format_state_updated = False
        new_reference_ts = None
        
        try:
            if direction == 'newer':
                # Get newer replays (default behavior)
                reference_ts = state.get(fmt)  # timestamp of last fetched battle for this format
                new_reference_ts = reference_ts  # we will update this if we find newer
                logger.info(f"Starting with reference timestamp: {reference_ts}")
            else:
                # Get older replays
                # Find the oldest timestamp we have for this format
                reference_ts = find_oldest_timestamp(fmt)
                if reference_ts:
                    logger.info(f"Found oldest timestamp for {fmt}: {reference_ts} ({datetime.fromtimestamp(reference_ts).strftime('%Y-%m-%d %H:%M:%S')})")
                else:
                    logger.info(f"No existing replays found for {fmt}, will download newest replays first")
                    # If no replays exist yet, default to getting newest replays
                    direction = 'newer'
                    reference_ts = None
                new_reference_ts = None  # For older direction, we'll track the oldest timestamp
            
            page = 0
            before_ts = reference_ts if direction == 'older' else None
            new_replay_ids = []
            replay_dates = {}  # Dictionary to store replay ID -> date mapping
            done = False
            total_replays_found = 0

            while page < max_pages and not done:
                try:
                    data = fetch_replay_page(fmt, before_ts)
                    # API returns a list directly, not a dictionary with a 'replays' key
                    replays = data if isinstance(data, list) else data.get("replays", [])
                    
                    # Only log every few pages to reduce verbosity
                    if page % 5 == 0 or len(replays) == 0:
                        logger.info(f"Page {page}: Found {len(replays)} replays for {fmt}")
                    
                    total_replays_found += len(replays)
                    
                    if not replays:
                        logger.info("No replays found, breaking loop")
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
                                logger.info(f"Reached already seen replay with timestamp {r_time}, stopping")
                                done = True
                                break
                            # Track the max timestamp seen (which will be the first page's first item ideally)
                            if not new_reference_ts or r_time > new_reference_ts:
                                new_reference_ts = r_time
                                format_state_updated = True
                        else:
                            # For older direction, we want to continue past the oldest timestamp
                            # but we need to track the new oldest timestamp
                            if not new_reference_ts or r_time < new_reference_ts:
                                new_reference_ts = r_time
                                format_state_updated = True
                        
                        # This is a replay we need to fetch
                        new_replay_ids.append(rep["id"])
                        
                    # Prepare for next page if needed
                    if done or len(replays) < 51:  # 51 indicates more pages, if less, we are at end
                        logger.info(f"Reached end of available replays (got {len(replays)} < 51)")
                        break
                    # Set 'before' to the uploadtime of the last replay in this page to get older ones
                    before_ts = replays[-1]["uploadtime"]
                    page += 1
                    
                    # Save state periodically (every 10 pages)
                    if page % 10 == 0 and format_state_updated and page > 0:
                        # We only save the state for replays we've already processed
                        # We don't want to update timestamps until we've successfully downloaded the replays
                        # This is a temporary save - the final state will be updated after downloading
                        logger.info(f"Saving intermediate state after page {page}")
                        
                        # For both directions, we should be careful about updating state during fetching
                        # We'll only do this for emergency situations like keyboard interrupts
                        # The proper state update happens after successful downloads
                        
                        # We don't save state here during normal operation - we'll save it after downloading
                        
                except KeyboardInterrupt:
                    logger.warning("Keyboard interrupt detected, saving state and exiting")
                    # Update state before exiting
                    if format_state_updated:
                        update_state_for_format(state, fmt, direction, new_reference_ts)
                        save_state(state)
                    raise
                except Exception as e:
                    logger.error(f"Error fetching page {page} for {fmt}: {e}")
                    logger.error(traceback.format_exc())
                    stats["errors"] += 1
                    break

            # Log summary of what we found
            logger.info(f"Found {len(new_replay_ids)} new replays to download from {total_replays_found} total replays across {page+1} pages")
            
            # Download replays in batches
            download_stats = batch_download_replays(new_replay_ids, fmt, replay_dates, today)
            stats["replays_downloaded"] += download_stats["downloaded"]
            stats["errors"] += download_stats["errors"]
            
            # Update state only after successful downloads
            if format_state_updated:
                # For 'older' direction, only update if we actually downloaded some replays
                if direction == 'older':
                    if download_stats["downloaded"] > 0:
                        logger.info(f"Updating oldest timestamp for {fmt} after successful downloads")
                        update_state_for_format(state, fmt, direction, new_reference_ts)
                    else:
                        logger.warning(f"No replays downloaded for {fmt}, not updating oldest timestamp")
                else:
                    # For 'newer' direction, always update
                    update_state_for_format(state, fmt, direction, new_reference_ts)
        
        except KeyboardInterrupt:
            logger.warning(f"Keyboard interrupt detected while processing format {fmt}")
            # Make sure we save state before exiting
            if format_state_updated:
                update_state_for_format(state, fmt, direction, new_reference_ts)
                save_state(state)
            raise
        except Exception as e:
            logger.error(f"Unexpected error processing format {fmt}: {e}")
            logger.error(traceback.format_exc())
            stats["errors"] += 1
            # Still try to save state if we have updates
            if format_state_updated:
                update_state_for_format(state, fmt, direction, new_reference_ts)

    # Save updated state
    save_state(state)
    return stats

def update_state_for_format(state: Dict[str, Any], format_id: str, direction: str, new_reference_ts: Optional[int]) -> None:
    """
    Update the state dictionary for a specific format.
    
    Args:
        state: The state dictionary to update
        format_id: The format ID to update
        direction: 'newer' or 'older'
        new_reference_ts: The new timestamp to save
    """
    if not new_reference_ts:
        return
        
    if direction == 'newer' and (format_id not in state or new_reference_ts > state.get(format_id, 0)):
        state[format_id] = new_reference_ts
        logger.info(f"Updated last_seen for {format_id} to {new_reference_ts} ({datetime.fromtimestamp(new_reference_ts).strftime('%Y-%m-%d %H:%M:%S')})")
    elif direction == 'older':
        # For older direction, we store the oldest timestamp in a different key
        oldest_key = f"{format_id}_oldest"
        if oldest_key not in state or new_reference_ts < state.get(oldest_key, float('inf')):
            state[oldest_key] = new_reference_ts
            logger.info(f"Updated oldest timestamp for {format_id} to {new_reference_ts} ({datetime.fromtimestamp(new_reference_ts).strftime('%Y-%m-%d %H:%M:%S')})")

def main():
    """Main function to run when script is executed directly."""
    parser = argparse.ArgumentParser(description='Download Pokemon Showdown replays')
    parser.add_argument('--direction', choices=['newer', 'older'], default='newer',
                        help='Download direction: "newer" gets replays newer than last seen, "older" gets replays older than oldest seen')
    parser.add_argument('--formats', nargs='+', default=DEFAULT_FORMATS,
                        help=f'List of formats to download replays for. Default: {DEFAULT_FORMATS}')
    parser.add_argument('--max-pages', type=int, default=DEFAULT_MAX_PAGES,
                        help=f'Maximum number of pages to fetch per format. Default: {DEFAULT_MAX_PAGES}')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'], 
                        default='INFO', help='Set the logging level')
    args = parser.parse_args()
    
    # Set log level
    logger.setLevel(getattr(logging, args.log_level))
    
    try:
        logger.info(f"Starting replay extraction with direction={args.direction}, formats={args.formats}, max_pages={args.max_pages}")
        stats = extract_replays(formats=args.formats, direction=args.direction, max_pages=args.max_pages)
        
        logger.info("\nExtraction complete!")
        logger.info(f"Formats processed: {stats['formats_processed']}")
        logger.info(f"Replays downloaded: {stats['replays_downloaded']}")
        logger.info(f"Errors encountered: {stats['errors']}")
        
        return 0
    except KeyboardInterrupt:
        logger.warning("Extraction interrupted by user")
        return 1
    except Exception as e:
        logger.critical(f"Fatal error: {e}")
        logger.critical(traceback.format_exc())
        return 1

if __name__ == "__main__":
    sys.exit(main())






