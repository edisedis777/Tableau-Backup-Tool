import tableauserverclient as TSC
from tableauserverclient import ServerResponseError
from collections import defaultdict
import os
from pathlib import Path
import git
from git import Actor
import shutil
import stat
import argparse
from datetime import datetime
import logging
import yaml
from typing import Dict, List, Tuple, Optional
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from dotenv import load_dotenv
import hashlib
from functools import lru_cache

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('tableau_backup.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

class TableauBackup:
    def __init__(self, config_path: str = 'config.yaml'):
        """Initialize TableauBackup with configuration."""
        self.config = self._load_config(config_path)
        self.server = None
        self.project_cache = {}  # Cache for project lookups
        self.max_workers = self.config.get('max_workers', 4)
        
    def _load_config(self, config_path: str) -> dict:
        """Load configuration from YAML file."""
        try:
            with open(config_path) as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            default_config = {
                'tableau_server': os.getenv('TABLEAU_SERVER', 'https://tableau.server.com'),
                'git_repo': os.getenv('GIT_REPO', 'https://git.user.com/projects/test_proj'),
                'base_dir': 'Tableau_Projects',
                'git_author': {
                    'name': os.getenv('GIT_AUTHOR_NAME', 'User'),
                    'email': os.getenv('GIT_AUTHOR_EMAIL', 'user@outlook.com')
                },
                'max_workers': 4,
                'overwrite_existing': False
            }
            Path(config_path).parent.mkdir(parents=True, exist_ok=True)
            with open(config_path, 'w') as f:
                yaml.dump(default_config, f)
            return default_config

    @lru_cache(maxsize=1024)
    def lookup_parent(self, parent_id: str) -> Dict:
        """Find parent project using cached dictionary lookup."""
        return self.project_cache.get(parent_id, {})

    def calculate_file_hash(self, filepath: str) -> str:
        """Calculate MD5 hash of file for change detection."""
        if not Path(filepath).exists():
            return ""
        with open(filepath, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()

    def should_download_file(self, filepath: str, content_id: str) -> bool:
        """Determine if file should be downloaded based on config and existing content."""
        if not self.config.get('overwrite_existing', False) and Path(filepath).exists():
            return False
        return True

    async def download_workbook(self, directory: str, workbook_id: str, workbook_name: str, username: str) -> bool:
        """Download Tableau workbook with error handling and hash checking."""
        filepath = Path(directory) / f"{workbook_name}.twbx"
        
        if not self.should_download_file(str(filepath), workbook_id):
            logging.info(f"Skipping existing workbook: {workbook_name}")
            return False

        try:
            original_hash = self.calculate_file_hash(str(filepath))
            self.server.workbooks.download(workbook_id, filepath=str(filepath))
            new_hash = self.calculate_file_hash(str(filepath))
            
            if original_hash != new_hash:
                logging.info(f"Downloaded workbook: {workbook_name}")
                return True
            return False
            
        except ServerResponseError as e:
            logging.warning(f"Access denied: {username} cannot download {workbook_name}: {e}")
        except Exception as e:
            logging.error(f"Failed to download workbook {workbook_name}: {e}")
        return False

    async def download_datasource(self, directory: str, datasource_id: str, datasource_name: str, username: str) -> bool:
        """Download Tableau datasource with error handling and hash checking."""
        filepath = Path(directory) / f"{datasource_name}.tdsx"
        
        if not self.should_download_file(str(filepath), datasource_id):
            logging.info(f"Skipping existing datasource: {datasource_name}")
            return False

        try:
            original_hash = self.calculate_file_hash(str(filepath))
            self.server.datasources.download(datasource_id, filepath=str(filepath))
            new_hash = self.calculate_file_hash(str(filepath))
            
            if original_hash != new_hash:
                logging.info(f"Downloaded datasource: {datasource_name}")
                return True
            return False
            
        except ServerResponseError as e:
            logging.warning(f"Access denied: {username} cannot download {datasource_name}: {e}")
        except Exception as e:
            logging.error(f"Failed to download datasource {datasource_name}: {e}")
        return False

    async def process_project_content(self, project: Dict, base_dir: str, username: str) -> List[bool]:
        """Process all content for a project using parallel downloads."""
        results = []
        directory = Path(base_dir) / project['Name'].replace(' ', '_')
        directory.mkdir(parents=True, exist_ok=True)

        # Create download tasks
        download_tasks = []
        for workbook in project['Workbooks']:
            download_tasks.append(('workbook', workbook))
        for datasource in project['Datasources']:
            download_tasks.append(('datasource', datasource))

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = []
            for content_type, content in download_tasks:
                if content_type == 'workbook':
                    future = executor.submit(
                        self.download_workbook, str(directory), 
                        content[1], content[0], username
                    )
                else:
                    future = executor.submit(
                        self.download_datasource, str(directory), 
                        content[1], content[0], username
                    )
                futures.append(future)

            # Show progress bar for downloads
            with tqdm(total=len(futures), desc=f"Downloading {project['Name']}") as pbar:
                for future in as_completed(futures):
                    results.append(future.result())
                    pbar.update(1)

        return results

    async def create_and_fill_child_dir(self, alle_ordner: Dict, base_dir: str, child_id: str, username: str) -> None:
        """Recursively create and populate directory structure with parallel processing."""
        proj = alle_ordner.get(child_id)
        if not proj:
            return

        # Process current project's content
        await self.process_project_content(proj, base_dir, username)

        # Process child directories recursively
        for child in proj['Child Dirs']:
            await self.create_and_fill_child_dir(alle_ordner, base_dir, child, username)

    def connect_to_tableau(self) -> None:
        """Establish connection to Tableau server using environment variables."""
        try:
            username = os.getenv('TABLEAU_USERNAME')
            password = os.getenv('TABLEAU_PASSWORD')
            if not username or not password:
                raise ValueError("Tableau credentials not found in environment variables")

            tableau_auth = TSC.TableauAuth(username, password, 'User')
            self.server = TSC.Server(self.config['tableau_server'], use_server_version=True)
            self.server.auth.sign_in(tableau_auth)
            logging.info("Successfully connected to Tableau server")
        except Exception as e:
            logging.error(f"Failed to connect to Tableau server: {e}")
            raise

    async def backup_tableau(self) -> None:
        """Main backup process with parallel processing."""
        try:
            self.connect_to_tableau()

            # Initialize Git repository
            repo = git.Repo.clone_from(self.config['git_repo'], self.config['base_dir'])
            logging.info("Cloned Git repository")

            # Build project cache
            projects = list(TSC.Pager(self.server.projects))
            self.project_cache = {
                proj.id: {'name': proj.name, 'parent_id': proj.parent_id}
                for proj in projects
            }

            # Process projects in parallel
            root_projects = [proj for proj in projects if not proj.parent_id]
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = []
                for proj in root_projects:
                    future = executor.submit(
                        self.create_and_fill_child_dir,
                        self.project_cache,
                        self.config['base_dir'],
                        proj.id,
                        os.getenv('TABLEAU_USERNAME')
                    )
                    futures.append(future)

                # Show progress bar for project processing
                with tqdm(total=len(futures), desc="Processing projects") as pbar:
                    for future in as_completed(futures):
                        future.result()
                        pbar.update(1)

            # Commit and push changes
            await self._commit_and_push_changes(repo)

        except Exception as e:
            logging.error(f"Backup failed: {e}")
            raise
        finally:
            if self.server:
                self.server.auth.sign_out()

    async def _commit_and_push_changes(self, repo: git.Repo) -> None:
        """Commit and push changes to Git repository with progress indication."""
        try:
            repo.git.add(all=True)
            author = Actor(
                self.config['git_author']['name'],
                self.config['git_author']['email']
            )
            commit_msg = f"Backup {datetime.now().strftime('%Y-%m-%d %X')}"
            repo.index.commit(commit_msg, author=author, committer=author)
            
            # Show progress during push
            with tqdm(total=1, desc="Pushing to Git") as pbar:
                repo.git.push()
                pbar.update(1)
                
            logging.info("Successfully committed and pushed changes to Git")
        except Exception as e:
            logging.error(f"Failed to commit/push changes: {e}")
            raise

async def main():
    parser = argparse.ArgumentParser(description='Tableau Backup Tool')
    parser.add_argument('--config', default='config.yaml', help='Path to config file')
    args = parser.parse_args()

    backup_tool = TableauBackup(args.config)
    await backup_tool.backup_tableau()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())