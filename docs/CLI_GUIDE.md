# ChunkHound CLI Guide

## Overview

ChunkHound provides a comprehensive command-line interface for managing embedding servers, indexing code, and performing semantic searches. This guide covers all CLI commands with practical examples.

**Performance**: CLI startup ~0.3s (Python) / ~0.6s (standalone binary)
**Languages**: Python, Java, C#, TypeScript, JavaScript, Markdown
**Architecture**: Service-layer with registry pattern for maximum flexibility

## Installation & Setup

```bash
# Install ChunkHound (Python 3.10+ required)
pip install chunkhound

# Or install with uv (recommended)
uv add chunkhound

# Create your first configuration (optional)
chunkhound config template --output ~/.chunkhound/config.yaml

# Test basic functionality
chunkhound --version
chunkhound --help

# Quick start - index current directory
chunkhound run . --no-embeddings  # Fast indexing without embeddings
```

## Core Commands

### `chunkhound run` - Index and Watch Code

Index code repositories and optionally watch for changes:

```bash
# Basic usage - index current directory
chunkhound run .

# Index specific directory
chunkhound run /path/to/your/project

# Index an installed Python package
chunkhound run --package requests

# Watch for changes in real-time
chunkhound run . --watch

# Initial scan only (no watching)
chunkhound run . --initial-scan-only

# Custom database location
chunkhound run . --db ./my-chunks.duckdb

# Include/exclude specific files
chunkhound run . --include "*.py" --include "*.js" --exclude "*/tests/*"

# Skip embedding generation (code structure only)
chunkhound run . --no-embeddings

# Use specific embedding provider
chunkhound run . --provider tei --base-url http://localhost:8080

# Use specific model (optional - defaults to text-embedding-3-small for OpenAI)
chunkhound run . --model text-embedding-3-large

# Performance tuning options
chunkhound run . --batch-size 100 --max-concurrent 5

# Force reindexing of all files
chunkhound run . --force-reindex

# Clean up orphaned chunks from deleted files
chunkhound run . --cleanup

# Custom debounce timing for file changes
chunkhound run . --debounce-ms 1000

# Verbose output for debugging
chunkhound run . --verbose
```

### `chunkhound mcp` - Model Context Protocol Server

Start an MCP server for AI assistant integration:

```bash
# Start MCP server (stdio transport, default)
chunkhound mcp

# Use custom database
chunkhound mcp --db ./my-chunks.duckdb

# Enable verbose logging
chunkhound mcp --verbose

# HTTP transport instead of stdio
chunkhound mcp --http --port 3000 --host localhost

# HTTP with CORS enabled
chunkhound mcp --http --cors --port 8080

# Stdio transport (explicit)
chunkhound mcp --stdio
```

### Configuration Management

⚠️ **Implementation Status**: Configuration management is partially implemented. Basic functionality works but advanced features are under development.

### Server Management

#### `chunkhound config list` - List Servers

```bash
# List all configured servers
chunkhound config list

# Show health status
chunkhound config list --show-health

# Use specific config file
chunkhound config list --config ./my-config.yaml
```

#### `chunkhound config add` - Add Server

⚠️ **Status**: Under Development

```bash
# Add OpenAI server (⚠️ Under Development)
chunkhound config add openai \
  --type openai \
  --base-url https://api.openai.com/v1 \
  --model text-embedding-3-small \
  --default

# Add local TEI server (⚠️ Under Development)
chunkhound config add local-tei \
  --type tei \
  --base-url http://localhost:8080 \
  --batch-size 32 \
  --timeout 60

# Add OpenAI-compatible server (⚠️ Under Development)
chunkhound config add custom-server \
  --type openai-compatible \
  --base-url https://api.custom.com/v1 \
  --model custom-embeddings \
  --api-key your-api-key

# Add with custom health check interval (⚠️ Under Development)
chunkhound config add production \
  --type openai-compatible \
  --base-url https://embeddings.company.com \
  --health-check-interval 30
```

#### `chunkhound config remove` - Remove Server

⚠️ **Status**: Under Development

```bash
# Remove a server (⚠️ Under Development)
chunkhound config remove server-name

# Use specific config file (⚠️ Under Development)
chunkhound config remove server-name --config ./my-config.yaml
```

#### `chunkhound config enable/disable` - Server Control

⚠️ **Status**: Under Development

```bash
# Enable a server (⚠️ Under Development)
chunkhound config enable server-name

# Disable a server (⚠️ Under Development)
chunkhound config disable server-name
```

#### `chunkhound config set-default` - Set Default Server

