# ChunkHound

**Semantic and Regex search for your codebase via MCP.**

Enable AI assistants to search your code with natural language and regex patterns.

## Installation

### Python Package
```bash
# Install with uv (recommended)
uv tool install chunkhound

# Or with pip
pip install chunkhound
```

### Binary
Download from [GitHub Releases](https://github.com/ofriw/chunkhound/releases) - zero dependencies required.

## Quick Start

```bash
# Index your codebase
chunkhound run .

# Start MCP server for AI assistants
chunkhound mcp
```

## AI Assistant Setup

### Claude Desktop
Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "chunkhound": {
      "command": "chunkhound",
      "args": ["mcp"],
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
      "command": "chunkhound",
      "args": ["mcp"]
    }
  }
}
```

### Cursor
Add to `.cursor/mcp.json` in your project:
```json
{
  "chunkhound": {
    "command": "chunkhound",
    "args": ["mcp"]
  }
}
```

## What You Get

- **Semantic search** - "Find database connection code"
- **Regex search** - Find exact patterns like `async def.*error`
- **Code context** - AI assistants understand your codebase structure
- **Multi-language** - Python, TypeScript, Java, C#, JavaScript, Markdown

## Language Support

| Language | Extensions | Extracted Elements |
|----------|------------|-------------------|
| **Python** | `.py` | Functions, classes, methods, async functions |
| **Java** | `.java` | Classes, methods, interfaces, constructors |
| **C#** | `.cs` | Classes, methods, interfaces, properties |
| **TypeScript** | `.ts`, `.tsx` | Functions, classes, interfaces, React components |
| **JavaScript** | `.js`, `.jsx` | Functions, classes, React components |
| **Markdown** | `.md` | Headers, code blocks, documentation |

## Configuration

### Environment Variables
```bash
# Required for semantic search
export OPENAI_API_KEY="sk-your-key-here"

# Optional: Database location
export CHUNKHOUND_DB_PATH="/path/to/chunkhound.db"

# Optional: Custom embedding model
export CHUNKHOUND_EMBEDDING_MODEL="text-embedding-3-small"
```

## Requirements

- **Python**: 3.10+
- **OpenAI API key**: Required for semantic search (regex works without)
- **Platforms**: macOS, Linux

## How It Works

1. **Scan** - Finds code files in your project
2. **Parse** - Extracts functions, classes, methods using tree-sitter
3. **Index** - Stores code chunks in local SQLite database
4. **Embed** - Creates AI embeddings for semantic search
5. **Search** - AI assistants query via MCP protocol

## Origin Story

*Built completely by a language model with human supervision.*

ChunkHound was assembled by an AI coding agent in two weeks through a self-improving process: design → code → test → review → commit. The agent even used ChunkHound to search its own code while building it.

## License

MIT
