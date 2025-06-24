"""Bash language parser provider implementation for ChunkHound using tree-sitter."""

from pathlib import Path
from typing import Any

from loguru import logger

from core.types import ChunkType
from core.types import Language as CoreLanguage
from interfaces.language_parser import ParseConfig
from providers.parsing.base_parser import TreeSitterParserBase

try:
    from tree_sitter import Language, Parser
    from tree_sitter import Node as TSNode
    from tree_sitter_language_pack import get_language, get_parser

    TREE_SITTER_AVAILABLE = True
except ImportError:
    TREE_SITTER_AVAILABLE = False
    TSNode = None
    Language = None
    Parser = None
    get_language = None
    get_parser = None


class BashParser(TreeSitterParserBase):
    """Bash language parser using tree-sitter."""

    def __init__(self, config: ParseConfig | None = None):
        """Initialize Bash parser.

        Args:
            config: Optional parse configuration
        """
        super().__init__(CoreLanguage.BASH, config)

    def _initialize(self) -> bool:
        """Initialize the Bash parser using tree-sitter-bash package.

        Returns:
            True if initialization successful, False otherwise
        """
        if self._initialized:
            return True

        if not TREE_SITTER_AVAILABLE or get_language is None:
            logger.error("Bash tree-sitter support not available")
            return False

        try:
            self._language = get_language("bash")
            self._parser = get_parser("bash")
            self._initialized = True
            logger.debug("Bash parser initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Bash parser: {e}")
            return False

    def _get_default_config(self) -> ParseConfig:
        """Get default configuration for Bash parser."""
        return ParseConfig(
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
                        "name": function_name,
                        "chunk_type": ChunkType.FUNCTION,
                        "start_line": start_line,
                        "end_line": end_line,
                        "file_path": str(file_path),
                        "language": self.language.value,
                        "line_count": end_line - start_line + 1,
                        "code": chunk_text,
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

