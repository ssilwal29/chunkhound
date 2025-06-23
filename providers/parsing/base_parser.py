"""Base tree-sitter parser with shared functionality for ChunkHound parsers."""

from pathlib import Path
from typing import List, Dict, Any, Optional, Set
import time

from loguru import logger

from core.types import ChunkType, Language as CoreLanguage
from interfaces.language_parser import ParseConfig, ParseResult

try:
    from tree_sitter_language_pack import get_language, get_parser
    from tree_sitter import Language as TSLanguage, Parser as TSParser, Node as TSNode
    TREE_SITTER_AVAILABLE = True
except ImportError:
    TREE_SITTER_AVAILABLE = False
    get_language = None
    get_parser = None
    TSLanguage = None
    TSParser = None
    TSNode = None


class TreeSitterParserBase:
    """Base class for tree-sitter parsers with shared functionality."""
    
    def __init__(self, language: CoreLanguage, config: Optional[ParseConfig] = None):
        """Initialize base tree-sitter parser.
        
        Args:
            language: Programming language this parser handles
            config: Optional parse configuration
        """
        self._language_name = language
        self._language = None
        self._parser = None
        self._initialized = False
        self._config = config or self._get_default_config()
        
        # Initialize if available
        if TREE_SITTER_AVAILABLE:
            self._initialize()
    
    def _get_default_config(self) -> ParseConfig:
        """Get default configuration for this parser. Override in subclasses."""
        return ParseConfig(
            language=self._language_name,
            chunk_types={ChunkType.FUNCTION, ChunkType.CLASS},
            max_chunk_size=8000,
            min_chunk_size=100,
            include_imports=True,
            include_comments=False,
            include_docstrings=True,
            max_depth=10,
            use_cache=True
        )
    
    def _get_tree_sitter_language_name(self) -> str:
        """Get tree-sitter language name. Override in subclasses if different."""
        return self._language_name.value.lower()
    
    def _initialize(self) -> bool:
        """Initialize the tree-sitter parser.
        
        Returns:
            True if initialization successful, False otherwise
        """
        if self._initialized:
            return True
            
        if not TREE_SITTER_AVAILABLE:
            logger.error(f"{self._language_name.value} tree-sitter support not available")
            return False
        
        try:
            if get_language and get_parser:
                ts_lang_name = self._get_tree_sitter_language_name()
                self._language = get_language(ts_lang_name)
                self._parser = get_parser(ts_lang_name)
                self._initialized = True
                logger.debug(f"{self._language_name.value} parser initialized successfully")
                return True
            else:
                logger.error(f"{self._language_name.value} parser dependencies not available")
                return False
        except Exception as e:
            logger.error(f"Failed to initialize {self._language_name.value} parser: {e}")
            return False
    
    @property
    def language(self) -> CoreLanguage:
        """Programming language this parser handles."""
        return self._language_name
    
    @property
    def supported_chunk_types(self) -> Set[ChunkType]:
        """Chunk types this parser can extract."""
        return self._config.chunk_types
    
    @property
    def is_available(self) -> bool:
        """Whether the parser is available and ready to use."""
        return TREE_SITTER_AVAILABLE and self._initialized
    
    def parse_file(self, file_path: Path, source: Optional[str] = None) -> ParseResult:
        """Parse a file and extract semantic chunks.
        
        Args:
            file_path: Path to source file
            source: Optional source code string
            
        Returns:
            ParseResult with extracted chunks and metadata
        """
        start_time = time.time()
        chunks = []
        errors = []
        warnings = []
        
        if not self.is_available:
            errors.append(f"{self._language_name.value} parser not available")
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
                with open(file_path, 'r', encoding='utf-8') as f:
                    source = f.read()
            
            # Parse with tree-sitter
            if self._parser is None:
                errors.append(f"{self._language_name.value} parser not initialized")
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
            
            # Extract semantic units - delegate to subclass
            chunks = self._extract_chunks(tree.root_node, source, file_path)
            
            logger.debug(f"Extracted {len(chunks)} chunks from {file_path}")
            
        except Exception as e:
            error_msg = f"Failed to parse {self._language_name.value} file {file_path}: {e}"
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
    
    def _extract_chunks(self, tree_node: TSNode, source: str, file_path: Path) -> List[Dict[str, Any]]:
        """Extract semantic chunks from AST. Override in subclasses.
        
        Args:
            tree_node: Root AST node
            source: Source code string
            file_path: Path to source file
            
        Returns:
            List of extracted chunks
        """
        raise NotImplementedError("Subclasses must implement _extract_chunks")
    
    def _get_node_text(self, node: TSNode, source: str) -> str:
        """Extract text content from a tree-sitter node."""
        return source[node.start_byte:node.end_byte]
    
    def _create_chunk(self, node: TSNode, source: str, file_path: Path, 
                     chunk_type: ChunkType, name: str, display_name: Optional[str] = None,
                     parent: Optional[str] = None, **extra_fields) -> Dict[str, Any]:
        """Create a standard chunk dictionary.
        
        Args:
            node: AST node
            source: Source code string
            file_path: Path to source file
            chunk_type: Type of chunk
            name: Chunk name/symbol
            display_name: Display name (defaults to name)
            parent: Parent symbol name
            **extra_fields: Additional fields to include
            
        Returns:
            Chunk dictionary
        """
        code = self._get_node_text(node, source)
        
        chunk = {
            "symbol": name,
            "start_line": node.start_point[0] + 1,
            "end_line": node.end_point[0] + 1,
            "code": code,
            "chunk_type": chunk_type.value,
            "language": self._language_name.value.lower(),
            "path": str(file_path),
            "name": name,
            "display_name": display_name or name,
            "content": code,
            "start_byte": node.start_byte,
            "end_byte": node.end_byte,
        }
        
        if parent:
            chunk["parent"] = parent
            
        # Add extra fields
        chunk.update(extra_fields)
        
        return chunk