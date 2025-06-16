# ChunkHound

**Semantic and Regex search for your projects via MCP.**

Semantic and Regex search for your projects via MCP.Built end‑to‑end by a language model, from the project name to the last line of code.

# How ChunkHound Was Born

In May 2025 a single LLM, steered only by carefully crafted prompts, bootstrapped the entire ChunkHound code‑base in two weeks:
- **Persistent memory** — the agent wrote to its own knowledge store after every step so future calls could pick up where it left off.

- **Pipeline of “stations”** — development was treated like a factory line. Each template prompt (“design”, “code”, “test”, “review”, …) did one job and handed the artefact to the next, with a human only reviewing and giving a thumbs‑up.

- **Self‑indexing feedback loop** — as soon as minimal indexing worked the agent pointed ChunkHound at its own repo, letting it search, reason about and refactor its code faster on every pass.

- **Autonomous QA via MCP** — once the code was searchable through MCP, the agent ran scripted queries against its own API, spotting and fixing issues without human help.

The result is the tool you are reading about — and the README you are reading now — all produced without a human writing a single character by hand.

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