⚠️ **Status**: Under Development

```bash
# Set default server (⚠️ Under Development)
chunkhound config set-default server-name
```

### Testing & Validation

#### `chunkhound config test` - Test Server Connectivity

⚠️ **Status**: Under Development

```bash
# Test default server (⚠️ Under Development)
chunkhound config test

# Test specific server (⚠️ Under Development)
chunkhound config test server-name

# Test with custom text (⚠️ Under Development)
chunkhound config test server-name --text "custom test phrase"
```

#### `chunkhound config validate` - Validate Configuration

```bash
# Validate current configuration
chunkhound config validate

# Validate and auto-fix issues
chunkhound config validate --fix

# Validate specific config file
chunkhound config validate --config ./my-config.yaml
```

#### `chunkhound config batch-test` - Test All Servers

```bash
# Test all enabled servers in parallel
chunkhound config batch-test

# Custom timeout and test text
chunkhound config batch-test --timeout 60 --text "batch test phrase"
```

### Health Monitoring

#### `chunkhound config health` - Check Server Health

```bash
# Check all servers
chunkhound config health

# Check specific server
chunkhound config health server-name

# Continuous monitoring
chunkhound config health --monitor
```

### Performance Analysis

#### `chunkhound config benchmark` - Benchmark Performance

```bash
# Benchmark all servers
chunkhound config benchmark

# Benchmark specific server
chunkhound config benchmark server-name

# Custom test parameters
chunkhound config benchmark --samples 20 --batch-sizes 1 5 10 20 50

# Benchmark with detailed analysis
chunkhound config benchmark server-name --samples 10
```

Example output:
```
Benchmarking 'local-tei'...
  Testing batch size 1...
    847.3 embeddings/sec (1.2ms avg)
  Testing batch size 5...
    1205.4 embeddings/sec (4.1ms avg)
  Testing batch size 10...
    1456.2 embeddings/sec (6.9ms avg) 🏆
```

### Provider Switching

#### `chunkhound config switch` - Switch Providers

```bash
# Switch to different provider with validation
chunkhound config switch server-name

# Switch without validation
chunkhound config switch server-name --no-validate

# Switch with performance comparison
chunkhound config switch new-server
```

Example output:
```
🔍 Validating server 'local-tei'...
✅ Server is healthy (45.2ms)

📊 Comparing performance: 'openai' vs 'local-tei'...
  Current (openai):     127.3ms, 1536 dimensions
  New     (local-tei):   45.2ms, 384 dimensions
  🚀 Performance improvement: 64.5% faster

🔧 Checking provider compatibility...
  Model: sentence-transformers/all-MiniLM-L6-v2
  Type: tei
  ✅ Provider is compatible

🎯 Provider switched successfully!
   From: openai
   To:   local-tei
```

### Configuration Discovery

#### `chunkhound config discover` - Find Configuration Files

```bash
# Discover configs from current directory
chunkhound config discover

# Discover from specific path
chunkhound config discover --path /path/to/project

# Show all files (including invalid)
chunkhound config discover --show-all
```

Example output:
```
── Project-specific (.chunkhound/) ──
✅ ./.chunkhound/config.yaml
   2 server(s): local-tei, openai-fallback (default: local-tei)

── User configs (~/.chunkhound/) ──
✅ /Users/you/.chunkhound/config.yaml
   1 server(s): openai (default: openai)

🎯 Recommended: Use './.chunkhound/config.yaml' (priority 1)
```

### Configuration Import/Export

#### `chunkhound config export` - Export Configuration

```bash
# Export to YAML (default)
chunkhound config export backup.yaml

# Export to JSON
chunkhound config export backup.json --format json

# Export from specific config
chunkhound config export backup.yaml --config ./source-config.yaml
```

#### `chunkhound config import` - Import Configuration

```bash
# Import configuration
chunkhound config import backup.yaml

# Merge with existing config
chunkhound config import additional.yaml --merge

# Import without backup
chunkhound config import config.yaml --no-backup

# Import to specific location
chunkhound config import source.yaml --config ./target-config.yaml
```

### Configuration Templates

#### `chunkhound config template` - Generate Templates

```bash
# Generate basic template (⚠️ Under Development)
chunkhound config template basic

# Generate specific template type (⚠️ Under Development)
chunkhound config template openai
chunkhound config template tei
chunkhound config template bge-in-icl
chunkhound config template multi

# Save to file (⚠️ Under Development)
chunkhound config template basic --output .chunkhound/config.yaml
```

