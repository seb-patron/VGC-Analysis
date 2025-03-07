# Data Storage Options for VGC-Spark

This document outlines various free options for storing and sharing the Pokémon battle data collected by this project, along with instructions for setting up each option.

## Current Data Size
As of the last check, the data folder size is approximately 113MB, which is quite manageable for free hosting options.

## Option 1: Hugging Face Datasets

[Hugging Face](https://huggingface.co/) provides free hosting for datasets with excellent integration for machine learning projects.

### Features
- Free storage with generous limits
- Built-in versioning
- Simple API for downloading
- Community visibility (if public)
- Metadata and documentation support

### Setup Instructions

1. **Create an account** on [Hugging Face](https://huggingface.co/join)

2. **Install required packages**:
   ```bash
   pip install datasets huggingface_hub
   ```

3. **Login to Hugging Face**:
   ```bash
   huggingface-cli login
   ```

4. **Prepare and upload your dataset**:
   ```python
   from datasets import Dataset
   from huggingface_hub import HfApi
   import os, json, glob
   
   # Create a dataset from your files
   # Example for replays:
   replay_files = glob.glob("data/replays/**/*.json", recursive=True)
   replay_data = []
   
   for file_path in replay_files:
       with open(file_path, 'r') as f:
           try:
               data = json.load(f)
               # Add file path as metadata
               data['_file_path'] = os.path.relpath(file_path, 'data/replays')
               replay_data.append(data)
           except json.JSONDecodeError:
               print(f"Error reading {file_path}")
   
   # Create dataset
   dataset = Dataset.from_list(replay_data)
   
   # Push to hub
   dataset.push_to_hub("your-username/vgc-battle-data")
   ```

5. **Download the dataset in your project**:
   ```python
   from datasets import load_dataset
   
   dataset = load_dataset("your-username/vgc-battle-data")
   ```

### Integration with DVC

You can use Hugging Face as a DVC remote:

```bash
# Add Hugging Face dataset as a DVC dependency
dvc import-url https://huggingface.co/datasets/your-username/vgc-battle-data/resolve/main/data/dataset.arrow data/
```

## Option 2: Kaggle Datasets

[Kaggle](https://www.kaggle.com/) offers free dataset hosting with up to 20GB per dataset.

### Features
- Up to 20GB free storage per dataset
- Version control support
- Large ML community
- Integration with Kaggle notebooks

### Setup Instructions

1. **Create a Kaggle account** at [Kaggle](https://www.kaggle.com/account/login)

2. **Install Kaggle CLI**:
   ```bash
   pip install kaggle
   ```

3. **Set up API credentials**:
   - Go to your Kaggle account settings
   - Click on "Create New API Token"
   - Save the `kaggle.json` file to `~/.kaggle/kaggle.json`
   - Run `chmod 600 ~/.kaggle/kaggle.json` for security

4. **Create a dataset metadata file** (`dataset-metadata.json`):
   ```json
   {
     "title": "Pokemon VGC Battle Data",
     "id": "yourusername/pokemon-vgc-battle-data",
     "licenses": [{"name": "CC0-1.0"}]
   }
   ```

5. **Upload your dataset**:
   ```bash
   # Create a folder for the dataset
   mkdir -p kaggle_dataset/data
   
   # Copy your data
   cp -r data/* kaggle_dataset/data/
   
   # Move metadata file
   mv dataset-metadata.json kaggle_dataset/
   
   # Upload to Kaggle
   cd kaggle_dataset
   kaggle datasets create -p .
   ```

6. **Download the dataset in your project**:
   ```bash
   kaggle datasets download yourusername/pokemon-vgc-battle-data -p data/
   unzip data/pokemon-vgc-battle-data.zip -d data/
   ```

### Integration with DVC

```bash
# Add Kaggle dataset as a DVC dependency
dvc import-url kaggle://yourusername/pokemon-vgc-battle-data data/
```

## Option 3: Google Drive

Google Drive offers 15GB of free storage (shared with Gmail and Google Photos).

### Features
- 15GB free storage
- Easy sharing via links
- Familiar interface
- Direct DVC integration

### Setup Instructions

1. **Upload data to Google Drive**:
   - Create a folder in your Google Drive
   - Upload your data folder contents
   - Right-click the folder and select "Share" to get a shareable link

2. **Install required packages for DVC integration**:
   ```bash
   pip install dvc[gdrive]
   ```

3. **Configure DVC to use Google Drive**:
   ```bash
   # Initialize DVC if not already done
   dvc init
   
   # Add Google Drive as a remote
   dvc remote add -d gdrive gdrive://folder_id
   
   # Where folder_id is the ID from your Google Drive URL
   # (e.g., from https://drive.google.com/drive/folders/1aBcDeFgHiJkLmNoPqRsTuVwXyZ)
   # the ID would be 1aBcDeFgHiJkLmNoPqRsTuVwXyZ
   
   # Push data to Google Drive
   dvc push
   ```

4. **Download data in your project**:
   ```bash
   # Pull data from Google Drive
   dvc pull
   ```

## Option 4: GitHub Releases

For datasets under 2GB, GitHub Releases can be a simple solution.

### Features
- Uses your existing GitHub account
- Up to 2GB per file
- Version tracking through releases
- No additional service needed

### Setup Instructions

1. **Create a GitHub release**:
   ```bash
   # Compress your data
   tar -czvf vgc-data.tar.gz data/
   
   # Create a tag
   git tag v1.0.0-data
   
   # Push the tag
   git push origin v1.0.0-data
   ```

2. **Upload the data file**:
   - Go to your GitHub repository
   - Click on "Releases"
   - Click on the tag you just created
   - Click "Edit"
   - Drag and drop your compressed data file
   - Click "Update release"

3. **Download in your project**:
   ```bash
   # Download the release asset
   curl -L https://github.com/yourusername/VGC-Spark/releases/download/v1.0.0-data/vgc-data.tar.gz -o vgc-data.tar.gz
   
   # Extract
   tar -xzvf vgc-data.tar.gz
   ```

### Integration with DVC

```bash
# Add GitHub release as a DVC dependency
dvc import-url https://github.com/yourusername/VGC-Spark/releases/download/v1.0.0-data/vgc-data.tar.gz data/
```

## Option 5: Internet Archive

The [Internet Archive](https://archive.org/) offers free, unlimited storage for datasets.

### Features
- Free unlimited storage
- Permanent archiving
- Public good mission
- Supports various file formats

### Setup Instructions

1. **Create an Internet Archive account** at [archive.org](https://archive.org/account/signup)

2. **Install the Internet Archive CLI**:
   ```bash
   pip install internetarchive
   ```

3. **Configure your credentials**:
   ```bash
   ia configure
   ```

4. **Upload your dataset**:
   ```bash
   # Create a compressed archive
   tar -czvf vgc-data.tar.gz data/
   
   # Upload to Internet Archive
   ia upload pokemon-vgc-battle-data vgc-data.tar.gz --metadata="title:Pokemon VGC Battle Data" --metadata="creator:Your Name" --metadata="subject:pokemon;vgc;data"
   ```

5. **Download in your project**:
   ```bash
   # Download from Internet Archive
   ia download pokemon-vgc-battle-data
   
   # Extract
   tar -xzvf vgc-data.tar.gz
   ```

### Integration with DVC

```bash
# Add Internet Archive item as a DVC dependency
dvc import-url https://archive.org/download/pokemon-vgc-battle-data/vgc-data.tar.gz data/
```

## Comparison of Options

| Option | Free Storage | Version Control | Ease of Setup | ML Integration | DVC Compatible |
|--------|--------------|-----------------|---------------|----------------|----------------|
| Hugging Face | Generous | ✅ | Medium | Excellent | ✅ |
| Kaggle | 20GB | ✅ | Medium | Good | ✅ |
| Google Drive | 15GB | Limited | Easy | Limited | ✅ |
| GitHub Releases | 2GB/file | ✅ | Easy | Limited | ✅ |
| Internet Archive | Unlimited | Limited | Medium | Limited | ✅ |

## Recommended Approach

For the VGC-Spark project with its current data size (113MB), **Hugging Face Datasets** is recommended for:
- Free storage with room to grow
- Excellent ML ecosystem integration
- Good documentation and metadata support
- Simple API for data access

## Updating the Data

Regardless of which option you choose, you'll want to periodically update the hosted data with new battle replays and ladder rankings. Each service has its own method for updates:

- **Hugging Face**: Use `dataset.push_to_hub()` with the same repository name to update
- **Kaggle**: Use `kaggle datasets version -p . -m "Update message"`
- **Google Drive**: Simply replace files or use DVC to manage updates
- **GitHub Releases**: Create a new release with a new version tag
- **Internet Archive**: Upload a new version with the same identifier

## Integration with the Project

To integrate with the VGC-Spark project, add a script that can download the data from your chosen platform:

```python
# Example for src/python/download_data.py

import os
import argparse

parser = argparse.ArgumentParser(description='Download VGC battle data')
parser.add_argument('--source', choices=['huggingface', 'kaggle', 'gdrive', 'github', 'archive'], 
                    default='huggingface', help='Data source to use')
args = parser.parse_args()

# Create data directories if they don't exist
os.makedirs('data/replays', exist_ok=True)
os.makedirs('data/ladder', exist_ok=True)

if args.source == 'huggingface':
    from datasets import load_dataset
    print("Downloading data from Hugging Face...")
    dataset = load_dataset("your-username/vgc-battle-data")
    # Process and save the dataset to the appropriate structure
    
elif args.source == 'kaggle':
    import subprocess
    print("Downloading data from Kaggle...")
    subprocess.run(['kaggle', 'datasets', 'download', 'yourusername/pokemon-vgc-battle-data', '-p', 'data/'])
    subprocess.run(['unzip', 'data/pokemon-vgc-battle-data.zip', '-d', 'data/'])
    
# Add other sources as needed...

print("Data download complete!")
```

Then update your README.md to include instructions for downloading the data. 