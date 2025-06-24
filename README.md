# ChunkHound

**Semantic and Regex search for your codebase via MCP.**

Enable AI assistants to search your code with natural language and regex patterns.

## Installation

### Python Package
```bash
uv tool install chunkhound
```

### Binary
Download from [GitHub Releases](https://github.com/ofriw/chunkhound/releases) - zero dependencies required.

## Quick Start

```bash
# Set your OpenAI API key
export OPENAI_API_KEY="sk-your-key-here"

# Index your codebase first (creates chunkhound.db in current directory)
uv run chunkhound run .

# OR: Index and watch for changes (standalone mode)
uv run chunkhound run . --watch

# Start MCP server for AI assistants (automatically watches for file changes)
uv run chunkhound mcp

# Use custom database location
uv run chunkhound run . --db /path/to/my-chunks.db
uv run chunkhound mcp --db /path/to/my-chunks.db
```

## AI Assistant Setup

### Claude Desktop
Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "chunkhound": {
      "command": "uv",
      "args": ["run", "chunkhound", "mcp"],
      "env": {
        "OPENAI_API_KEY": "sk-your-key-here"
      }
    }
  }
}
```

### Claude Code
Add to `~/.claude.json`:
```json
{
  "mcpServers": {
    "chunkhound": {
      "command": "uv",
      "args": ["run", "chunkhound", "mcp"],
      "env": {
        "OPENAI_API_KEY": "sk-your-key-here"
      }
    }
  }
}
```

### VS Code
Add to `.vscode/mcp.json` in your project:
```json
{
  "servers": {
    "chunkhound": {
      "command": "uv",
      "args": ["run", "chunkhound", "mcp"]
    }
  }
}
```

### Cursor
Add to `.cursor/mcp.json` in your project:
```json
{
  "chunkhound": {
    "command": "uv",
    "args": ["run", "chunkhound", "mcp"]
  }
}
```

## What You Get

- **Semantic search** - "Find database connection code"
- **Regex search** - Find exact patterns like `async def.*error`
- **Code context** - AI assistants understand your codebase structure
- **Multi-language** - Python, TypeScript, Java, C#, JavaScript, Groovy, Kotlin, Go, Rust, C, C++, Matlab, Bash, Makefile, Markdown, JSON, YAML, TOML

## Language Support

| Language | Extensions | Extracted Elements |
|----------|------------|-------------------|
| **Python** | `.py` | Functions, classes, methods, async functions |
| **Java** | `.java` | Classes, methods, interfaces, constructors |
| **C#** | `.cs` | Classes, methods, interfaces, properties |
| **TypeScript** | `.ts`, `.tsx` | Functions, classes, interfaces, React components |
| **JavaScript** | `.js`, `.jsx` | Functions, classes, React components |
| **Groovy** | `.groovy`, `.gvy`, `.gy` | Classes, methods, closures, traits, enums, scripts |
| **Kotlin** | `.kt`, `.kts` | Classes, objects, functions, properties, data classes, extension functions |
| **Go** | `.go` | Functions, methods, structs, interfaces, type declarations, variables, constants |
| **Rust** | `.rs` | Functions, methods, structs, enums, traits, implementations, modules, macros, constants, statics, type aliases |
| **C** | `.c`, `.h` | Functions, structs, unions, enums, variables, typedefs, macros |
| **C++** | `.cpp`, `.cxx`, `.cc`, `.hpp`, `.hxx`, `.h++` | Classes, functions, namespaces, templates, enums, variables, type aliases, macros |
| **Matlab** | `.m` | Functions, classes, methods, scripts, nested functions |
| **Bash** | `.sh`, `.bash`, `.zsh` | Functions, control structures, complex commands |
| **Makefile** | `Makefile`, `makefile`, `GNUmakefile`, `.mk`, `.make` | Targets, rules, variables, recipes |
| **Markdown** | `.md`, `.markdown` | Headers, code blocks, documentation |
| **JSON** | `.json` | Structure and data elements |
| **YAML** | `.yaml`, `.yml` | Configuration and data elements |
| **TOML** | `.toml` | Tables, key-value pairs, arrays, inline tables |
| **Text** | `.txt` | Plain text content |

## Usage Modes

ChunkHound operates in two main modes:

1. **MCP Server Mode** (`chunkhound mcp`) - Recommended for AI assistants
   - Automatically watches for file changes
   - Responds to search queries via MCP protocol
   - Runs continuously in background

2. **Standalone Mode** (`chunkhound run`)
   - One-time indexing: `chunkhound run .`
   - Continuous watching: `chunkhound run . --watch`
   - Direct CLI usage without MCP integration

## Configuration

### Database Location

By default, ChunkHound creates `chunkhound.db` in your current directory. You can customize this with:

- **Command line**: `--db /path/to/my-chunks.db`
- **Environment variable**: `CHUNKHOUND_DB_PATH="/path/to/chunkhound.db"`

### Embedding Providers

ChunkHound supports multiple embedding providers:

**OpenAI (default)**:
```bash
export OPENAI_API_KEY="sk-your-key-here"
uv run chunkhound run . --provider openai --model text-embedding-3-small
```

**OpenAI-compatible servers** (Ollama, LocalAI, etc.):
```bash
uv run chunkhound run . --provider openai-compatible --base-url http://localhost:11434 --model nomic-embed-text
```

**Text Embeddings Inference (TEI)**:
```bash
uv run chunkhound run . --provider tei --base-url http://localhost:8080
```

### Environment Variables
```bash
# Required for semantic search (OpenAI)
export OPENAI_API_KEY="sk-your-key-here"

# Optional: Database location
export CHUNKHOUND_DB_PATH="/path/to/chunkhound.db"

# Optional: Custom embedding model
export CHUNKHOUND_EMBEDDING_MODEL="text-embedding-3-small"

# Optional: Custom base URL for compatible providers
export CHUNKHOUND_BASE_URL="http://localhost:11434"
```

## Requirements

- **Python**: 3.10+
- **OpenAI API key**: Required for semantic search (regex works without)

## How It Works

1. **Scan** - Finds code files in your project
2. **Parse** - Extracts functions, classes, methods using tree-sitter
3. **Index** - Stores code chunks in local DuckDB database
4. **Embed** - Creates AI embeddings for semantic search
5. **Watch** - MCP server automatically monitors files for changes and re-indexes
6. **Search** - AI assistants query via MCP protocol

*Note: ChunkHound currently uses DuckDB. Support for other local and remote databases is planned.*

## Origin Story

*Built completely by a language model with human supervision.*

ChunkHound was assembled by an AI coding agent in under three weeks through a self-improving process: design → code → test → review → commit. The agent even used ChunkHound to search its own code while building it.

## License

MIT
