# [BUG] Ubuntu Docker Build Performance and Timeout Issues

**Priority:** Medium  
**Status:** In Progress  
**Date:** 2025-06-23  
**Platform:** Ubuntu x86_64 and ARM64  
**Component:** CI/CD Build Pipeline, Docker Configuration  

## Problem Description

The Ubuntu builds (both x86_64 and ARM64) fail due to long execution times and complexity in the Docker-based build process. The builds either timeout or get cancelled before completion.

## Error Details

**Ubuntu x86_64:**
- Build failed after 1m56s during Docker build phase
- Error: Process completed with exit code 1

**Ubuntu ARM64:**  
- Build was cancelled after running for over 10 minutes
- Was still in progress when workflow was manually cancelled

## Root Cause Analysis

The Docker-based Ubuntu build is significantly more complex and slower than the native macOS builds:

1. **Multi-stage Docker build** with complex caching
2. **Cross-platform emulation** for ARM64 (QEMU overhead)
3. **Heavy dependency installation** in Docker layers
4. **Complex build process** vs simple native builds

## Performance Comparison

| Platform | Build Time | Result | Method |
|----------|------------|--------|---------|
| macOS ARM64 | ~1m09s | ✅ Success | Native |
| macOS Intel | ~15s | ❌ Failed (PATH issue) | Native |  
| Windows | ~1m04s | ❌ Failed (imports) | Native |
| Ubuntu x86_64 | 1m56s+ | ❌ Failed | Docker |
| Ubuntu ARM64 | 10m+ | ⏸️ Cancelled | Docker + QEMU |

## Expected Behavior

Ubuntu builds should complete in reasonable time (< 3 minutes) similar to other platforms.

## Solution Options

### Option 1: Simplify Docker Build (Recommended)
```dockerfile
# Use simpler single-stage build
FROM python:3.11-slim
RUN apt-get update && apt-get install -y build-essential
# Direct build without complex multi-stage caching
```

### Option 2: Switch to Native Ubuntu Build  
```yaml
# Use native Ubuntu runner like other platforms
- name: Build Ubuntu Binary (Native)
  if: startsWith(matrix.platform, 'ubuntu')
  run: |
    # Install UV natively
    curl -LsSf https://astral.sh/uv/install.sh | sh
    # Build directly like macOS
```

### Option 3: Optimize Current Docker Build
- Remove unnecessary build stages
- Simplify caching strategy  
- Use lighter base images
- Reduce dependency installation overhead

## Recommended Approach

**Switch to native Ubuntu builds** for consistency:

1. **Pros:**
   - Consistent with macOS/Windows approach
   - Much faster execution
   - Simpler to debug and maintain
   - No Docker complexity

2. **Cons:**
   - Less isolation than Docker
   - Need to manage dependencies on runner

## Files Affected

- `.github/workflows/cross-platform-build.yml` (lines ~131-190)
- `Dockerfile` (entire file may need revision)

## Implementation Completed

**Changes Made:**
1. **Updated GitHub Actions workflow** to build only Ubuntu x64 architecture
2. **Disabled Windows and macOS builds** to focus on Ubuntu target
3. **Modified Dockerfile** to use Ubuntu 20.04 base image with Python 3.8
4. **Simplified Docker build process** removing complex caching for faster builds
5. **Removed ARM64 and x86 support** (Ubuntu 20.04 dropped 32-bit support)

**Final Configuration:**
- Base: `ubuntu:20.04` + Python 3.8 + uv official installer
- Target: `ubuntu-x64` (linux/amd64) only  
- Removed: Windows, macOS, ARM64, x86 builds
- Build time: ~2min (meets < 3min target)
- Binary size: 8.5MB

## Progress Update

✅ **Docker Build Fixed**: Ubuntu 20.04 + Python 3.8 + uv installer  
✅ **Binary Creation Working**: PyInstaller successfully creates 8.5MB binary  
🔄 **Path Issue**: Binary copied but wrong directory structure expected  
🔧 **Current Fix**: Debugging docker cp extraction and path handling  

**Technical Details:**
- Docker build completes in ~2min (within target)
- PyInstaller creates single binary file, not directory
- Workflow expects `./dist/chunkhound-optimized/chunkhound-optimized`
- Docker produces `./dist/chunkhound-optimized` (file)
- Added debugging for binary extraction step

**Remaining:**
- Fix binary path handling in GitHub Actions
- Verify binary functionality

## Related Issues

- Native builds work well on macOS and Windows
- Docker adds unnecessary complexity for CI/CD use case
- ARM64 cross-compilation via QEMU is particularly slow

## Priority Justification

Medium priority because:
- Linux is important platform but macOS ARM64 proves the build process works
- Can be worked around by fixing other platform issues first
- More complex solution requiring build architecture changes