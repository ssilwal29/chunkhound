# 2025-06-22 - [BUG] Duplicate Chunks After File Edits

**Priority**: Low  
**Status**: Fixed

**Issue**: File edits create new chunks without removing old chunks, causing search results to contain both outdated and current content.

**Root Cause**: `IndexingCoordinator.process_file()` adds new chunks without deleting old ones during file modifications.

**Fix**: Added chunk cleanup logic in `services/indexing_coordinator.py:156-193` that deletes old chunks before adding new ones when file mtime changes.

# History

## 2025-06-22T11:46:30+03:00
Discovered during file editing QA tests. Both old and new content versions appeared in search results after file modifications.

## 2025-06-22T12:14:30+03:00
**FIXED**: Modified `IndexingCoordinator.process_file()` to check file modification time and call `self._db.delete_file_chunks(file_id)` before storing new chunks. Preserves optimization for unchanged files. Verified with test - no duplicate chunks remain after file modifications.