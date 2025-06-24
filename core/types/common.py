"""ChunkHound Core Types - Common type definitions and aliases.

This module contains type definitions, enums, and type aliases used throughout
the ChunkHound system. These types provide better code clarity, IDE support,
and runtime type checking capabilities.
"""

from enum import Enum
from typing import List, Union, NewType
from pathlib import Path


# String-based type aliases for better semantic clarity
ProviderName = NewType("ProviderName", str)  # e.g., "openai", "bge"
ModelName = NewType("ModelName", str)       # e.g., "text-embedding-3-small"
FilePath = NewType("FilePath", str)         # File path as string

# Numeric type aliases
ChunkId = NewType("ChunkId", int)          # Database chunk ID
FileId = NewType("FileId", int)            # Database file ID
LineNumber = NewType("LineNumber", int)     # 1-based line numbers
ByteOffset = NewType("ByteOffset", int)     # Byte positions in files
Timestamp = NewType("Timestamp", float)     # Unix timestamp
Distance = NewType("Distance", float)       # Vector distance/similarity score
Dimensions = NewType("Dimensions", int)     # Embedding vector dimensions

# Complex types
EmbeddingVector = List[float]              # Vector embedding representation


class ChunkType(Enum):
    """Enumeration of semantic chunk types supported by ChunkHound."""

    # Code structure types
    FUNCTION = "function"
    METHOD = "method"
    CLASS = "class"
    INTERFACE = "interface"
    STRUCT = "struct"
    ENUM = "enum"
    NAMESPACE = "namespace"
    CONSTRUCTOR = "constructor"
    PROPERTY = "property"
    FIELD = "field"
    TYPE_ALIAS = "type_alias"
    CLOSURE = "closure"
    TRAIT = "trait"
    SCRIPT = "script"
    OBJECT = "object"
    COMPANION_OBJECT = "companion_object"
    DATA_CLASS = "data_class"
    EXTENSION_FUNCTION = "extension_function"
    
    # C-specific types
    VARIABLE = "variable"
    TYPE = "type"
    MACRO = "macro"

    # Documentation types
    HEADER_1 = "header_1"
    HEADER_2 = "header_2"
    HEADER_3 = "header_3"
    HEADER_4 = "header_4"
    HEADER_5 = "header_5"
    HEADER_6 = "header_6"
    PARAGRAPH = "paragraph"
    CODE_BLOCK = "code_block"

    # Configuration types
    TABLE = "table"
    KEY_VALUE = "key_value"
    ARRAY = "array"

    # Generic types
    BLOCK = "block"
    UNKNOWN = "unknown"

    @classmethod
    def from_string(cls, value: str) -> "ChunkType":
        """Convert string to ChunkType enum, defaulting to UNKNOWN for invalid values."""
        try:
            return cls(value)
        except ValueError:
            return cls.UNKNOWN

    @property
    def is_code(self) -> bool:
        """Return True if this chunk type represents code structure."""
        return self in {
            self.FUNCTION, self.METHOD, self.CLASS, self.INTERFACE,
            self.STRUCT, self.ENUM, self.NAMESPACE, self.CONSTRUCTOR,
            self.PROPERTY, self.FIELD, self.TYPE_ALIAS, self.CLOSURE,
            self.TRAIT, self.SCRIPT, self.BLOCK, self.VARIABLE, self.TYPE, self.MACRO
        }

    @property
    def is_documentation(self) -> bool:
        """Return True if this chunk type represents documentation."""
        return self in {
            self.HEADER_1, self.HEADER_2, self.HEADER_3,
            self.HEADER_4, self.HEADER_5, self.HEADER_6,
            self.PARAGRAPH, self.CODE_BLOCK
        }


class Language(Enum):
    """Enumeration of programming languages and file types supported by ChunkHound."""

    # Programming languages
    PYTHON = "python"
    JAVA = "java"
    CSHARP = "csharp"
    TYPESCRIPT = "typescript"
    JAVASCRIPT = "javascript"
    TSX = "tsx"
    JSX = "jsx"
    GROOVY = "groovy"
    KOTLIN = "kotlin"
    GO = "go"
    BASH = "bash"
    MAKEFILE = "makefile"
    C = "c"
    CPP = "cpp"
    MATLAB = "matlab"

    # Documentation languages
    MARKDOWN = "markdown"

    # Data/Configuration languages
    JSON = "json"
    YAML = "yaml"
    TOML = "toml"
    TEXT = "text"

    # Generic/unknown
    UNKNOWN = "unknown"

    @classmethod
    def from_file_extension(cls, file_path: Union[str, Path]) -> "Language":
        """Determine language from file extension and filename."""
        if isinstance(file_path, str):
            file_path = Path(file_path)

        # Check filename-based detection first (for Makefiles)
        basename = file_path.name.lower()
        filename_map = {
            'makefile': cls.MAKEFILE,
            'gnumakefile': cls.MAKEFILE,
        }
        
        if basename in filename_map:
            return filename_map[basename]

        # Check extension-based detection
        extension = file_path.suffix.lower()
        extension_map = {
            '.py': cls.PYTHON,
            '.java': cls.JAVA,
            '.cs': cls.CSHARP,
            '.ts': cls.TYPESCRIPT,
            '.js': cls.JAVASCRIPT,
            '.tsx': cls.TSX,
            '.jsx': cls.JSX,
            '.groovy': cls.GROOVY,
            '.gvy': cls.GROOVY,
            '.gy': cls.GROOVY,
            '.kt': cls.KOTLIN,
            '.kts': cls.KOTLIN,
            '.go': cls.GO,
            '.sh': cls.BASH,
            '.bash': cls.BASH,
            '.zsh': cls.BASH,
            '.mk': cls.MAKEFILE,
            '.make': cls.MAKEFILE,
            '.md': cls.MARKDOWN,
            '.markdown': cls.MARKDOWN,
            '.json': cls.JSON,
            '.yaml': cls.YAML,
            '.yml': cls.YAML,
            '.toml': cls.TOML,
            '.txt': cls.TEXT,
            '.c': cls.C,
            '.h': cls.C,
            '.cpp': cls.CPP,
            '.cxx': cls.CPP,
            '.cc': cls.CPP,
            '.hpp': cls.CPP,
            '.hxx': cls.CPP,
            '.h++': cls.CPP,
            '.m': cls.MATLAB,
        }

        return extension_map.get(extension, cls.UNKNOWN)

    @classmethod
    def from_string(cls, value: str) -> "Language":
        """Convert string to Language enum, defaulting to UNKNOWN for invalid values."""
        try:
            return cls(value)
        except ValueError:
            return cls.UNKNOWN

    @property
    def is_programming_language(self) -> bool:
        """Return True if this is a programming language (not documentation)."""
        return self in {
            self.PYTHON, self.JAVA, self.CSHARP, self.TYPESCRIPT,
            self.JAVASCRIPT, self.TSX, self.JSX, self.GROOVY, self.KOTLIN, self.GO, self.BASH, self.MAKEFILE, self.C, self.CPP, self.MATLAB
        }

    @property
    def supports_classes(self) -> bool:
        """Return True if this language supports class definitions."""
        return self in {
            self.PYTHON, self.JAVA, self.CSHARP, self.TYPESCRIPT, self.TSX, self.GROOVY, self.KOTLIN, self.GO, self.CPP, self.MATLAB
        }

    @property
    def supports_interfaces(self) -> bool:
        """Return True if this language supports interface definitions."""
        return self in {
            self.JAVA, self.CSHARP, self.TYPESCRIPT, self.TSX
        }
