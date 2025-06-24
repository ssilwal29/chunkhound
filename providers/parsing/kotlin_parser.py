"""Kotlin language parser provider implementation for ChunkHound using tree-sitter."""

from pathlib import Path
from typing import Any

from loguru import logger

from core.types import ChunkType
from core.types import Language as CoreLanguage
from interfaces.language_parser import ParseConfig
from providers.parsing.base_parser import TreeSitterParserBase

try:
    import tree_sitter_kotlin
    from tree_sitter import Language, Parser
    from tree_sitter import Node as TSNode
    TREE_SITTER_AVAILABLE = True
except ImportError:
    TREE_SITTER_AVAILABLE = False
    TSNode = None
    Language = None
    Parser = None
    tree_sitter_kotlin = None


class KotlinParser(TreeSitterParserBase):
    """Kotlin language parser using tree-sitter."""

    def __init__(self, config: ParseConfig | None = None):
        """Initialize Kotlin parser.

        Args:
            config: Optional parse configuration
        """
        super().__init__(CoreLanguage.KOTLIN, config)

    def _initialize(self) -> bool:
        """Initialize the Kotlin parser using tree-sitter-kotlin package.

        Returns:
            True if initialization successful, False otherwise
        """
        if self._initialized:
            return True

        if not TREE_SITTER_AVAILABLE or tree_sitter_kotlin is None:
            logger.error("Kotlin tree-sitter support not available")
            return False

        try:
            self._language = Language(tree_sitter_kotlin.language())
            self._parser = Parser(self._language)
            self._initialized = True
            logger.debug("Kotlin parser initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Kotlin parser: {e}")
            return False

    def _get_default_config(self) -> ParseConfig:
        """Get default configuration for Kotlin parser."""
        return ParseConfig(
            language=CoreLanguage.KOTLIN,
            chunk_types={
                ChunkType.CLASS,
                ChunkType.INTERFACE,
                ChunkType.METHOD,
                ChunkType.CONSTRUCTOR,
                ChunkType.FIELD,
                ChunkType.ENUM,
                ChunkType.OBJECT,
                ChunkType.COMPANION_OBJECT,
                ChunkType.DATA_CLASS,
                ChunkType.EXTENSION_FUNCTION
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
        """Extract semantic chunks from Kotlin AST.

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
            package_name = self._extract_package(tree_node, source)

            if ChunkType.CLASS in self._config.chunk_types:
                chunks.extend(
                    self._extract_classes(tree_node, source, file_path, package_name)
                )

            if ChunkType.DATA_CLASS in self._config.chunk_types:
                chunks.extend(
                    self._extract_data_classes(tree_node, source, file_path, package_name)
                )

            if ChunkType.OBJECT in self._config.chunk_types:
                chunks.extend(
                    self._extract_objects(tree_node, source, file_path, package_name)
                )

            if ChunkType.COMPANION_OBJECT in self._config.chunk_types:
                chunks.extend(
                    self._extract_companion_objects(tree_node, source, file_path, package_name)
                )

            if ChunkType.INTERFACE in self._config.chunk_types:
                chunks.extend(
                    self._extract_interfaces(tree_node, source, file_path, package_name)
                )

            if ChunkType.ENUM in self._config.chunk_types:
                chunks.extend(
                    self._extract_enums(tree_node, source, file_path, package_name)
                )

            if (
                ChunkType.METHOD in self._config.chunk_types
                or ChunkType.CONSTRUCTOR in self._config.chunk_types
                or ChunkType.EXTENSION_FUNCTION in self._config.chunk_types
            ):
                chunks.extend(
                    self._extract_methods(tree_node, source, file_path, package_name)
                )

            if ChunkType.FIELD in self._config.chunk_types:
                chunks.extend(
                    self._extract_properties(tree_node, source, file_path, package_name)
                )

        except Exception as e:
            logger.error(f"Failed to extract Kotlin chunks: {e}")

        return chunks

    def _extract_package(self, tree_node: TSNode, source: str) -> str:
        """Extract package name from Kotlin file."""
        try:
            if self._language is None:
                return ""

            query = self._language.query("""
                (package_header
                    (identifier) @package_name
                ) @package_def
            """)

            matches = query.matches(tree_node)

            if not matches:
                return ""

            for pattern_index, captures in matches:
                if "package_name" in captures:
                    package_node = captures["package_name"][0]
                    return self._get_node_text(package_node, source)

            return ""
        except Exception as e:
            logger.error(f"Failed to extract Kotlin package: {e}")
            return ""

    def _extract_classes(
        self,
        tree_node: TSNode,
        source: str,
        file_path: Path,
        package_name: str,
    ) -> list[dict[str, Any]]:
        """Extract Kotlin class definitions from AST."""
        chunks = []

        try:
            if self._language is None:
                return chunks

            query = self._language.query("""
                (class_declaration
                    name: (type_identifier) @class_name
                ) @class_def
            """)

            matches = query.matches(tree_node)

            for pattern_index, captures in matches:
                if "class_def" not in captures or "class_name" not in captures:
                    continue

                class_node = captures["class_def"][0]
                class_name_node = captures["class_name"][0]
                class_name = self._get_node_text(class_name_node, source)

                qualified_name = class_name
                if package_name:
                    qualified_name = f"{package_name}.{class_name}"

                chunk = self._create_chunk(
                    class_node, source, file_path, ChunkType.CLASS,
                    qualified_name, qualified_name
                )

                chunks.append(chunk)

        except Exception as e:
            logger.error(f"Failed to extract Kotlin classes: {e}")

        return chunks

    def _extract_data_classes(
        self,
        tree_node: TSNode,
        source: str,
        file_path: Path,
        package_name: str,
    ) -> list[dict[str, Any]]:
        """Extract Kotlin data class definitions from AST."""
        chunks = []

        try:
            if self._language is None:
                return chunks

            query = self._language.query("""
                (class_declaration
                    (modifiers 
                        (class_modifier "data")
                    )
                    name: (type_identifier) @data_class_name
                ) @data_class_def
            """)

            matches = query.matches(tree_node)

            for pattern_index, captures in matches:
                if "data_class_def" not in captures or "data_class_name" not in captures:
                    continue

                data_class_node = captures["data_class_def"][0]
                data_class_name_node = captures["data_class_name"][0]
                data_class_name = self._get_node_text(data_class_name_node, source)

                qualified_name = data_class_name
                if package_name:
                    qualified_name = f"{package_name}.{data_class_name}"

                chunk = self._create_chunk(
                    data_class_node, source, file_path, ChunkType.DATA_CLASS,
                    qualified_name, qualified_name
                )

                chunks.append(chunk)

        except Exception as e:
            logger.error(f"Failed to extract Kotlin data classes: {e}")

        return chunks

    def _extract_objects(
        self,
        tree_node: TSNode,
        source: str,
        file_path: Path,
        package_name: str,
    ) -> list[dict[str, Any]]:
        """Extract Kotlin object declarations from AST."""
        chunks = []

        try:
            if self._language is None:
                return chunks

            query = self._language.query("""
                (object_declaration
                    name: (type_identifier) @object_name
                ) @object_def
            """)

            matches = query.matches(tree_node)

            for pattern_index, captures in matches:
                if "object_def" not in captures or "object_name" not in captures:
                    continue

                object_node = captures["object_def"][0]
                object_name_node = captures["object_name"][0]
                object_name = self._get_node_text(object_name_node, source)

                qualified_name = object_name
                if package_name:
                    qualified_name = f"{package_name}.{object_name}"

                chunk = self._create_chunk(
                    object_node, source, file_path, ChunkType.OBJECT,
                    qualified_name, qualified_name
                )

                chunks.append(chunk)

        except Exception as e:
            logger.error(f"Failed to extract Kotlin objects: {e}")

        return chunks

    def _extract_companion_objects(
        self,
        tree_node: TSNode,
        source: str,
        file_path: Path,
        package_name: str,
    ) -> list[dict[str, Any]]:
        """Extract Kotlin companion object declarations from AST."""
        chunks = []

        try:
            if self._language is None:
                return chunks

            query = self._language.query("""
                (companion_object
                    name: (type_identifier)? @companion_name
                ) @companion_def
            """)

            matches = query.matches(tree_node)

            for pattern_index, captures in matches:
                if "companion_def" not in captures:
                    continue

                companion_node = captures["companion_def"][0]
                
                # Companion objects may or may not have explicit names
                companion_name = "Companion"
                if "companion_name" in captures:
                    companion_name_node = captures["companion_name"][0]
                    companion_name = self._get_node_text(companion_name_node, source)

                # Find containing class
                parent_class = self._find_containing_class(companion_node, source)
                
                qualified_name = companion_name
                if parent_class and package_name:
                    qualified_name = f"{package_name}.{parent_class}.{companion_name}"
                elif parent_class:
                    qualified_name = f"{parent_class}.{companion_name}"

                chunk = self._create_chunk(
                    companion_node, source, file_path, ChunkType.COMPANION_OBJECT,
                    qualified_name, companion_name,
                    parent=parent_class if parent_class else None
                )

                chunks.append(chunk)

        except Exception as e:
            logger.error(f"Failed to extract Kotlin companion objects: {e}")

        return chunks

    def _extract_interfaces(
        self,
        tree_node: TSNode,
        source: str,
        file_path: Path,
        package_name: str,
    ) -> list[dict[str, Any]]:
        """Extract Kotlin interface definitions from AST."""
        chunks = []

        try:
            if self._language is None:
                return chunks

            query = self._language.query("""
                (interface_declaration
                    name: (type_identifier) @interface_name
                ) @interface_def
            """)

            matches = query.matches(tree_node)

            for pattern_index, captures in matches:
                if "interface_def" not in captures or "interface_name" not in captures:
                    continue

                interface_node = captures["interface_def"][0]
                interface_name_node = captures["interface_name"][0]
                interface_name = self._get_node_text(interface_name_node, source)

                qualified_name = interface_name
                if package_name:
                    qualified_name = f"{package_name}.{interface_name}"

                chunk = self._create_chunk(
                    interface_node, source, file_path, ChunkType.INTERFACE,
                    qualified_name, qualified_name
                )

                chunks.append(chunk)

        except Exception as e:
            logger.error(f"Failed to extract Kotlin interfaces: {e}")

        return chunks

    def _extract_enums(
        self,
        tree_node: TSNode,
        source: str,
        file_path: Path,
        package_name: str,
    ) -> list[dict[str, Any]]:
        """Extract Kotlin enum definitions from AST."""
        chunks = []

        try:
            if self._language is None:
                return chunks

            query = self._language.query("""
                (enum_class_declaration
                    name: (type_identifier) @enum_name
                ) @enum_def
            """)

            matches = query.matches(tree_node)

            for pattern_index, captures in matches:
                if "enum_def" not in captures or "enum_name" not in captures:
                    continue

                enum_node = captures["enum_def"][0]
                enum_name_node = captures["enum_name"][0]
                enum_name = self._get_node_text(enum_name_node, source)

                qualified_name = enum_name
                if package_name:
                    qualified_name = f"{package_name}.{enum_name}"

                chunk = self._create_chunk(
                    enum_node, source, file_path, ChunkType.ENUM,
                    qualified_name, qualified_name
                )

                chunks.append(chunk)

        except Exception as e:
            logger.error(f"Failed to extract Kotlin enums: {e}")

        return chunks

    def _extract_methods(
        self,
        tree_node: TSNode,
        source: str,
        file_path: Path,
        package_name: str,
    ) -> list[dict[str, Any]]:
        """Extract Kotlin function definitions from AST."""
        chunks = []

        try:
            if self._language is None:
                return chunks

            query = self._language.query("""
                (function_declaration
                    name: (simple_identifier) @function_name
                ) @function_def

                (primary_constructor
                    (class_parameter_list) @constructor_params
                ) @constructor_def

                ; Extension functions
                (function_declaration
                    receiver: (function_type) @receiver_type
                    name: (simple_identifier) @extension_name
                ) @extension_def
            """)

            matches = query.matches(tree_node)

            for pattern_index, captures in matches:
                function_node = None
                function_name = None
                is_constructor = False
                is_extension = False

                # Handle regular functions
                if "function_def" in captures and "function_name" in captures:
                    function_node = captures["function_def"][0]
                    function_name_node = captures["function_name"][0]
                    function_name = self._get_node_text(function_name_node, source)

                # Handle constructors
                elif "constructor_def" in captures:
                    function_node = captures["constructor_def"][0]
                    function_name = "constructor"
                    is_constructor = True

                # Handle extension functions
                elif "extension_def" in captures and "extension_name" in captures:
                    function_node = captures["extension_def"][0]
                    function_name_node = captures["extension_name"][0]
                    function_name = self._get_node_text(function_name_node, source)
                    is_extension = True

                if not function_node or not function_name:
                    continue

                # Check if we want this chunk type
                if (
                    is_constructor
                    and ChunkType.CONSTRUCTOR not in self._config.chunk_types
                ):
                    continue
                if (
                    is_extension
                    and ChunkType.EXTENSION_FUNCTION not in self._config.chunk_types
                ):
                    continue
                if (
                    not is_constructor
                    and not is_extension
                    and ChunkType.METHOD not in self._config.chunk_types
                ):
                    continue

                # Find containing class/object
                parent_class = self._find_containing_class(function_node, source)

                # Build qualified name
                if parent_class and package_name:
                    qualified_name = f"{package_name}.{parent_class}.{function_name}"
                elif parent_class:
                    qualified_name = f"{parent_class}.{function_name}"
                else:
                    qualified_name = function_name

                if is_constructor:
                    chunk_type = ChunkType.CONSTRUCTOR
                elif is_extension:
                    chunk_type = ChunkType.EXTENSION_FUNCTION
                else:
                    chunk_type = ChunkType.METHOD

                chunk = self._create_chunk(
                    function_node, source, file_path, chunk_type,
                    qualified_name, qualified_name,
                    parent=parent_class if parent_class else None
                )

                chunks.append(chunk)

        except Exception as e:
            logger.error(f"Failed to extract Kotlin methods: {e}")

        return chunks

    def _extract_properties(
        self,
        tree_node: TSNode,
        source: str,
        file_path: Path,
        package_name: str,
    ) -> list[dict[str, Any]]:
        """Extract Kotlin property definitions from AST."""
        chunks = []

        try:
            if self._language is None:
                return chunks

            query = self._language.query("""
                (property_declaration
                    (variable_declaration
                        (simple_identifier) @property_name
                    )
                ) @property_def
            """)

            matches = query.matches(tree_node)

            for pattern_index, captures in matches:
                if "property_def" not in captures or "property_name" not in captures:
                    continue

                property_node = captures["property_def"][0]
                property_name_node = captures["property_name"][0]
                property_name = self._get_node_text(property_name_node, source)

                # Find containing class
                parent_class = self._find_containing_class(property_node, source)

                # Build qualified name
                if parent_class and package_name:
                    qualified_name = f"{package_name}.{parent_class}.{property_name}"
                elif parent_class:
                    qualified_name = f"{parent_class}.{property_name}"
                else:
                    qualified_name = property_name

                chunk = self._create_chunk(
                    property_node, source, file_path, ChunkType.FIELD,
                    qualified_name, property_name,
                    parent=parent_class if parent_class else None
                )

                chunks.append(chunk)

        except Exception as e:
            logger.error(f"Failed to extract Kotlin properties: {e}")

        return chunks

    def _find_containing_class(self, node: TSNode, source: str) -> str | None:
        """Find the name of the class containing the given node."""
        current = node.parent

        while current:
            if current.type in ["class_declaration", "object_declaration"]:
                # Find the class/object name
                for i in range(current.child_count):
                    child = current.child(i)
                    if child and child.type == "type_identifier":
                        return self._get_node_text(child, source)
            current = current.parent

        return None