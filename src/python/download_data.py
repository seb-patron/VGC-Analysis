#!/usr/bin/env python3
"""
Download VGC battle data from various storage options.
This script provides a unified interface to download data from different sources.
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path

# Get the absolute path to the project root directory
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
BASE_DIR = os.path.join(PROJECT_ROOT, "data")
REPLAYS_DIR = os.path.join(BASE_DIR, "replays")
LADDER_DIR = os.path.join(BASE_DIR, "ladder")

def setup_directories():
    """Create necessary directories if they don't exist."""
    os.makedirs(REPLAYS_DIR, exist_ok=True)
    os.makedirs(LADDER_DIR, exist_ok=True)
    print(f"Data directories created at {BASE_DIR}")

def download_from_huggingface(dataset_name):
    """Download data from Hugging Face Datasets."""
    try:
        from datasets import load_dataset
        from huggingface_hub import hf_hub_download
    except ImportError:
        print("Error: Required packages not installed. Run: pip install datasets huggingface_hub")
        return False
    
    print(f"Downloading data from Hugging Face dataset: {dataset_name}")
    try:
        # Load the dataset
        dataset = load_dataset(dataset_name)
        
        # Process replay data
        if 'replays' in dataset:
            replay_data = dataset['replays']
            for item in replay_data:
                # Extract file path and data
                file_path = item.get('_file_path')
                if file_path:
                    # Ensure directory exists
                    full_path = os.path.join(REPLAYS_DIR, file_path)
                    os.makedirs(os.path.dirname(full_path), exist_ok=True)
                    
                    # Write data to file
                    with open(full_path, 'w') as f:
                        import json
                        # Remove metadata field before saving
                        data = {k: v for k, v in item.items() if not k.startswith('_')}
                        json.dump(data, f)
        
        # Process ladder data
        if 'ladder' in dataset:
            ladder_data = dataset['ladder']
            for item in ladder_data:
                # Extract file path and data
                file_path = item.get('_file_path')
                if file_path:
                    # Ensure directory exists
                    full_path = os.path.join(LADDER_DIR, file_path)
                    os.makedirs(os.path.dirname(full_path), exist_ok=True)
                    
                    # Write data to file
                    with open(full_path, 'w') as f:
                        import json
                        # Remove metadata field before saving
                        data = {k: v for k, v in item.items() if not k.startswith('_')}
                        json.dump(data, f)
        
        print("Data successfully downloaded from Hugging Face")
        return True
    except Exception as e:
        print(f"Error downloading from Hugging Face: {str(e)}")
        return False

