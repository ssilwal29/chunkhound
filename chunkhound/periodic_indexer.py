#!/usr/bin/env python3
"""
Periodic Indexing Manager for ChunkHound MCP Server
Provides background periodic indexing to maintain database consistency.
"""

import asyncio
import os
import time
from pathlib import Path
from typing import Any

from loguru import logger

from .task_coordinator import TaskCoordinator, TaskPriority


class PeriodicIndexManager:
    """Manages background periodic indexing with lowest priority."""

    def __init__(
        self,
        indexing_coordinator,
        task_coordinator: TaskCoordinator,
        base_directory: Path,
        interval: int = 300,  # 5 minutes default
        batch_size: int = 10,
        enabled: bool = True
    ):
        """Initialize periodic index manager.

        Args:
            indexing_coordinator: IndexingCoordinator instance for file processing
            task_coordinator: TaskCoordinator for priority-based execution
            base_directory: Base directory to scan for changes
            interval: Scan interval in seconds (default: 300)
            batch_size: Files per batch (default: 10)
            enabled: Whether periodic indexing is enabled (default: True)
        """
        self._indexing_coordinator = indexing_coordinator
        self._task_coordinator = task_coordinator
        self._base_directory = base_directory
        self._interval = interval
        self._batch_size = batch_size
        self._enabled = enabled
        
        # State tracking
        self._scanning_task: asyncio.Task | None = None
        self._shutdown_event = asyncio.Event()
        self._running = False
        self._scan_position = 0
        self._last_scan_time = 0
        
        # Statistics
        self._stats = {
            'scans_completed': 0,
            'files_processed': 0,
            'files_updated': 0,
            'files_skipped': 0,
            'last_scan_duration': 0
        }

    @classmethod
    def from_environment(
        cls,
        indexing_coordinator,
        task_coordinator: TaskCoordinator,
        base_directory: Path
    ) -> 'PeriodicIndexManager':
        """Create periodic index manager from environment variables.

        Environment Variables:
            CHUNKHOUND_PERIODIC_INDEX_INTERVAL: Scan interval in seconds (default: 300)
            CHUNKHOUND_PERIODIC_BATCH_SIZE: Files per batch (default: 10)
            CHUNKHOUND_PERIODIC_INDEX_ENABLED: Enable/disable (default: true)

        Args:
            indexing_coordinator: IndexingCoordinator instance
            task_coordinator: TaskCoordinator instance
            base_directory: Base directory to scan

        Returns:
            Configured PeriodicIndexManager instance
        """
        interval = int(os.getenv('CHUNKHOUND_PERIODIC_INDEX_INTERVAL', '300'))
        batch_size = int(os.getenv('CHUNKHOUND_PERIODIC_BATCH_SIZE', '10'))
        enabled = os.getenv('CHUNKHOUND_PERIODIC_INDEX_ENABLED', 'true').lower() == 'true'

        return cls(
            indexing_coordinator=indexing_coordinator,
            task_coordinator=task_coordinator,
            base_directory=base_directory,
            interval=interval,
            batch_size=batch_size,
            enabled=enabled
        )

    async def start(self) -> None:
        """Start periodic indexing tasks."""
        if not self._enabled or self._running:
            return

        self._running = True
        self._shutdown_event.clear()
        
        # Start immediate background scan to catch changes since last offline index
        self._scanning_task = asyncio.create_task(self._periodic_scan_loop())
        
        logger.info(f"PeriodicIndexManager started - interval: {self._interval}s, batch_size: {self._batch_size}")

    async def stop(self, timeout: float = 30.0) -> None:
        """Stop periodic indexing tasks.

        Args:
            timeout: Maximum time to wait for graceful shutdown
        """
        if not self._running:
            return

        logger.info("PeriodicIndexManager stopping...")
        self._running = False
        self._shutdown_event.set()

        if self._scanning_task:
            try:
                await asyncio.wait_for(self._scanning_task, timeout=timeout)
            except asyncio.TimeoutError:
                logger.warning("PeriodicIndexManager scan task did not stop gracefully, cancelling")
                self._scanning_task.cancel()
                try:
                    await self._scanning_task
                except asyncio.CancelledError:
                    pass

        logger.info("PeriodicIndexManager stopped")

    def get_stats(self) -> dict[str, Any]:
        """Get statistics about periodic indexing."""
        return {
            **self._stats,
            'enabled': self._enabled,
            'running': self._running,
            'interval': self._interval,
            'batch_size': self._batch_size,
            'scan_position': self._scan_position,
            'last_scan_time': self._last_scan_time
        }

    async def _periodic_scan_loop(self) -> None:
        """Main periodic scanning loop."""
        logger.info("PeriodicIndexManager scan loop started")

        # Immediate startup scan to catch changes since last offline index
        if self._running:
            await self._queue_background_scan("startup")

        # Continue with periodic scans
        while self._running:
            try:
                # Wait for interval or shutdown signal
                try:
                    await asyncio.wait_for(
                        self._shutdown_event.wait(),
                        timeout=self._interval
                    )
                    # Shutdown signal received
                    break
                except asyncio.TimeoutError:
                    # Timeout reached, time for next scan
                    pass

                if self._running:
                    await self._queue_background_scan("periodic")

            except Exception as e:
                logger.error(f"Error in periodic scan loop: {e}")
                # Continue running despite errors
                await asyncio.sleep(5)  # Brief recovery delay

        logger.info("PeriodicIndexManager scan loop stopped")

    async def _queue_background_scan(self, scan_type: str) -> None:
        """Queue a background directory scan.

        Args:
            scan_type: Type of scan ("startup" or "periodic")
        """
        try:
            if not self._task_coordinator:
                logger.warning("No task coordinator available for background scan")
                return

            # Queue background scan task with lowest priority
            await self._task_coordinator.queue_task_nowait(
                TaskPriority.BACKGROUND,
                self._execute_background_scan,
                scan_type
            )
            
            logger.debug(f"Queued {scan_type} background scan")

        except Exception as e:
            logger.error(f"Failed to queue background scan: {e}")

    async def _execute_background_scan(self, scan_type: str) -> None:
        """Execute a background directory scan in small batches.

        Args:
            scan_type: Type of scan ("startup" or "periodic")
        """
        scan_start_time = time.time()
        logger.debug(f"Starting {scan_type} background scan")

        try:
            # Discover all files in base directory
            files = self._indexing_coordinator._discover_files(
                self._base_directory, 
                patterns=None,  # Use default patterns
                exclude_patterns=None  # Use default exclude patterns
            )

            if not files:
                logger.debug("No files found during background scan")
                return

            # Reset scan position for startup scans, continue from position for periodic
            if scan_type == "startup":
                self._scan_position = 0

            # Process files in small batches starting from scan position
            batch_count = 0
            files_in_this_scan = 0
            
            while self._scan_position < len(files) and self._running:
                # Get next batch of files
                batch_end = min(self._scan_position + self._batch_size, len(files))
                batch_files = files[self._scan_position:batch_end]
                
                # Process batch
                await self._process_file_batch(batch_files)
                
                # Update position and stats
                self._scan_position = batch_end
                batch_count += 1
                files_in_this_scan += len(batch_files)
                
                # Yield control between batches to allow higher priority tasks
                await asyncio.sleep(0.1)  # 100ms yield

            # Reset position when we reach the end
            if self._scan_position >= len(files):
                self._scan_position = 0

            # Update statistics
            scan_duration = time.time() - scan_start_time
            self._stats['scans_completed'] += 1
            self._stats['last_scan_duration'] = scan_duration
            self._last_scan_time = scan_start_time

            logger.debug(
                f"Completed {scan_type} background scan: "
                f"{files_in_this_scan} files in {batch_count} batches, "
                f"duration: {scan_duration:.2f}s"
            )

        except Exception as e:
            logger.error(f"Background scan failed: {e}")

    async def _process_file_batch(self, files: list[Path]) -> None:
        """Process a batch of files with CRC32 cache optimization.

        Args:
            files: List of file paths to process
        """
        for file_path in files:
            if not self._running:
                break

            try:
                # Use existing process_file method which includes CRC32 cache optimization
                result = await self._indexing_coordinator.process_file(
                    file_path,
                    skip_embeddings=True  # Skip embeddings for background processing
                )

                # Update statistics
                self._stats['files_processed'] += 1
                
                if result["status"] == "success":
                    self._stats['files_updated'] += 1
                elif result["status"] == "up_to_date":
                    self._stats['files_skipped'] += 1

            except Exception as e:
                logger.debug(f"Error processing file {file_path} in background: {e}")
                # Continue with next file despite errors