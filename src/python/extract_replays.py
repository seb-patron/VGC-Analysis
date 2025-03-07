import os, json, requests
import argparse
from datetime import datetime

# Parse command line arguments
parser = argparse.ArgumentParser(description='Download Pokemon Showdown replays')
parser.add_argument('--direction', choices=['newer', 'older'], default='newer',
                    help='Download direction: "newer" gets replays newer than last seen, "older" gets replays older than oldest seen')
args = parser.parse_args()

# Utility: fetch a page of replay search results for a format, optionally with a 'before' timestamp
def fetch_replay_page(format_id, before_ts=None):
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

# Directory where data will be stored
# Get the absolute path to the project root directory
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
BASE_DIR = os.path.join(PROJECT_ROOT, "data")
REPLAYS_DIR = os.path.join(BASE_DIR, "replays")
LADDER_DIR = os.path.join(BASE_DIR, "ladder")

# Get today's date in YYYY-MM-DD format
today = datetime.utcnow().strftime("%Y-%m-%d")

# Load or initialize state (last seen timestamps per format)
state_path = os.path.join(PROJECT_ROOT, "state.json")
if os.path.exists(state_path):
    with open(state_path, "r") as f:
        state = json.load(f)
else:
    state = {}  # e.g., {"gen8ou": 1670000000, ...}

# Create directories if they don't exist
os.makedirs(REPLAYS_DIR, exist_ok=True)
os.makedirs(LADDER_DIR, exist_ok=True)

# Specify which formats to scrape replays for
battle_formats = [
    "gen9ou", 
    "gen9vgc2024regh",        # Current active VGC format (Regulation H)
    "gen9vgc2025regg",     # Current active VGC format (Regulation G)
    "gen9randombattle"
]

# Function to find the oldest timestamp in a format's replays
def find_oldest_timestamp(format_id):
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

MAX_PAGES = 55  # safety to avoid infinite loop
for fmt in battle_formats:
    print(f"Collecting {'older' if args.direction == 'older' else 'newer'} replays for format: {fmt}")
    
    if args.direction == 'newer':
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
            args.direction = 'newer'
            reference_ts = None
        new_reference_ts = None  # For older direction, we'll track the oldest timestamp
    
    page = 0
    before_ts = reference_ts if args.direction == 'older' else None
    new_replay_ids = []
    replay_dates = {}  # Dictionary to store replay ID -> date mapping
    done = False

    while page < MAX_PAGES and not done:
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
            
            if args.direction == 'newer':
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

    # Download each new replay JSON
    print(f"Found {len(new_replay_ids)} new replay IDs to download")
    for rid in new_replay_ids:
        # Get the date for this replay from our mapping
        replay_date = replay_dates.get(rid, today)  # Default to today if not found
        
        # Create format/date directory structure
        format_dir = os.path.join(REPLAYS_DIR, fmt, replay_date)
        os.makedirs(format_dir, exist_ok=True)
        
        rep_url = f"https://replay.pokemonshowdown.com/{rid}.json"
        print(f"Downloading replay from {rep_url}")
        try:
            r = requests.get(rep_url, timeout=10)
            r.raise_for_status()
        except Exception as e:
            print(f"Error downloading replay {rid}: {e}")
            continue
        # Save replay JSON
        fname = os.path.join(format_dir, f"{rid}.json")
        with open(fname, "wb") as f:
            f.write(r.content)
        print(f"Saved replay to {fname}")
    
    # Update state
    if args.direction == 'newer' and new_reference_ts and (not reference_ts or new_reference_ts > reference_ts):
        state[fmt] = new_reference_ts
        print(f"Updated last_seen for {fmt} to {new_reference_ts}")
    elif args.direction == 'older' and new_reference_ts:
        # For older direction, we store the oldest timestamp in a different key
        oldest_key = f"{fmt}_oldest"
        state[oldest_key] = new_reference_ts
        print(f"Updated oldest timestamp for {fmt} to {new_reference_ts}")

# Save updated state
with open(state_path, "w") as f:
    json.dump(state, f)






