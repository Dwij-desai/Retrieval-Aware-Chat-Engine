"""
Automated Data Ingestion with Folder Watcher

Monitors the data/ directory for new files and automatically ingests them
without manual intervention. Useful for production environments where data
is continuously updated from external sources (S3, cloud storage, etc.).

This is a simple local solution using watchdog. For cloud environments,
use managed services:
- AWS: S3 events → Lambda → ingest
- GCP: Cloud Storage events → Cloud Functions → ingest
- Azure: Blob Storage events → Azure Functions → ingest
"""

import logging
import os
import time
from pathlib import Path
from typing import Optional

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

logger = logging.getLogger(__name__)


class DataIngestionHandler(FileSystemEventHandler):
    """Watch for new files and trigger ingestion."""

    def __init__(self, ingest_callback=None):
        """
        Initialize handler.
        
        Args:
            ingest_callback: Function to call when a file is detected.
                           Should accept file path as argument.
        """
        self.ingest_callback = ingest_callback
        self.processed_files = set()

    def on_created(self, event):
        """Trigger ingestion when a file is created."""
        if event.is_directory:
            return

        file_path = event.src_path
        
        # Ignore temporary files
        if self._should_ignore(file_path):
            return

        # Prevent duplicate processing
        if file_path in self.processed_files:
            return

        # Wait for file to be fully written
        if not self._is_file_ready(file_path):
            logger.info(f"⏳ Waiting for {Path(file_path).name} to be ready...")
            time.sleep(1)
            if not self._is_file_ready(file_path):
                return

        self.processed_files.add(file_path)
        logger.info(f"📥 New file detected: {Path(file_path).name}")

        if self.ingest_callback:
            try:
                self.ingest_callback(file_path)
                logger.info(f"✅ Successfully ingested: {Path(file_path).name}")
            except Exception as e:
                logger.error(f"❌ Ingestion failed for {file_path}: {e}")

    def on_modified(self, event):
        """Optionally re-ingest if a file is modified."""
        if event.is_directory:
            return

        file_path = event.src_path
        if self._should_ignore(file_path):
            return

        # Remove from processed to allow re-ingestion
        self.processed_files.discard(file_path)
        logger.info(f"🔄 File modified, queued for re-ingestion: {Path(file_path).name}")

    @staticmethod
    def _should_ignore(file_path: str) -> bool:
        """Check if file should be ignored."""
        name = Path(file_path).name
        # Ignore hidden files, temp files, system files
        return name.startswith('.') or name.endswith(('~', '.tmp', '.swp'))

    @staticmethod
    def _is_file_ready(file_path: str, timeout: int = 5) -> bool:
        """Check if file has finished being written."""
        try:
            with open(file_path, 'rb'):
                return True
        except (IOError, OSError):
            return False


def watch_data_directory(
    data_dir: str = "data",
    ingest_callback=None,
    recursive: bool = True,
) -> Observer:
    """
    Start watching data directory for new files.
    
    Args:
        data_dir: Directory to watch (default: "data")
        ingest_callback: Function to call when files are detected
        recursive: Watch subdirectories too
    
    Returns:
        watchdog.observers.Observer that can be started/stopped
    
    Example:
        def ingest_file(path):
            print(f"Ingesting {path}")
        
        observer = watch_data_directory(ingest_callback=ingest_file)
        observer.start()
        
        # Later, stop watching
        observer.stop()
        observer.join()
    """
    data_path = Path(data_dir)
    data_path.mkdir(parents=True, exist_ok=True)

    handler = DataIngestionHandler(ingest_callback=ingest_callback)
    observer = Observer()
    observer.schedule(handler, str(data_path), recursive=recursive)

    logger.info(f"👁️  Watching {data_path.absolute()} for new files...")
    return observer


def start_ingestion_watcher(ingest_callback=None, block: bool = False):
    """
    Start watching for files (optionally blocking).
    
    Args:
        ingest_callback: Function to call for each new file
        block: If True, block until KeyboardInterrupt. If False, return observer.
    
    Returns:
        Observer if block=False, else None
    """
    observer = watch_data_directory(ingest_callback=ingest_callback)
    observer.start()

    if block:
        try:
            logger.info("Ingestion watcher running (press Ctrl+C to stop)...")
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Stopping watcher...")
            observer.stop()
        finally:
            observer.join()
        return None
    else:
        return observer


# Example usage for testing
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Simple callback for testing
    def test_ingest(file_path):
        print(f"Would ingest: {file_path}")

    # Start watcher (blocking)
    start_ingestion_watcher(ingest_callback=test_ingest, block=True)
