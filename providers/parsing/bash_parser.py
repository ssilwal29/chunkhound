"""Bash language parser provider implementation for ChunkHound using tree-sitter."""

import time
from pathlib import Path
from typing import Any

from loguru import logger

from core.types import ChunkType
from core.types import Language as CoreLanguage
from interfaces.language_parser import ParseConfig, ParseResult

try:
    from tree_sitter import Language as TSLanguage
    from tree_sitter import Node as TSNode
    from tree_sitter import Parser as TSParser
    from tree_sitter_language_pack import get_language, get_parser
    BASH_AVAILABLE = True
except ImportError:
    BASH_AVAILABLE = False
    get_language = None
    get_parser = None
    TSLanguage = None
    TSParser = None
    TSNode = None

# Try direct import as fallback
try:
    import tree_sitter_bash as ts_bash
    BASH_DIRECT_AVAILABLE = True
except ImportError:
    BASH_DIRECT_AVAILABLE = False
    ts_bash = None


class BashParser:
    """Bash language parser using tree-sitter."""

    def __init__(self, config: ParseConfig | None = None):
        """Initialize Bash parser.

        Args:
            config: Optional parse configuration
        """
        self._language = None
        self._parser = None
        self._initialized = False

        # Default configuration for Bash-specific chunk types
        self._config = config or ParseConfig(
            language=CoreLanguage.BASH,
            chunk_types={ChunkType.FUNCTION, ChunkType.BLOCK},
            max_chunk_size=8000,
            min_chunk_size=100,
            include_imports=True,
            include_comments=False,
            include_docstrings=True,
            max_depth=10,
            use_cache=True,
        )

        # Initialize parser - crash if dependencies unavailable
        if not BASH_AVAILABLE and not BASH_DIRECT_AVAILABLE:
            raise ImportError("Bash tree-sitter dependencies not available - install tree-sitter-language-pack or tree-sitter-bash")
        
        if not self._initialize():
            raise RuntimeError("Failed to initialize Bash parser")

    def _initialize(self) -> bool:
        """Initialize the Bash parser.

        Returns:
            True if initialization successful, False otherwise
        """
        if self._initialized:
            return True

        if not BASH_AVAILABLE and not BASH_DIRECT_AVAILABLE:
            logger.error("Bash tree-sitter support not available")
            return False

        # Try direct import first
        try:
            if BASH_DIRECT_AVAILABLE and ts_bash and TSLanguage and TSParser:
                self._language = TSLanguage(ts_bash.language())
                self._parser = TSParser(self._language)
                self._initialized = True
                logger.debug("Bash parser initialized successfully (direct)")
                return True
        except Exception as e:
            logger.debug(f"Direct Bash parser initialization failed: {e}")

        # Fallback to language pack
        try:
            if BASH_AVAILABLE and get_language and get_parser:
                self._language = get_language('bash')
                self._parser = get_parser('bash')
                self._initialized = True
                logger.debug("Bash parser initialized successfully (language pack)")
                return True
        except Exception as e:
            logger.error(f"Bash parser language pack initialization failed: {e}")

        logger.error("Bash parser initialization failed with both methods")
        return False

    @property
    def language(self) -> CoreLanguage:
        """Programming language this parser handles."""
        return CoreLanguage.BASH

    @property
    def supported_chunk_types(self) -> set[ChunkType]:
        """Chunk types this parser can extract."""
        return self._config.chunk_types

    @property
    def is_available(self) -> bool:
        """Whether the parser is available and ready to use."""
        return (BASH_AVAILABLE or BASH_DIRECT_AVAILABLE) and self._initialized

    def _get_node_text(self, node: TSNode, source: str) -> str:
        """Extract text content from a tree-sitter node."""
        return source[node.start_byte:node.end_byte]

    def parse_file(self, file_path: Path, source: str | None = None) -> ParseResult:
        """Parse a Bash file and extract semantic chunks.

        Args:
            file_path: Path to Bash file
            source: Optional source code string

        Returns:
            ParseResult with extracted chunks and metadata
        """
        start_time = time.time()
        chunks = []
        errors = []
        warnings = []

        if not self.is_available:
            errors.append("Bash parser not available")
            return ParseResult(
                chunks=chunks,
                language=self.language,
                total_chunks=0,
                parse_time=time.time() - start_time,
                errors=errors,
                warnings=warnings,
                metadata={"file_path": str(file_path)}
            )

        try:
            # Read source if not provided
            if source is None:
                with open(file_path, encoding='utf-8') as f:
                    source = f.read()

            # Parse with tree-sitter
            if self._parser is None:
                errors.append("Bash parser not initialized")
                return ParseResult(
                    chunks=chunks,
                    language=self.language,
                    total_chunks=0,
                    parse_time=time.time() - start_time,
                    errors=errors,
                    warnings=warnings,
                    metadata={"file_path": str(file_path)}
                )

            tree = self._parser.parse(bytes(source, 'utf8'))

            # Extract semantic units
            chunks = self._extract_chunks(tree.root_node, source, file_path)

            logger.debug(f"Extracted {len(chunks)} chunks from {file_path}")

        except Exception as e:
            error_msg = f"Failed to parse Bash file {file_path}: {e}"
            logger.error(error_msg)
            errors.append(error_msg)

        return ParseResult(
            chunks=chunks,
            language=self.language,
            total_chunks=len(chunks),
            parse_time=time.time() - start_time,
            errors=errors,
            warnings=warnings,
            metadata={"file_path": str(file_path)}
        )

    def _extract_chunks(
        self, tree_node: TSNode, source: str, file_path: Path
    ) -> list[dict[str, Any]]:
        """Extract semantic chunks from Bash AST.

        Args:
            tree_node: Root AST node
            source: Source code string
            file_path: Path to source file

        Returns:
            List of extracted chunks
        """
        chunks = []

        if not self.is_available:
            logger.warning("Bash parser not available, falling back to text parsing")
            return self._extract_fallback_chunks(source, file_path)

        try:
            self._traverse_node(tree_node, source, chunks, file_path)
            return chunks
        except Exception as e:
            logger.error(f"Failed to extract Bash chunks: {e}")
            return self._extract_fallback_chunks(source, file_path)

    def _traverse_node(
        self,
        node: TSNode,
        source: str,
        chunks: list[dict[str, Any]],
        file_path: Path,
        depth: int = 0,
    ) -> None:
        """Traverse AST nodes recursively to extract chunks.

        Args:
            node: Current AST node
            source: Source code string
            chunks: List to append chunks to
            file_path: Path to source file
            depth: Current traversal depth
        """
        if depth > self._config.max_depth:
            return

        node_type = node.type

        # Extract different types of Bash constructs
        if node_type == "function_definition":
            self._extract_function(node, source, chunks, file_path)
        elif node_type in [
            "if_statement",
            "while_statement",
            "for_statement",
            "case_statement",
        ]:
            self._extract_control_structure(node, source, chunks, file_path, node_type)
        elif node_type == "command":
            self._extract_command(node, source, chunks, file_path)
        elif node_type == "variable_assignment":
            self._extract_variable_assignment(node, source, chunks, file_path)

        # Continue traversing child nodes
        for child in node.children:
            self._traverse_node(child, source, chunks, file_path, depth + 1)

    def _extract_function(
        self, node: TSNode, source: str, chunks: list[dict[str, Any]], file_path: Path
    ) -> None:
        """Extract function definitions from Bash scripts.

        Args:
            node: Function definition node
            source: Source code string
            chunks: List to append chunks to
            file_path: Path to source file
        """
        try:
            start_line = node.start_point[0] + 1
            end_line = node.end_point[0] + 1
            chunk_text = self._get_node_text(node, source)

            # Extract function name
            function_name = "anonymous_function"
            for child in node.children:
                if child.type == "word":
                    function_name = self._get_node_text(child, source)
                    break

            if self._should_include_chunk(chunk_text, ChunkType.FUNCTION):
                chunks.append(
                    {
                        "symbol": function_name,
                        "name": function_name,
                        "display_name": function_name,
                        "chunk_type": ChunkType.FUNCTION.value,
                        "start_line": start_line,
                        "end_line": end_line,
                        "path": str(file_path),
                        "language": "bash",
                        "content": chunk_text,
                        "code": chunk_text,
                        "start_byte": node.start_byte,
                        "end_byte": node.end_byte,
                    }
                )

        except Exception as e:
            logger.debug(f"Failed to extract Bash function: {e}")

    def _extract_control_structure(
        self,
        node: TSNode,
        source: str,
        chunks: list[dict[str, Any]],
        file_path: Path,
        structure_type: str,
    ) -> None:
        """Extract control structures (if, while, for, case) from Bash scripts.

        Args:
            node: Control structure node
            source: Source code string
            chunks: List to append chunks to
            file_path: Path to source file
            structure_type: Type of control structure
        """
        try:
            start_line = node.start_point[0] + 1
            end_line = node.end_point[0] + 1
            chunk_text = self._get_node_text(node, source)

            if self._should_include_chunk(chunk_text, ChunkType.BLOCK):
                chunks.append(
                    {
                        "symbol": f"{structure_type}_{start_line}",
                        "name": f"{structure_type}_{start_line}",
                        "chunk_type": ChunkType.BLOCK,
                        "start_line": start_line,
                        "end_line": end_line,
                        "file_path": str(file_path),
                        "language": self.language.value,
                        "line_count": end_line - start_line + 1,
                        "code": chunk_text,
                    }
                )

        except Exception as e:
            logger.debug(f"Failed to extract Bash control structure: {e}")

    def _extract_command(
        self, node: TSNode, source: str, chunks: list[dict[str, Any]], file_path: Path
    ) -> None:
        """Extract command invocations from Bash scripts.

        Args:
            node: Command node
            source: Source code string
            chunks: List to append chunks to
            file_path: Path to source file
        """
        try:
            # Only extract multi-line commands or complex command pipelines
            start_line = node.start_point[0] + 1
            end_line = node.end_point[0] + 1

            if end_line - start_line < 1:  # Skip single-line simple commands
                return

            chunk_text = self._get_node_text(node, source)

            if self._should_include_chunk(chunk_text, ChunkType.BLOCK):
                chunks.append(
                    {
                        "symbol": f"command_{start_line}",
                        "name": f"command_{start_line}",
                        "chunk_type": ChunkType.BLOCK,
                        "start_line": start_line,
                        "end_line": end_line,
                        "file_path": str(file_path),
                        "language": self.language.value,
                        "line_count": end_line - start_line + 1,
                        "code": chunk_text,
                    }
                )

        except Exception as e:
            logger.debug(f"Failed to extract Bash command: {e}")

    def _extract_variable_assignment(
        self, node: TSNode, source: str, chunks: list[dict[str, Any]], file_path: Path
    ) -> None:
        """Extract variable assignments from Bash scripts.

        Args:
            node: Variable assignment node
            source: Source code string
            chunks: List to append chunks to
            file_path: Path to source file
        """
        try:
            # Only extract complex variable assignments (multi-line or cmd substitution)
            start_line = node.start_point[0] + 1
            end_line = node.end_point[0] + 1
            chunk_text = self._get_node_text(node, source)

            # Check if it's a complex assignment worth indexing
            if (
                "$(" in chunk_text or "`" in chunk_text or end_line > start_line
            ) and self._should_include_chunk(chunk_text, ChunkType.BLOCK):
                # Extract variable name
                var_name = "variable"
                for child in node.children:
                    if child.type == "variable_name":
                        var_name = self._get_node_text(child, source)
                        break

                chunks.append(
                    {
                        "symbol": f"var_{var_name}_{start_line}",
                        "name": f"var_{var_name}_{start_line}",
                        "chunk_type": ChunkType.BLOCK,
                        "start_line": start_line,
                        "end_line": end_line,
                        "file_path": str(file_path),
                        "language": self.language.value,
                        "line_count": end_line - start_line + 1,
                        "code": chunk_text,
                    }
                )

        except Exception as e:
            logger.debug(f"Failed to extract Bash variable assignment: {e}")

    def _should_include_chunk(self, chunk_text: str, chunk_type: ChunkType) -> bool:
        """Determine if a chunk should be included based on size and content.

        Args:
            chunk_text: The chunk content
            chunk_type: Type of chunk

        Returns:
            True if chunk should be included
        """
        if not chunk_text or not chunk_text.strip():
            return False

        # Check size constraints
        if len(chunk_text) < self._config.min_chunk_size:
            return False
        if len(chunk_text) > self._config.max_chunk_size:
            return False

        # Check if chunk type is enabled
        if chunk_type not in self._config.chunk_types:
            return False

        return True

    def _get_node_text(self, node: TSNode, source: str) -> str:
        """Extract text content from a tree-sitter node."""
        return source[node.start_byte : node.end_byte]

    def _extract_fallback_chunks(
        self, source: str, file_path: Path
    ) -> list[dict[str, Any]]:
        """Fallback text-based extraction when tree-sitter fails."""
        chunks = []
        lines = source.split("\n")

        # Simple pattern-based extraction for functions
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith("function ") or (
                "()" in stripped and "{" in stripped
            ):
                # Found a function-like pattern
                chunks.append(
                    {
                        "symbol": f"function_{i + 1}",
                        "name": f"function_{i + 1}",
                        "chunk_type": ChunkType.FUNCTION,
                        "start_line": i + 1,
                        "end_line": i + 1,
                        "file_path": str(file_path),
                        "language": self.language.value,
                        "line_count": 1,
                        "code": line,
                    }
                )

        return chunks