Available template types:
- **basic**: Simple OpenAI configuration
- **openai**: OpenAI API configuration
- **tei**: Text Embeddings Inference server
- **bge-in-icl**: BGE In-Context Learning setup
- **multi**: Multi-server configuration

⚠️ **Note**: Template generation is currently under development. Use `chunkhound config list` to see existing configurations.

## Common Workflows

### Setting Up Local Embeddings

1. **Start a local TEI server:**
```bash
docker run -p 8080:80 -v $PWD/data:/data \
  ghcr.io/huggingface/text-embeddings-inference:latest \
  --model-id sentence-transformers/all-MiniLM-L6-v2
```

2. **Generate local configuration (⚠️ Under Development):**
```bash
chunkhound config template tei --output .chunkhound/config.yaml
```

3. **Test the setup (⚠️ Under Development):**
```bash
chunkhound config test local-tei
```

4. **Start indexing:**
```bash
chunkhound run . --watch
```

### Production Deployment

⚠️ **Status**: Configuration system under development. For production use, set environment variables directly:

```bash
# Set OpenAI API key for semantic search
export OPENAI_API_KEY="your-api-key-here"

# Start production indexing
chunkhound run /path/to/codebase --watch

# Start MCP server for AI assistant integration
chunkhound mcp --verbose
```

**Advanced Configuration (⚠️ Under Development):**

1. **Create production config:**
```bash
chunkhound config template multi --output production-config.yaml
```

2. **Validate configuration:**
```bash
chunkhound config validate --config production-config.yaml
```

3. **Test all servers:**
```bash
chunkhound config batch-test --config production-config.yaml
```

### Switching Between Environments

⚠️ **Status**: Under Development

```bash
# Development (local) (⚠️ Under Development)
chunkhound config switch dev-local

# Staging (⚠️ Under Development)
chunkhound config switch staging-cluster

# Production (⚠️ Under Development)
chunkhound config switch production-cluster

# Emergency fallback (⚠️ Under Development)
chunkhound config enable emergency-fallback
chunkhound config switch emergency-fallback
```

**Current Workaround**: Use environment variables to switch between configurations:
```bash
# Development
export OPENAI_API_KEY="dev-key"
chunkhound run . --watch

# Production
export OPENAI_API_KEY="prod-key"
chunkhound run /prod/code --watch
```

### Health Monitoring

```bash
# One-time health check
chunkhound config health

# Continuous monitoring
chunkhound config health --monitor

# Check specific server
chunkhound config health production-cluster
```

### Performance Optimization

```bash
# Benchmark all servers
chunkhound config benchmark

# Compare specific servers
chunkhound config benchmark server1
chunkhound config benchmark server2

# Test different batch sizes
chunkhound config benchmark --batch-sizes 1 8 16 32 64 128
```

## Troubleshooting

### Configuration Issues

```bash
# Check configuration validity
chunkhound config validate

# Discover configuration files
chunkhound config discover

# Fix common issues automatically
chunkhound config validate --fix
```

### Server Connectivity

```bash
# Test server connectivity
chunkhound config test server-name

# Check server health
chunkhound config health server-name

# Test all servers
chunkhound config batch-test
```

### Performance Issues

```bash
# Benchmark servers
chunkhound config benchmark

# Compare performance
chunkhound config switch new-server  # Shows comparison

# Check server health
chunkhound config health --monitor
```

## Environment Variables

ChunkHound respects these environment variables:

- `OPENAI_API_KEY` - OpenAI API key
- `CHUNKHOUND_CONFIG` - Default config file path
- `CHUNKHOUND_DB` - Default database path
- `CHUNKHOUND_PRODUCTION_API_KEY` - Production API key
- `CHUNKHOUND_STAGING_API_KEY` - Staging API key

## Configuration File Locations

ChunkHound searches for configuration files in this order:

1. `.chunkhound/config.yaml` (project-specific)
2. `.chunkhound/config.yml`
3. `~/.chunkhound/config.yaml` (user-specific)
4. `~/.chunkhound/config.yml`
5. `/etc/chunkhound/config.yaml` (system-wide)
6. `/etc/chunkhound/config.yml`

## Exit Codes

- `0` - Success
- `1` - General error or validation failure
- `2` - Configuration error
- `130` - Interrupted by user (Ctrl+C)

## Getting Help

```bash
# General help
chunkhound --help

# Command-specific help
chunkhound config --help
chunkhound config add --help

# Version information
chunkhound --version
```

For more information and examples, see the documentation at:
https://github.com/your-org/chunkhound/docs