# Extract Replays Guide

This document explains the data flow and usage of the `extract_replays.py` script, which is used to download battle replays from the Pokémon Showdown website.

## Overview

The `extract_replays.py` script is designed to download battle replays from the Pokémon Showdown website for various battle formats. It can be run as a standalone script or imported and used in a Jupyter notebook.

## Data Flow

Here's a detailed explanation of how the data flows through the script:

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│                 │     │                 │     │                 │     │                 │
│  Load State     │────▶│  Fetch Pages    │────▶│ Download Replays│────▶│  Update State   │
│                 │     │                 │     │                 │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘     └─────────────────┘
```

### 1. Load State

The script first loads the current state from `state.json`, which contains:
- For "newer" direction: The most recent timestamp for each format
- For "older" direction: The oldest timestamp for each format

This state tracking allows the script to:
- Skip replays it has already downloaded
- Continue from where it left off if interrupted

### 2. Fetch Pages

For each specified format, the script:
1. Determines the reference timestamp based on the direction:
   - For "newer": Uses the most recent timestamp from state
   - For "older": Uses the oldest timestamp from state or finds it by scanning the replay files
2. Fetches pages of replay search results from the Pokémon Showdown API
3. For each page:
   - Extracts replay IDs and timestamps
   - Tracks the newest/oldest timestamp seen
   - Continues until it reaches already-seen replays or the end of available replays

### 3. Download Replays

After collecting replay IDs:
1. Groups replays by date for efficient directory creation
2. Creates format/date directory structure (e.g., `data/replays/gen9vgc2025regg/2023-12-25/`)
3. Downloads each replay JSON file
4. Tracks download statistics (successful downloads and errors)

### 4. Update State

Finally, the script updates the state:
- For "newer" direction: Updates the most recent timestamp
- For "older" direction: Updates the oldest timestamp, but only if replays were successfully downloaded
- Saves the updated state to `state.json`

### Safety Features

The script includes several safety features:
- Periodic state saving (every 10 pages) for "newer" direction
- Error handling with detailed logging
- Graceful handling of keyboard interrupts
- Maximum page limit to prevent infinite loops

## Directory Structure

Replays are organized in the following directory structure:

```
data/
└── replays/
    └── {format_id}/
        └── {date}/
            └── {replay_id}.json
```

For example:
```
data/
└── replays/
    └── gen9vgc2025regg/
        ├── 2023-12-25/
        │   ├── gen9vgc2025regg-1234567890.json
        │   └── ...
        └── 2023-12-26/
            ├── gen9vgc2025regg-1234567891.json
            └── ...
```

## State File Format

The `state.json` file has the following format:

```json
{
  "gen9vgc2025regg": 1672531200,  // Most recent timestamp for newer direction
  "gen9vgc2025regg_oldest": 1672444800,  // Oldest timestamp for older direction
  "gen9ou": 1672531200,
  "gen9ou_oldest": 1672444800,
  ...
}
```

## Using in a Notebook

You can import and use the script in a Jupyter notebook. Here's how:

```python
import sys
import os

# Add the src/python directory to the path
sys.path.append(os.path.join(os.getcwd(), 'src/python'))

# Import the extract_replays function
from extract_replays import extract_replays

# Download newer replays for specific formats
stats = extract_replays(
    formats=["gen9vgc2025regg", "gen9vgc2024regh"],
    direction="newer",
    max_pages=10
)

print(f"Downloaded {stats['replays_downloaded']} replays")
print(f"Encountered {stats['errors']} errors")

# Download older replays
older_stats = extract_replays(
    formats=["gen9vgc2025regg"],
    direction="older",
    max_pages=20
)

print(f"Downloaded {older_stats['replays_downloaded']} older replays")
```

### Example Notebook

Here's a more complete example notebook:

```python
# %% [markdown]
# # Pokémon Showdown Replay Downloader
# 
# This notebook demonstrates how to use the `extract_replays` function to download battle replays.

# %%
import sys
import os
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)

# Add the src/python directory to the path
sys.path.append(os.path.join(os.getcwd(), 'src/python'))

# Import the extract_replays function
from extract_replays import extract_replays, load_state

# %% [markdown]
# ## Check Current State
# 
# First, let's check what replays we already have:

# %%
state = load_state()
print("Current state:")
for key, value in state.items():
    if "_oldest" in key:
        print(f"  {key}: {value} ({datetime.fromtimestamp(value).strftime('%Y-%m-%d %H:%M:%S')})")
    else:
        print(f"  {key}: {value} ({datetime.fromtimestamp(value).strftime('%Y-%m-%d %H:%M:%S')})")

# %% [markdown]
# ## Download New Replays
# 
# Now let's download new replays for VGC formats:

# %%
vgc_formats = ["gen9vgc2025regg", "gen9vgc2024regh"]
stats = extract_replays(
    formats=vgc_formats,
    direction="newer",
    max_pages=5  # Limit to 5 pages for demonstration
)

print(f"Downloaded {stats['replays_downloaded']} new replays")

# %% [markdown]
# ## Download Older Replays
# 
# We can also download older replays:

# %%
older_stats = extract_replays(
    formats=["gen9vgc2025regg"],
    direction="older",
    max_pages=5  # Limit to 5 pages for demonstration
)

print(f"Downloaded {older_stats['replays_downloaded']} older replays")

# %% [markdown]
# ## Analyze the Data
# 
# Now we can start analyzing the downloaded replays...
```

## Command Line Usage

The script can also be run from the command line:

```bash
# Download newer replays for all default formats
python src/python/extract_replays.py

# Download older replays for a specific format
python src/python/extract_replays.py --direction older --formats gen9vgc2025regg

# Download newer replays with a limit of 10 pages
python src/python/extract_replays.py --max-pages 10

# Set a specific log level
python src/python/extract_replays.py --log-level DEBUG
```

## Troubleshooting

### Common Issues

1. **Network Errors**: If you encounter network errors, the script will log them and continue with the next replay. You can retry later.

2. **Keyboard Interrupts**: If you interrupt the script with Ctrl+C, it will attempt to save the state before exiting.

3. **Rate Limiting**: If you're downloading many replays, the Pokémon Showdown server might rate-limit your requests. The script includes timeouts to handle this.

### Logs

The script logs to both the console and a file named `extract_replays.log`. Check this file for detailed information about any errors.

## Advanced Usage

### Custom Formats

You can specify custom formats to download:

```python
custom_formats = ["gen9monotype", "gen9ubers", "gen9doublesou"]
stats = extract_replays(formats=custom_formats)
```

### Incremental Updates

For a production system, you might want to run the script periodically to get new replays:

```python
# In a scheduled job
from extract_replays import extract_replays

# Get newest replays for all formats
extract_replays(direction="newer")

# Also get some older replays to build historical data
extract_replays(direction="older", max_pages=5)
``` 