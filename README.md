# ChunkHound

**Semantic and Regex search for your projects via MCP.**

*Built completely by a language model with human supervision.*

# How ChunkHound Was Born

In May 2025 an LLM coding agent assembled the first working version of ChunkHound in about two weeks. Development ran through a repeatable set of prompt‑"stations":
- **Persistent memory** — each step wrote notes for the next.

- **Pipeline of “stations”** — design → code → test → review → commit, one or more prompts per task.

- **Self‑indexing feedback loop** — once basic indexing worked, the agent queried its own repo using ChunkHound and refined the code.

- **Autonomous QA via [MCP](https://modelcontextprotocol.io)** — scripted searches exercised the API and revealed bugs.

All code and docs, including this README, were generated this way; the human role was limited to approval, review and steering the project in the right direction.

## Quick Start

```bash
# Install (after PyPI release)
pip install chunkhound

# Or install with uv
uv add chunkhound

# Index your code
chunkhound run .

# Start search server for AI assistants
chunkhound mcp
```

That's it! Your code is now searchable by AI assistants.

## What It Does

- **Indexes your code** - Finds functions, classes, and methods automatically
- **Regex search** - Find exact patterns like `def.*async`
- **Semantic search** - Ask questions like "How do I connect to the database?"
- **Works with AI assistants** - Claude, Cursor, VS Code, etc.
- **Multi-language support** - Python, Java, C#, TypeScript, JavaScript, and Markdown

## AI Assistant Setup
```json
{
  "mcpServers": {
    "chunkhound": {
      "command": "chunkhound",
      "args": ["mcp"],
      "env": {
        "OPENAI_API_KEY": "your-openai-key-here"
      }
    }
  }
}
```

## How It Works

1. **Scan** - ChunkHound reads your Python, Java, C#, TypeScript, JavaScript, and Markdown files
2. **Parse** - Extracts functions, classes, methods using tree-sitter
3. **Index** - Stores code chunks in a local database
4. **Embed** - Creates AI embeddings for semantic search (optional)
5. **Search** - AI assistants can now search your code

## Requirements

- **Python Package**: Python 3.10+
- **Standalone Binary**: No requirements (zero dependencies)
- OpenAI API key (optional, for semantic search)
- Works on macOS and Linux

## Language Support

ChunkHound provides comprehensive parsing and indexing with **tree-sitter** for accurate syntax analysis:

### Supported Languages

| Language | Extensions | Extracted Elements | Status |
|----------|------------|-------------------|---------|
| **Python** | `.py` | Functions, classes, methods, decorators, async functions | ✅ Full |
| **Java** | `.java` | Classes, methods, interfaces, packages, constructors | ✅ Full |
| **C#** | `.cs` | Classes, methods, interfaces, namespaces, properties, events | ✅ Full |
| **TypeScript** | `.ts`, `.tsx` | Functions, classes, interfaces, types, enums, React components | ✅ Full |
| **JavaScript** | `.js`, `.jsx`, `.mjs`, `.cjs` | Functions, classes, modules, React components, arrow functions | ✅ Full |
| **Markdown** | `.md` | Headers, code blocks, structured content, documentation | ✅ Full |

### Advanced Features

- **Tree-sitter parsing** - Accurate syntax analysis with proper AST generation
- **Incremental parsing** - Only reparse changed files for fast updates
- **Symbol extraction** - Precise code structure with scope and context
- **Cross-language search** - Find patterns across all supported file types
- **React/JSX support** - Full component and hook extraction
- **Async/await patterns** - Modern JavaScript and Python async code
- **Generics support** - TypeScript and C# generic type extraction

## License

MIT
