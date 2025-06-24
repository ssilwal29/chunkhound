"""C language parser provider implementation for ChunkHound using tree-sitter."""

from pathlib import Path
from typing import Any

from loguru import logger

from core.types import ChunkType
from core.types import Language as CoreLanguage
from interfaces.language_parser import ParseConfig
from providers.parsing.base_parser import TreeSitterParserBase

try:
    import tree_sitter_c
    from tree_sitter import Language, Parser
    from tree_sitter import Node as TSNode
    TREE_SITTER_AVAILABLE = True
except ImportError:
    TREE_SITTER_AVAILABLE = False
    TSNode = None
    Language = None
    Parser = None
    tree_sitter_c = None


class CParser(TreeSitterParserBase):
    """C language parser using tree-sitter."""

    def __init__(self, config: ParseConfig | None = None):
        """Initialize C parser.

        Args:
            config: Optional parse configuration
        """
        super().__init__(CoreLanguage.C, config)

    def _initialize(self) -> bool:
        """Initialize the C parser using direct tree-sitter-c package.

        Returns:
            True if initialization successful, False otherwise
        """
        if self._initialized:
            return True

        if not TREE_SITTER_AVAILABLE or tree_sitter_c is None:
            logger.error("C tree-sitter support not available")
            return False

        try:
            # Use direct tree-sitter-c instead of language pack
            self._language = Language(tree_sitter_c.language())
            self._parser = Parser(self._language)
            self._initialized = True
            logger.debug("C parser initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize C parser: {e}")
            return False

    def _get_default_config(self) -> ParseConfig:
        """Get default configuration for C parser."""
        return ParseConfig(
            language=CoreLanguage.C,
            chunk_types={
                ChunkType.FUNCTION,
                ChunkType.CLASS,  # structs/unions mapped to class
                ChunkType.ENUM,
                ChunkType.VARIABLE,
                ChunkType.TYPE,
                ChunkType.MACRO,
            },
            max_chunk_size=8000,
            min_chunk_size=100,
            include_imports=True,
            include_comments=False,
            include_docstrings=True,
            max_depth=10,
            use_cache=True
        )

    def _extract_chunks(
        self, tree_node: TSNode, source: str, file_path: Path
    ) -> list[dict[str, Any]]:
        """Extract semantic chunks from C AST.

        Args:
            tree_node: Root AST node
            source: Source code string
            file_path: Path to source file

        Returns:
            List of extracted chunks
        """
        chunks = []

        if not self.is_available:
            return chunks

        try:
            # Extract different chunk types based on configuration
            if ChunkType.FUNCTION in self._config.chunk_types:
                chunks.extend(
                    self._extract_functions(tree_node, source, file_path)
                )

            if ChunkType.CLASS in self._config.chunk_types:
                chunks.extend(
                    self._extract_structs_unions(tree_node, source, file_path)
                )

            if ChunkType.ENUM in self._config.chunk_types:
                chunks.extend(
                    self._extract_enums(tree_node, source, file_path)
                )

            if ChunkType.VARIABLE in self._config.chunk_types:
                chunks.extend(
                    self._extract_variables(tree_node, source, file_path)
                )

            if ChunkType.TYPE in self._config.chunk_types:
                chunks.extend(
                    self._extract_typedefs(tree_node, source, file_path)
                )

            if ChunkType.MACRO in self._config.chunk_types:
                chunks.extend(
                    self._extract_macros(tree_node, source, file_path)
                )

        except Exception as e:
            logger.error(f"Failed to extract C chunks: {e}")

        return chunks

    def _extract_functions(
        self, tree_node: TSNode, source: str, file_path: Path
    ) -> list[dict[str, Any]]:
        """Extract C function definitions from AST."""
        chunks = []

        try:
            if self._language is None:
                return chunks

            # Query for function definitions
            query = self._language.query("""
                (function_definition
                    declarator: (function_declarator
                        declarator: (identifier) @function_name
                    )
                ) @function_def
            """)

            matches = query.matches(tree_node)

            for pattern_index, captures in matches:
                if "function_def" not in captures or "function_name" not in captures:
                    continue

                function_node = captures["function_def"][0]
                function_name_node = captures["function_name"][0]
                function_name = self._get_node_text(function_name_node, source)

                chunk = self._create_chunk(
                    function_node, source, file_path, ChunkType.FUNCTION,
                    function_name, function_name
                )

                chunks.append(chunk)

        except Exception as e:
            logger.error(f"Failed to extract C functions: {e}")

        return chunks

    def _extract_structs_unions(
        self, tree_node: TSNode, source: str, file_path: Path
    ) -> list[dict[str, Any]]:
        """Extract C struct and union definitions from AST."""
        chunks = []

        try:
            if self._language is None:
                return chunks

            # Query for struct and union declarations
            query = self._language.query("""
                (struct_specifier
                    name: (type_identifier) @struct_name
                ) @struct_def

                (union_specifier
                    name: (type_identifier) @union_name
                ) @union_def
            """)

            matches = query.matches(tree_node)

            for pattern_index, captures in matches:
                struct_node = None
                struct_name = None

                # Handle structs
                if "struct_def" in captures and "struct_name" in captures:
                    struct_node = captures["struct_def"][0]
                    struct_name_node = captures["struct_name"][0]
                    struct_name = f"struct {self._get_node_text(struct_name_node, source)}"

                # Handle unions
                elif "union_def" in captures and "union_name" in captures:
                    struct_node = captures["union_def"][0]
                    union_name_node = captures["union_name"][0]
                    struct_name = f"union {self._get_node_text(union_name_node, source)}"

                if not struct_node or not struct_name:
                    continue

                chunk = self._create_chunk(
                    struct_node, source, file_path, ChunkType.CLASS,
                    struct_name, struct_name
                )

                chunks.append(chunk)

        except Exception as e:
            logger.error(f"Failed to extract C structs/unions: {e}")

        return chunks

    def _extract_enums(
        self, tree_node: TSNode, source: str, file_path: Path
    ) -> list[dict[str, Any]]:
        """Extract C enum definitions from AST."""
        chunks = []

        try:
            if self._language is None:
                return chunks

            query = self._language.query("""
                (enum_specifier
                    name: (type_identifier) @enum_name
                ) @enum_def
            """)

            matches = query.matches(tree_node)

            for pattern_index, captures in matches:
                if "enum_def" not in captures or "enum_name" not in captures:
                    continue

                enum_node = captures["enum_def"][0]
                enum_name_node = captures["enum_name"][0]
                enum_name = f"enum {self._get_node_text(enum_name_node, source)}"

                chunk = self._create_chunk(
                    enum_node, source, file_path, ChunkType.ENUM,
                    enum_name, enum_name
                )

                chunks.append(chunk)

        except Exception as e:
            logger.error(f"Failed to extract C enums: {e}")

        return chunks

    def _extract_variables(
        self, tree_node: TSNode, source: str, file_path: Path
    ) -> list[dict[str, Any]]:
        """Extract C global variable declarations from AST."""
        chunks = []

        try:
            if self._language is None:
                return chunks

            # Query for global variable declarations (not inside functions/structs)
            query = self._language.query("""
                (translation_unit
                    (declaration
                        declarator: (init_declarator
                            declarator: (identifier) @var_name
                        )
                    ) @var_def
                )

                (translation_unit
                    (declaration
                        declarator: (identifier) @var_name
                    ) @var_def
                )
            """)

            matches = query.matches(tree_node)

            for pattern_index, captures in matches:
                if "var_def" not in captures or "var_name" not in captures:
                    continue

                var_node = captures["var_def"][0]
                var_name_node = captures["var_name"][0]
                var_name = self._get_node_text(var_name_node, source)

                chunk = self._create_chunk(
                    var_node, source, file_path, ChunkType.VARIABLE,
                    var_name, var_name
                )

                chunks.append(chunk)

        except Exception as e:
            logger.error(f"Failed to extract C variables: {e}")

        return chunks

    def _extract_typedefs(
        self, tree_node: TSNode, source: str, file_path: Path
    ) -> list[dict[str, Any]]:
        """Extract C typedef declarations from AST."""
        chunks = []

        try:
            if self._language is None:
                return chunks

            query = self._language.query("""
                (type_definition
                    declarator: (type_identifier) @typedef_name
                ) @typedef_def
            """)

            matches = query.matches(tree_node)

            for pattern_index, captures in matches:
                if "typedef_def" not in captures or "typedef_name" not in captures:
                    continue

                typedef_node = captures["typedef_def"][0]
                typedef_name_node = captures["typedef_name"][0]
                typedef_name = f"typedef {self._get_node_text(typedef_name_node, source)}"

                chunk = self._create_chunk(
                    typedef_node, source, file_path, ChunkType.TYPE,
                    typedef_name, typedef_name
                )

                chunks.append(chunk)

        except Exception as e:
            logger.error(f"Failed to extract C typedefs: {e}")

        return chunks

    def _extract_macros(
        self, tree_node: TSNode, source: str, file_path: Path
    ) -> list[dict[str, Any]]:
        """Extract C preprocessor macro definitions from AST."""
        chunks = []

        try:
            if self._language is None:
                return chunks

            # Query for preprocessor definitions
            query = self._language.query("""
                (preproc_def
                    name: (identifier) @macro_name
                ) @macro_def

                (preproc_function_def
                    name: (identifier) @func_macro_name
                ) @func_macro_def
            """)

            matches = query.matches(tree_node)

            for pattern_index, captures in matches:
                macro_node = None
                macro_name = None

                # Handle simple macros
                if "macro_def" in captures and "macro_name" in captures:
                    macro_node = captures["macro_def"][0]
                    macro_name_node = captures["macro_name"][0]
                    macro_name = f"#define {self._get_node_text(macro_name_node, source)}"

                # Handle function-like macros
                elif "func_macro_def" in captures and "func_macro_name" in captures:
                    macro_node = captures["func_macro_def"][0]
                    func_macro_name_node = captures["func_macro_name"][0]
                    macro_name = f"#define {self._get_node_text(func_macro_name_node, source)}(...)"

                if not macro_node or not macro_name:
                    continue

                chunk = self._create_chunk(
                    macro_node, source, file_path, ChunkType.MACRO,
                    macro_name, macro_name
                )

                chunks.append(chunk)

        except Exception as e:
            logger.error(f"Failed to extract C macros: {e}")

        return chunks