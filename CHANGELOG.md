# Changelog

All notable changes to ChunkHound will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Extensive language support: Rust, Go, C++, C, Kotlin, Groovy, Bash, TOML, Makefile, and Matlab
- Registry-based parser architecture for better extensibility
- Task coordinator for improved MCP search responsiveness
- PyInstaller compatibility with multiprocessing support
- Comprehensive IDE integration documentation

### Changed
- Refactored parser system to use registry pattern exclusively
- Improved embedding performance with token-aware batching
- Enhanced code quality with better type annotations
- Optimized embedding service configuration with higher defaults
- Simplified progress tracking for embedding operations

### Fixed
- PyInstaller module path resolution
- OpenAI token limit handling with improved error recovery
- Embedding generation batch operations performance

## [1.2.3] - 2025-06-23

### Changed
- Default database location changed to current directory for better persistence

### Fixed
- OpenAI token limit exceeded error with dynamic batching for large embedding requests
- Empty chunk filtering to reduce noise in search results
- Python parser validation for empty symbol names
- Windows build support with comprehensive GitHub Actions workflow
- macOS Intel build issues with UV package manager installation
- Cross-platform build workflow reliability

### Added
- Windows build support with automated testing
- Enhanced debugging for build processes across platforms

## [1.2.2] - 2024-12-15

### Added
- File watching CLI for real-time code monitoring

### Changed
- Unified JavaScript and TypeScript parsers
- Default database location to current directory

### Fixed
- Empty symbol validation in Python parser

## [1.2.1] - 2024-11-28

### Added
- Ubuntu 20.04 build support
- Token limit management for MCP search

### Fixed
- Duplicate chunks after file edits
- File modification detection race conditions

## [1.2.0] - 2024-11-15

### Added
- C# language support
- JSON, YAML, and plain text file support
- File watching with real-time indexing

### Fixed
- File deletion handling
- Database connection issues

## [1.1.0] - 2025-06-12

### Added
- Multi-language support: TypeScript, JavaScript, C#, Java, and Markdown
- Comprehensive CLI interface
- Binary distribution with faster startup

### Changed
- Improved CLI startup performance (90% faster)
- Binary startup performance (16x faster)

### Fixed
- Version display consistency
- Cross-platform build issues

## [1.0.1] - 2025-06-11

### Added
- Python 3.10+ compatibility
- PyPI publishing
- Standalone executable support
- MCP server integration

### Fixed
- Dependency conflicts
- OpenAI model parameter handling
- Binary compilation issues

## [1.0.0] - 2025-06-10

### Added
- Initial release of ChunkHound
- Python parsing with tree-sitter
- DuckDB backend for storage and search
- OpenAI embeddings for semantic search
- CLI interface for indexing and searching
- MCP server for AI assistant integration
- File watching for real-time indexing
- Regex search capabilities

For more information, visit: https://github.com/chunkhound/chunkhound

[Unreleased]: https://github.com/chunkhound/chunkhound/compare/v1.2.3...HEAD
[1.2.3]: https://github.com/chunkhound/chunkhound/compare/v1.2.2...v1.2.3
[1.2.2]: https://github.com/chunkhound/chunkhound/compare/v1.2.1...v1.2.2
[1.2.1]: https://github.com/chunkhound/chunkhound/compare/v1.2.0...v1.2.1
[1.2.0]: https://github.com/chunkhound/chunkhound/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/chunkhound/chunkhound/compare/v1.0.1...v1.1.0
[1.0.1]: https://github.com/chunkhound/chunkhound/compare/v1.0.0...v1.0.1
[1.0.0]: https://github.com/chunkhound/chunkhound/releases/tag/v1.0.0