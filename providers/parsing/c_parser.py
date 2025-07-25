"""C language parser provider implementation for ChunkHound using tree-sitter."""

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
    C_AVAILABLE = True
except ImportError:
    C_AVAILABLE = False
    get_language = None
    get_parser = None
    TSLanguage = None
    TSParser = None
    TSNode = None

# Try direct import as fallback
try:
    import tree_sitter_c as ts_c
    C_DIRECT_AVAILABLE = True
except ImportError:
    C_DIRECT_AVAILABLE = False
    ts_c = None


class CParser:
    """C language parser using tree-sitter."""

    def __init__(self, config: ParseConfig | None = None):
        """Initialize C parser.

        Args:
            config: Optional parse configuration
        """
        self._language = None
        self._parser = None
        self._initialized = False

        # Default configuration for C-specific chunk types
        self._config = config or ParseConfig(
            language=CoreLanguage.C,
            chunk_types={
                ChunkType.FUNCTION,
                ChunkType.STRUCT,
                ChunkType.ENUM,
                ChunkType.VARIABLE,
                ChunkType.TYPE,
                ChunkType.MACRO,
                ChunkType.COMMENT,
                ChunkType.DOCSTRING,
            },
            max_chunk_size=8000,
            min_chunk_size=100,
            include_imports=True,
            include_comments=False,
            include_docstrings=True,
            max_depth=10,
            use_cache=True
        )

        # Initialize parser - crash if dependencies unavailable
        if not C_AVAILABLE and not C_DIRECT_AVAILABLE:
            raise ImportError("C tree-sitter dependencies not available - install tree-sitter-language-pack or tree-sitter-c")

        if not self._initialize():
            raise RuntimeError("Failed to initialize C parser")

    def _initialize(self) -> bool:
        """Initialize the C parser.

        Returns:
            True if initialization successful, False otherwise
        """
        if self._initialized:
            return True

        if not C_AVAILABLE and not C_DIRECT_AVAILABLE:
            logger.error("C tree-sitter support not available")
            return False

        # Try direct import first
        try:
            if C_DIRECT_AVAILABLE and ts_c and TSLanguage and TSParser:
                self._language = TSLanguage(ts_c.language())
                self._parser = TSParser(self._language)
                self._initialized = True
                logger.debug("C parser initialized successfully (direct)")
                return True
        except Exception as e:
            logger.debug(f"Direct C parser initialization failed: {e}")

        # Fallback to language pack
        try:
            if C_AVAILABLE and get_language and get_parser:
                self._language = get_language('c')
                self._parser = get_parser('c')
                self._initialized = True
                logger.debug("C parser initialized successfully (language pack)")
                return True
        except Exception as e:
            logger.error(f"C parser language pack initialization failed: {e}")

        logger.error("C parser initialization failed with both methods")
        return False

    @property
    def language(self) -> CoreLanguage:
        """Programming language this parser handles."""
        return CoreLanguage.C

    @property
    def supported_chunk_types(self) -> set[ChunkType]:
        """Chunk types this parser can extract."""
        return self._config.chunk_types

    @property
    def is_available(self) -> bool:
        """Whether the parser is available and ready to use."""
        return (C_AVAILABLE or C_DIRECT_AVAILABLE) and self._initialized

    def _get_node_text(self, node: TSNode, source: str) -> str:
        """Extract text content from a tree-sitter node."""
        return source[node.start_byte:node.end_byte]

    def parse_file(self, file_path: Path, source: str | None = None) -> ParseResult:
        """Parse a C file and extract semantic chunks.

        Args:
            file_path: Path to C file
            source: Optional source code string

        Returns:
            ParseResult with extracted chunks and metadata
        """
        start_time = time.time()
        chunks = []
        errors = []
        warnings = []

        if not self.is_available:
            errors.append("C parser not available")
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
                errors.append("C parser not initialized")
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
            error_msg = f"Failed to parse C file {file_path}: {e}"
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

            # Extract comments and docstrings
            if ChunkType.COMMENT in self._config.chunk_types:
                chunks.extend(
                    self._extract_comments(tree_node, source, file_path)
                )

            if ChunkType.DOCSTRING in self._config.chunk_types:
                chunks.extend(
                    self._extract_docstrings(tree_node, source, file_path)
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

    def _create_chunk(
        self, node: TSNode, source: str, file_path: Path,
        chunk_type: ChunkType, symbol: str, display_name: str
    ) -> dict[str, Any]:
        """Create a chunk dictionary from a tree-sitter node.
        
        Args:
            node: Tree-sitter node
            source: Source code string
            file_path: Path to source file
            chunk_type: Type of chunk
            symbol: Symbol name
            display_name: Display name for the chunk
            
        Returns:
            Chunk dictionary
        """
        content = self._get_node_text(node, source)

        return {
            "symbol": symbol,
            "start_line": node.start_point[0] + 1,
            "end_line": node.end_point[0] + 1,
            "code": content,
            "chunk_type": chunk_type.value,
            "language": "c",
            "path": str(file_path),
            "name": symbol,
            "display_name": display_name,
            "content": content,
            "start_byte": node.start_byte,
            "end_byte": node.end_byte,
        }

    def _extract_comments(self, tree_node: TSNode, source: str, file_path: Path) -> list[dict[str, Any]]:
        """Extract C comments (// and /* */)."""
        comment_patterns = [
            "(comment) @comment"
        ]
        return self._extract_comments_generic(tree_node, source, file_path, comment_patterns)

    def _extract_docstrings(self, tree_node: TSNode, source: str, file_path: Path) -> list[dict[str, Any]]:
        """Extract C documentation comments (/** */)."""
        chunks = []
        
        if self._language is None:
            return chunks
            
        try:
            # Extract documentation comments (/** ... */)
            query = self._language.query("(comment) @comment")
            matches = query.matches(tree_node)
            
            for match in matches:
                pattern_index, captures = match
                
                for capture_name, nodes in captures.items():
                    for node in nodes:
                        comment_text = self._get_node_text(node, source)
                        
                        # Check if it's a documentation comment (starts with /**)
                        if comment_text.strip().startswith("/**"):
                            cleaned_text = self._clean_doc_comment_text(comment_text)
                            symbol = f"doc:{node.start_point[0] + 1}"
                            
                            chunk = self._create_chunk(
                                node=node,
                                source=source,
                                file_path=file_path,
                                chunk_type=ChunkType.DOCSTRING,
                                name=symbol,
                                display_name=f"Documentation at line {node.start_point[0] + 1}",
                                content=cleaned_text
                            )
                            
                            chunks.append(chunk)
                            
        except Exception as e:
            logger.error(f"Failed to extract C docstrings: {e}")
            
        return chunks

    def _clean_doc_comment_text(self, text: str) -> str:
        """Clean documentation comment text by removing /** */ markers and * prefixes."""
        cleaned = text.strip()
        
        # Remove /** */ markers
        if cleaned.startswith("/**") and cleaned.endswith("*/"):
            cleaned = cleaned[3:-2]
        
        # Remove leading * from each line
        lines = cleaned.split('\n')
        cleaned_lines = []
        for line in lines:
            line = line.strip()
            if line.startswith('*'):
                line = line[1:].lstrip()
            cleaned_lines.append(line)
            
        return '\n'.join(cleaned_lines).strip()

    def _extract_comments_generic(self, tree_node: TSNode, source: str, file_path: Path, 
                                 comment_patterns: list[str]) -> list[dict[str, Any]]:
        """Extract comments using generic patterns."""
        chunks = []
        
        if not comment_patterns or self._language is None:
            return chunks
            
        try:
            for pattern in comment_patterns:
                query = self._language.query(pattern)
                matches = query.matches(tree_node)
                
                for match in matches:
                    pattern_index, captures = match
                    
                    for capture_name, nodes in captures.items():
                        for node in nodes:
                            comment_text = self._get_node_text(node, source)
                            
                            # Skip empty comments and doc comments (handled separately)
                            if not comment_text.strip() or comment_text.strip().startswith("/**"):
                                continue
                                
                            cleaned_text = self._clean_comment_text(comment_text)
                            symbol = f"comment:{node.start_point[0] + 1}"
                            
                            chunk = self._create_chunk(
                                node=node,
                                source=source,
                                file_path=file_path,
                                chunk_type=ChunkType.COMMENT,
                                name=symbol,
                                display_name=f"Comment at line {node.start_point[0] + 1}",
                                content=cleaned_text
                            )
                            
                            chunks.append(chunk)
                            
        except Exception as e:
            logger.error(f"Failed to extract comments for C: {e}")
            
        return chunks
    
    def _clean_comment_text(self, text: str) -> str:
        """Clean comment text by removing comment markers."""
        cleaned = text.strip()
        
        # Remove common single-line comment markers
        if cleaned.startswith("//"):
            cleaned = cleaned[2:].strip()
            
        # Remove common multi-line comment markers (but not doc comments)
        if cleaned.startswith("/*") and cleaned.endswith("*/") and not cleaned.startswith("/**"):
            cleaned = cleaned[2:-2].strip()
            
        return cleaned
