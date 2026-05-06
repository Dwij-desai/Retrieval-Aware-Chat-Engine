#!/usr/bin/env python
"""
Automated Data Ingestion Orchestrator

Runs in the background and automatically ingests files from data/ directory.
Can be deployed as a service or cron job.

Usage:
    # Run continuously
    python backend/ingest_orchestrator.py --watch

    # Run once and exit
    python backend/ingest_orchestrator.py --once

    # Run with a schedule (every hour)
    python backend/ingest_orchestrator.py --schedule hourly
"""

import argparse
import logging
import sys
import time
from pathlib import Path
from typing import Optional

try:
    from backend.ingest import ingest_documents_from_directory
    from backend.file_watcher import start_ingestion_watcher
except ImportError:
    from ingest import ingest_documents_from_directory
    from file_watcher import start_ingestion_watcher

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def ingest_callback(file_path: str):
    """
    Callback for file watcher - ingests a single file.
    
    Args:
        file_path: Path to file to ingest
    """
    try:
        logger.info(f"📥 Ingesting file: {file_path}")
        ingest_documents_from_directory(str(Path(file_path).parent))
        logger.info(f"✅ Successfully processed: {file_path}")
    except Exception as e:
        logger.error(f"❌ Failed to ingest {file_path}: {e}")


def run_watch_mode():
    """Watch data directory continuously."""
    logger.info("🚀 Starting continuous ingestion watcher...")
    start_ingestion_watcher(ingest_callback=ingest_callback, block=True)


def run_once(data_dir: str = "data"):
    """Run ingestion once and exit."""
    logger.info(f"📥 Running one-time ingestion from {data_dir}...")
    try:
        ingest_documents_from_directory(data_dir)
        logger.info("✅ Ingestion completed")
        return 0
    except Exception as e:
        logger.error(f"❌ Ingestion failed: {e}")
        return 1


def run_schedule(interval: str = "hourly"):
    """Run ingestion on a schedule."""
    intervals = {
        "hourly": 3600,
        "daily": 86400,
        "weekly": 604800,
    }

    seconds = intervals.get(interval)
    if not seconds:
        logger.error(f"Unknown interval: {interval}. Use: hourly, daily, weekly")
        return 1

    logger.info(f"📅 Starting scheduled ingestion ({interval})...")

    try:
        while True:
            logger.info(f"🔄 Running scheduled ingestion...")
            try:
                ingest_documents_from_directory("data")
                logger.info(f"✅ Scheduled ingestion completed")
            except Exception as e:
                logger.error(f"❌ Scheduled ingestion failed: {e}")

            logger.info(f"⏳ Next ingestion in {interval} ({seconds}s)")
            time.sleep(seconds)

    except KeyboardInterrupt:
        logger.info("Stopping scheduled ingestion")
        return 0


def run_daemon():
    """Run as a background daemon (Unix-only)."""
    try:
        import daemon
        with daemon.DaemonContext():
            run_watch_mode()
    except ImportError:
        logger.error("python-daemon not installed. Install with: pip install python-daemon")
        logger.info("Running in foreground instead...")
        run_watch_mode()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Automated data ingestion orchestrator"
    )
    parser.add_argument(
        "--mode",
        choices=["watch", "once", "schedule", "daemon"],
        default="watch",
        help="Ingestion mode (default: watch)"
    )
    parser.add_argument(
        "--interval",
        choices=["hourly", "daily", "weekly"],
        default="hourly",
        help="Schedule interval when using --mode schedule"
    )
    parser.add_argument(
        "--data-dir",
        default="data",
        help="Data directory to watch (default: data)"
    )

    # Legacy argument names for compatibility
    parser.add_argument("--watch", action="store_true", help="Watch mode (legacy)")
    parser.add_argument("--once", action="store_true", help="Once mode (legacy)")
    parser.add_argument("--schedule", type=str, help="Schedule mode (legacy)")
    parser.add_argument("--daemon", action="store_true", help="Daemon mode (legacy)")

    args = parser.parse_args()

    # Handle legacy arguments
    if args.watch:
        args.mode = "watch"
    elif args.once:
        args.mode = "once"
    elif args.schedule:
        args.mode = "schedule"
        args.interval = args.schedule
    elif args.daemon:
        args.mode = "daemon"

    logger.info(f"🚀 Data Ingestion Orchestrator")
    logger.info(f"   Mode: {args.mode}")
    if args.mode == "schedule":
        logger.info(f"   Interval: {args.interval}")

    # Run selected mode
    if args.mode == "watch":
        return run_watch_mode() or 0
    elif args.mode == "once":
        return run_once(args.data_dir)
    elif args.mode == "schedule":
        return run_schedule(args.interval)
    elif args.mode == "daemon":
        return run_daemon() or 0
    else:
        logger.error(f"Unknown mode: {args.mode}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