def download_from_kaggle(dataset_name):
    """Download data from Kaggle Datasets."""
    try:
        # Check if kaggle CLI is installed
        subprocess.run(['kaggle', '--version'], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except (subprocess.SubprocessError, FileNotFoundError):
        print("Error: Kaggle CLI not installed or configured. Run: pip install kaggle")
        print("Then set up your API credentials as described in the documentation.")
        return False
    
    print(f"Downloading data from Kaggle dataset: {dataset_name}")
    try:
        # Download the dataset
        subprocess.run(['kaggle', 'datasets', 'download', dataset_name, '-p', BASE_DIR], check=True)
        
        # Extract the downloaded zip file
        zip_file = os.path.join(BASE_DIR, f"{dataset_name.split('/')[-1]}.zip")
        if os.path.exists(zip_file):
            import zipfile
            with zipfile.ZipFile(zip_file, 'r') as zip_ref:
                zip_ref.extractall(BASE_DIR)
            
            # Remove the zip file after extraction
            os.remove(zip_file)
            print("Data successfully downloaded and extracted from Kaggle")
            return True
        else:
            print(f"Error: Downloaded file not found at {zip_file}")
            return False
    except subprocess.SubprocessError as e:
        print(f"Error downloading from Kaggle: {str(e)}")
        return False

def download_from_gdrive(folder_id):
    """Download data from Google Drive."""
    try:
        # Check if gdown is installed
        subprocess.run(['pip', 'show', 'gdown'], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except subprocess.SubprocessError:
        print("Error: gdown not installed. Run: pip install gdown")
        return False
    
    print(f"Downloading data from Google Drive folder: {folder_id}")
    try:
        # Download the folder
        subprocess.run(['gdown', '--folder', '--id', folder_id, '-O', BASE_DIR], check=True)
        print("Data successfully downloaded from Google Drive")
        return True
    except subprocess.SubprocessError as e:
        print(f"Error downloading from Google Drive: {str(e)}")
        return False

def download_from_github(repo, tag, asset_name):
    """Download data from GitHub Releases."""
    import requests
    import tarfile
    
    print(f"Downloading data from GitHub release: {repo} {tag}")
    try:
        # Construct the URL for the release asset
        url = f"https://github.com/{repo}/releases/download/{tag}/{asset_name}"
        
        # Download the file
        response = requests.get(url, stream=True)
        if response.status_code == 200:
            download_path = os.path.join(BASE_DIR, asset_name)
            with open(download_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            # Extract if it's a compressed file
            if asset_name.endswith('.tar.gz') or asset_name.endswith('.tgz'):
                with tarfile.open(download_path) as tar:
                    tar.extractall(path=BASE_DIR)
                os.remove(download_path)
            
            print("Data successfully downloaded from GitHub")
            return True
        else:
            print(f"Error: Failed to download from GitHub. Status code: {response.status_code}")
            return False
    except Exception as e:
        print(f"Error downloading from GitHub: {str(e)}")
        return False

def download_from_archive(identifier):
    """Download data from Internet Archive."""
    try:
        # Check if internetarchive CLI is installed
        subprocess.run(['ia', '--version'], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except (subprocess.SubprocessError, FileNotFoundError):
        print("Error: internetarchive CLI not installed. Run: pip install internetarchive")
        return False
    
    print(f"Downloading data from Internet Archive: {identifier}")
    try:
        # Download the item
        subprocess.run(['ia', 'download', identifier], check=True, cwd=BASE_DIR)
        
        # Extract any compressed files
        archive_dir = os.path.join(BASE_DIR, identifier)
        if os.path.exists(archive_dir):
            for file in os.listdir(archive_dir):
                if file.endswith('.tar.gz') or file.endswith('.tgz'):
                    import tarfile
                    with tarfile.open(os.path.join(archive_dir, file)) as tar:
                        tar.extractall(path=BASE_DIR)
            
            print("Data successfully downloaded from Internet Archive")
            return True
        else:
            print(f"Error: Downloaded directory not found at {archive_dir}")
            return False
    except subprocess.SubprocessError as e:
        print(f"Error downloading from Internet Archive: {str(e)}")
        return False

def download_using_dvc():
    """Download data using DVC."""
    try:
        # Check if DVC is installed
        subprocess.run(['dvc', '--version'], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except (subprocess.SubprocessError, FileNotFoundError):
        print("Error: DVC not installed. Run: pip install dvc")
        return False
    
    print("Downloading data using DVC")
    try:
        # Pull data using DVC
        subprocess.run(['dvc', 'pull'], check=True, cwd=PROJECT_ROOT)
        print("Data successfully downloaded using DVC")
        return True
    except subprocess.SubprocessError as e:
        print(f"Error downloading using DVC: {str(e)}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Download VGC battle data from various sources')
    parser.add_argument('--source', choices=['huggingface', 'kaggle', 'gdrive', 'github', 'archive', 'dvc'], 
                        default='dvc', help='Data source to use')
    
    # Source-specific arguments
    parser.add_argument('--dataset', help='Dataset name for Hugging Face or Kaggle (e.g., "username/dataset-name")')
    parser.add_argument('--folder-id', help='Folder ID for Google Drive')
    parser.add_argument('--repo', help='Repository name for GitHub (e.g., "username/repo")')
    parser.add_argument('--tag', help='Release tag for GitHub')
    parser.add_argument('--asset', help='Asset name for GitHub release')
    parser.add_argument('--identifier', help='Item identifier for Internet Archive')
    
    args = parser.parse_args()
    
    # Create data directories
    setup_directories()
    
    # Download data from the specified source
    success = False
    if args.source == 'huggingface':
        if not args.dataset:
            print("Error: --dataset argument is required for Hugging Face source")
            return 1
        success = download_from_huggingface(args.dataset)
    
    elif args.source == 'kaggle':
        if not args.dataset:
            print("Error: --dataset argument is required for Kaggle source")
            return 1
        success = download_from_kaggle(args.dataset)
    
    elif args.source == 'gdrive':
        if not args.folder_id:
            print("Error: --folder-id argument is required for Google Drive source")
            return 1
        success = download_from_gdrive(args.folder_id)
    
    elif args.source == 'github':
        if not all([args.repo, args.tag, args.asset]):
            print("Error: --repo, --tag, and --asset arguments are required for GitHub source")
            return 1
        success = download_from_github(args.repo, args.tag, args.asset)
    
    elif args.source == 'archive':
        if not args.identifier:
            print("Error: --identifier argument is required for Internet Archive source")
            return 1
        success = download_from_archive(args.identifier)
    
    elif args.source == 'dvc':
        success = download_using_dvc()
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main()) 