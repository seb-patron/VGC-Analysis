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
