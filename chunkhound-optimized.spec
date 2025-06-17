# -*- mode: python ; coding: utf-8 -*-
"""
Optimized PyInstaller spec file for ChunkHound with focus on startup performance.
This version eliminates unnecessary data collection and optimizes for fast startup.
"""

import os
import sys
from pathlib import Path

# Get the project root directory
project_root = Path(SPECPATH)

# Minimal hidden imports - only what's absolutely necessary
hiddenimports = [
    # Core chunkhound modules that are definitely needed
    'chunkhound.api.cli.main',
    'chunkhound.api.cli.commands.run',
    'chunkhound.api.cli.commands.config',
    'chunkhound.api.cli.commands.mcp',
    'chunkhound.mcp_entry',

    # Core system modules
    'core.models.chunk',
    'core.models.file',
    'core.models.embedding',
    'providers.database.duckdb_provider',
    'providers.embedding.openai_provider',
    'providers.parser.tree_sitter_provider',
    'services.embedding_service',
    'services.indexing_coordinator',
    'registry',

    # Essential third-party modules
    'duckdb',
    'tree_sitter',
    'tree_sitter_python',
    'tree_sitter_markdown',
    'openai',
    'pydantic',
    'click',
    'loguru',
    'mcp',
    'mcp.server',
    'mcp.server.fastmcp',
]

# Minimal data files - only essential binaries
datas = [
    # Include mcp_launcher.py for MCP server functionality
    (str(project_root / 'mcp_launcher.py'), '.'),
]

# Add only essential DuckDB binaries
try:
    import duckdb
    duckdb_path = Path(duckdb.__file__).parent
    for lib_file in duckdb_path.glob('*.so'):
        datas.append((str(lib_file), 'duckdb'))
    for lib_file in duckdb_path.glob('*.dylib'):
        datas.append((str(lib_file), 'duckdb'))
    for lib_file in duckdb_path.glob('*.dll'):
        datas.append((str(lib_file), 'duckdb'))
except ImportError:
    pass

# Add tree-sitter language pack binaries
try:
    import tree_sitter
    import tree_sitter_language_pack

    # Core tree-sitter library
    ts_path = Path(tree_sitter.__file__).parent
    for lib_file in ts_path.glob('*.so'):
        datas.append((str(lib_file), 'tree_sitter'))
    for lib_file in ts_path.glob('*.dylib'):
        datas.append((str(lib_file), 'tree_sitter'))
    for lib_file in ts_path.glob('*.dll'):
        datas.append((str(lib_file), 'tree_sitter'))

    # Language pack bindings - includes all supported languages
    lang_pack_path = Path(tree_sitter_language_pack.__file__).parent
    bindings_path = lang_pack_path / 'bindings'
    if bindings_path.exists():
        for lib_file in bindings_path.glob('*.so'):
            datas.append((str(lib_file), 'tree_sitter_language_pack/bindings'))
        for lib_file in bindings_path.glob('*.dylib'):
            datas.append((str(lib_file), 'tree_sitter_language_pack/bindings'))
        for lib_file in bindings_path.glob('*.dll'):
            datas.append((str(lib_file), 'tree_sitter_language_pack/bindings'))
        # Also include the __init__.py file for the bindings module
        bindings_init = bindings_path / '__init__.py'
        if bindings_init.exists():
            datas.append((str(bindings_init), 'tree_sitter_language_pack/bindings'))
except ImportError:
    pass

# Add tiktoken encoding data files for OpenAI semantic search
try:
    import tiktoken
    tiktoken_path = Path(tiktoken.__file__).parent

    # Include tiktoken encodings directory
    encodings_path = tiktoken_path / 'encodings'
    if encodings_path.exists():
        for encoding_file in encodings_path.glob('*.json'):
            datas.append((str(encoding_file), 'tiktoken/encodings'))
        for encoding_file in encodings_path.glob('*.txt'):
            datas.append((str(encoding_file), 'tiktoken/encodings'))
        for encoding_file in encodings_path.glob('*.tiktoken'):
            datas.append((str(encoding_file), 'tiktoken/encodings'))
except ImportError:
    pass

# Aggressive exclusions to reduce size and startup time
excludes = [
    # Remove large unused packages
    'matplotlib',
    'numpy',
    'scipy',
    'pandas',
    'tensorflow',
    'torch',
    'jupyter',
    'notebook',
    'IPython',
    'sphinx',
    'pytest',
    'test',
    'tests',
    'unittest',
    'doctest',
    'pdb',
    'profile',
    'pstats',
    'cProfile',

    # Remove GUI frameworks
    'tkinter',
    'Tkinter',
    '_tkinter',
    'tcl',
    'tk',
    'PyQt5',
    'PyQt6',
    'PySide2',
    'PySide6',
    'wx',

    # Remove development tools
    'setuptools',
    'pip',
    'wheel',
    'distutils',
    'packaging',

    # Remove optional features we don't need
    'http.server',
    'urllib3.contrib',
    'requests_oauthlib',
    'oauthlib',

    # Remove unused stdlib modules
    'turtle',
    'audiodev',
    'curses',
    'dbm',
    'ensurepip',
    'venv',
    'wsgiref',
    'xmlrpc',
]

# Optimized Analysis configuration
a = Analysis(
    ['cli_wrapper.py'],
    pathex=[str(project_root)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
    optimize=2,  # Enable maximum bytecode optimization
)

# Optimize PYZ with compression
pyz = PYZ(a.pure, a.zipped_data, cipher=None)

# Create optimized executable
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='chunkhound-optimized',
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,  # Strip debug symbols
    upx=False,   # Keep UPX disabled for now
    console=True,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

# Create optimized directory distribution
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=True,  # Strip debug symbols from all binaries
    upx=False,   # Keep UPX disabled for startup performance
    upx_exclude=[],
    name='chunkhound-optimized',
)
