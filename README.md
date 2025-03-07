# Spark Project for VGC Data Analysis

This repository provides a framework for analyzing Pokémon VGC (Video Game Championship) battle data using Apache Spark. It includes scripts to download battle replays and ladder rankings from the Pokémon Showdown website.

## Project Structure

```
VGC-Spark/
├── data/                  # Data directory (not tracked by git)
│   ├── replays/           # Downloaded battle replays
│   └── ladder/            # Ladder rankings data
├── docs/                  # Documentation
│   └── data_storage_options.md  # Detailed info on data storage options
├── src/                   # Source code
│   └── python/            # Python scripts
│       ├── extract_replays.py        # Script to download battle replays
│       ├── extract_ladder_rankings.py # Script to download ladder rankings
│       └── download_data.py          # Script to download data from various sources
├── Dockerfile             # Docker configuration
├── start-spark-notebook.sh # Script to start Jupyter notebook with Spark
└── README.md              # Project documentation
```

## Getting Started

### Running the Jupyter Notebook Environment

Run the following command to start the Jupyter notebook server:

```bash
./start-spark-notebook.sh
```

The script will prompt you to choose between:

1. **Use jupyter/all-spark-notebook** (simplest option, default)
2. **Build custom image** with both Spark and Scala pre-configured
3. **Use almondsh/almond** (for Scala focus)

### Downloading Battle Data

The project includes two scripts for downloading data:

1. **extract_ladder_rankings.py**: Downloads the current ladder rankings for specified formats
2. **extract_replays.py**: Downloads battle replays for specified formats

To download the latest battle replays:

```bash
python src/python/extract_replays.py
```

To download older battle replays (going back in time):

```bash
python src/python/extract_replays.py --direction older
```

## Data Management

The `data/` directory is not tracked by git due to its potentially large size. We provide several options for managing this data:

### Option 1: Using the Download Script

We've included a versatile script that can download data from various sources:

```bash
# Download using DVC (default)
python src/python/download_data.py

# Download from Hugging Face
python src/python/download_data.py --source huggingface --dataset username/vgc-battle-data

# Download from Kaggle
python src/python/download_data.py --source kaggle --dataset username/pokemon-vgc-battle-data

# Download from Google Drive
python src/python/download_data.py --source gdrive --folder-id your-folder-id

# Download from GitHub Releases
python src/python/download_data.py --source github --repo username/repo --tag v1.0.0-data --asset vgc-data.tar.gz

# Download from Internet Archive
python src/python/download_data.py --source archive --identifier pokemon-vgc-battle-data
```

### Option 2: Data Storage Solutions

We support several free data storage solutions:

1. **Hugging Face Datasets**: Excellent for ML projects with good versioning
2. **Kaggle Datasets**: Up to 20GB free storage with version control
3. **Google Drive**: 15GB free storage with easy sharing
4. **GitHub Releases**: For datasets under 2GB
5. **Internet Archive**: Free unlimited storage

For detailed setup instructions for each option, see [Data Storage Options](docs/data_storage_options.md).

### Option 3: Data Version Control (DVC)

DVC is recommended for tracking data alongside your code:

```bash
# Install DVC
pip install dvc

# Initialize DVC
dvc init

# Add data directory to DVC
dvc add data

# Configure remote storage (example with Google Drive)
dvc remote add -d myremote gdrive://folder_id

# Push data to remote
dvc push
```

To pull data on another machine:

```bash
# Clone the repository
git clone https://github.com/yourusername/VGC-Spark.git
cd VGC-Spark

# Install DVC
pip install dvc

# Pull data
dvc pull
```

## Formats

The scripts currently track the following Pokémon battle formats:

- `gen9ou`: Generation 9 OverUsed
- `gen9vgc2024regh`: VGC 2024 Regulation H
- `gen9vgc2025regg`: VGC 2025 Regulation G
- `gen9randombattle`: Generation 9 Random Battle

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request
