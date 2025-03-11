# Tableau-Backup-Tool
[![Visual Studio Code](https://custom-icon-badges.demolab.com/badge/Visual%20Studio%20Code-0078d7.svg?logo=vsc&logoColor=white)](#)
[![Python](https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=fff)](#)
![Git](https://img.shields.io/badge/git-%23F05033.svg?style=for-the-badge&logo=git&logoColor=white)
![Tableau](https://img.shields.io/badge/Tableau-Data%20Visualization-E97627?logo=tableau&logoColor=white)
[![Markdown](https://img.shields.io/badge/Markdown-%23000000.svg?logo=markdown&logoColor=white)](#)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

An automated tool for backing up Tableau workbooks and datasources to Git, featuring parallel processing, progress tracking, and smart file handling.

## Features
- **Automated Backup**: Automatically downloads and backs up all Tableau workbooks and datasources
- **Git Integration**: Seamlessly integrates with Git for version control
- **Parallel Processing**: Uses multi-threading for faster downloads
- **Smart File Handling**: Checks file hashes to avoid unnecessary downloads
- **Progress Tracking**: Visual progress bars for all operations
- **Configurable**: Flexible configuration through YAML and environment variables
- **Cross-Platform**: Works on Windows, Linux, and macOS
- **Detailed Logging**: Comprehensive logging system for monitoring and debugging

## Prerequisites
- Python 3.7+
- Git
- Tableau Server access
- Git repository for backups

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/tableau-backup-tool
cd tableau-backup-tool
```

2. Install required packages:
```bash
pip install -r requirements.txt
```

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
TABLEAU_USERNAME=your_username
TABLEAU_PASSWORD=your_password
TABLEAU_SERVER=your_server_url
GIT_REPO=your_repo_url
GIT_AUTHOR_NAME=your_name
GIT_AUTHOR_EMAIL=your_email
```

### Configuration File

The tool uses a `config.yaml` file for settings. A default one will be created if not present:

```yaml
tableau_server: https://tableau.server.com
git_repo: https://git.user.com/projects/test_proj
base_dir: Tableau_Projects
git_author:
  name: User
  email: user@outlook.com
max_workers: 4
overwrite_existing: false
```

## Usage

Run the backup tool:

```bash
python script.py --config config.yaml
```

### Command Line Arguments

- `--config`: Path to configuration file (default: config.yaml)

## Project Structure

```
tableau-backup-tool/
├── tableau-backup.py     # Main script
├── config.yaml           # Configuration file
├── requirements.txt      # Python dependencies
└── README.md             # This file
```

## How It Works

1. **Authentication**: Connects to Tableau Server using provided credentials
2. **Project Discovery**: Maps the project hierarchy and content
3. **Parallel Download**: Downloads workbooks and datasources using multiple threads
4. **Git Integration**: Commits and pushes changes to the specified repository
5. **Cleanup**: Performs necessary cleanup operations

## Features in Detail

### Parallel Processing
- Uses ThreadPoolExecutor for concurrent downloads
- Configurable number of worker threads
- Progress tracking for parallel operations

### Smart File Handling
- MD5 hash checking for change detection
- Skip unchanged files
- Optional file overwrite control

### Logging System
- Detailed logging to both file and console
- Different log levels for various operations
- Timestamp and category information

### Error Handling
- Comprehensive error catching and reporting
- Graceful failure handling
- Automatic cleanup on failure

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## Dependencies

```
tableauserverclient
gitpython
pyyaml
python-dotenv
tqdm
pathlib
```

## Error Codes

Common error codes and their meanings:

- `E001`: Authentication failure
- `E002`: Download permission denied
- `E003`: Git repository error
- `E004`: Configuration error
- `E005`: Network connection error

## Troubleshooting

### Common Issues

1. **Authentication Failures**
   - Verify credentials in `.env` file
   - Check Tableau Server URL
   - Ensure proper permissions

2. **Git Issues**
   - Verify Git repository access
   - Check Git credentials
   - Ensure proper repository structure

3. **Download Failures**
   - Check network connection
   - Verify content permissions
   - Ensure sufficient disk space

## License

Distributed under the MIT License. See `LICENSE` for more information.


## Credits
- Tableau Server Client library
- GitPython contributors
- TQDM progress bar library

<div align="right">

[Back To Top ⬆️](#Tableau-Backup-Tool)
</div>
