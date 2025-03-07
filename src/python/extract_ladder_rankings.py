import os, json, requests
from datetime import datetime

# Directory where data will be stored
# Get the absolute path to the project root directory
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
BASE_DIR = os.path.join(PROJECT_ROOT, "data")
REPLAYS_DIR = os.path.join(BASE_DIR, "replays")
LADDER_DIR = os.path.join(BASE_DIR, "ladder")


# Function to get ladder data
formats_to_get = [
    "gen9ou", 
    "gen9vgc2024regh",        # Current active VGC format (Regulation H)
    "gen9vgc2025regg",     # Current active VGC format (Regulation H, Best of 3)
    "gen9vgc2024regulationg", # Previous VGC format
    "gen9vgc2025regulationg", # Previous VGC format
    "gen9randombattle"
]

today = datetime.utcnow().strftime("%Y-%m-%d")
ladder_day_dir = os.path.join(LADDER_DIR, today)
os.makedirs(ladder_day_dir, exist_ok=True)

for fmt in formats_to_get:
    print(f"Attempting to fetch ladder data for {fmt}...")
    url = f"https://pokemonshowdown.com/ladder/{fmt}.json"
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        # Check if the response contains actual ladder data
        data = resp.json()
        if isinstance(data, dict) and "toplist" in data and len(data["toplist"]) > 0:
            print(f"Found {len(data['toplist'])} players on the ladder for {fmt}")
        else:
            print(f"Ladder for {fmt} exists but has no players")
    except Exception as e:
        print(f"Failed to get ladder for {fmt}: {e}")
        continue
    # Save ladder JSON to file
    ladder_file = os.path.join(ladder_day_dir, f"ladder_{fmt}.json")
    with open(ladder_file, "wb") as f:
        f.write(resp.content)
    print(f"Saved ladder data for {fmt}")