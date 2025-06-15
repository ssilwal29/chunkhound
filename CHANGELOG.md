# Changelog

All notable changes to ChunkHound will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2025-06-12

### Added
- **Multi-language support**: TypeScript, JavaScript, C#, Java, and Markdown parsing
- **Comprehensive CLI interface** with improved argument parsing and help system
- **Architecture documentation** with detailed system design and extension points
- **Docker build infrastructure** with multi-stage cross-platform support
- **Binary distribution** with onedir deployment for faster startup (~0.6s vs 15s+)
- **Performance improvements**: CLI startup time optimized to ~0.3s (90% improvement)
- **File watcher debugging** with comprehensive timing instrumentation
- **Fallback BLOCK chunk support** for unstructured Python files
- **pytest development dependencies** for enhanced testing support

### Changed
- **CLI startup performance**: Reduced from ~2.7s to ~0.3s (Python version)
- **Binary startup performance**: Reduced from 15+ seconds to ~0.6s with onedir distribution
- **Documentation structure**: Unified build system documentation and comprehensive CLI usage guide
- **Version consistency**: Fixed version display inconsistency across all modules
- **Configuration system**: Basic functionality implemented, advanced features marked as under development

### Fixed
- **macOS build script**: Fixed directory rename bug in build process
- **Version display**: Consistent 1.1.0 version across CLI, MCP server, and all modules
- **Real-time file sync**: Added debugging instrumentation for better diagnostics
- **Database handling**: Improved error handling and connection management
- **Cross-platform compatibility**: Enhanced build system for macOS and Linux

### Technical Details
- **Languages supported**: Python, Java, C#, TypeScript, JavaScript, Markdown
- **Parser accuracy**: 95%+ successful parsing of valid code files
- **Test coverage**: 262/274 tests passing (95.6% pass rate)
- **Performance metrics**: 44 files processed with 776 chunks in ~4 seconds
- **Database**: DuckDB with VSS extension for vector similarity search
- **Architecture**: Service-layer with registry pattern for maximum flexibility

## [1.0.1] - 2025-06-11

### Added
- **Python 3.10+ compatibility** with comprehensive dependency audit
- **PyPI publishing** with automated release pipeline
- **Standalone executable** support with PyInstaller
- **MCP server integration** with Model Context Protocol support
- **Search functionality**: Both semantic and regex search capabilities

### Fixed
- **Dependency conflicts** resolved for Python 3.10+ environments
- **OpenAI model parameter** handling for embedding generation
- **Binary compilation** issues with PyInstaller
- **MCP launcher** compatibility problems

### Changed
- **Minimum Python version**: Requires Python 3.10+ for full compatibility
- **Packaging**: Published to PyPI for easy installation
- **Documentation**: Added troubleshooting guides and installation instructions

## [1.0.0] - 2025-06-10

### Added
- **Initial release** of ChunkHound
- **Python parsing** with tree-sitter for accurate syntax analysis
- **DuckDB backend** for efficient storage and search
- **OpenAI embeddings** integration for semantic search
- **CLI interface** for indexing and searching code
- **MCP server** for AI assistant integration
- **File watching** for real-time code indexing
- **Regex search** capabilities alongside semantic search

### Features
- **Code parsing**: Extract functions, classes, methods from Python files
- **Semantic search**: AI-powered code search using embeddings
- **Regex search**: Pattern-based code search
- **Real-time indexing**: Watch file changes and update index automatically
- **AI assistant integration**: Work with Claude, Cursor, VS Code via MCP
- **Local-first**: All processing and storage happens locally

### Technical Specifications
- **Database**: DuckDB with vector similarity search (VSS) extension
- **Parsing**: Tree-sitter based for accurate syntax analysis
- **Embeddings**: OpenAI text-embedding-3-small (1536 dimensions)
- **Languages**: Python (initial release)
- **Platforms**: macOS and Linux support

---

## Version History Summary

- **v1.1.0**: Multi-language support, performance improvements, comprehensive documentation
- **v1.0.1**: Python 3.10+ compatibility, PyPI publishing, standalone executables
- **v1.0.0**: Initial release with Python parsing and semantic search

## Upcoming Features (Roadmap)

### Configuration System (v1.2.0)
- Full implementation of configuration management CLI
- Template generation for different deployment scenarios
- Server health monitoring and benchmarking
- Multi-provider support with automatic failover

### Additional Languages (v1.3.0)
- Rust language support
- Go language support
- PHP language support
- Enhanced parsing for existing languages

### Advanced Features (v1.4.0)
- Code similarity analysis
- Dependency graph extraction
- Custom embedding models support
- Performance analytics and insights

---

## Development Notes

### Build System
- **Python package**: Available via `pip install chunkhound`
- **Standalone binary**: Self-contained executable with zero dependencies
- **Docker**: Multi-stage builds for containerized deployment
- **Cross-platform**: Automated builds for macOS and Linux

### Testing
- **Test suite**: 274 tests with 95.6% pass rate
- **CI/CD**: Automated testing and release pipeline
- **Performance testing**: Startup time and indexing performance validation
- **Integration testing**: End-to-end functionality verification

### Documentation
- **Architecture guide**: Comprehensive system design documentation
- **CLI guide**: Complete command reference with examples
- **Troubleshooting**: Common issues and solutions
- **API documentation**: MCP integration details

For more information, visit: https://github.com/chunkhound/chunkhound