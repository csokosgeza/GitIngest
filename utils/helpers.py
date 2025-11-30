"""
Segédfüggvények modul
"""

import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional


def is_binary_file(file_path: Path, sample_size: int = 1024) -> bool:
    """
    Ellenőrzi, hogy a fájl bináris-e
    
    Args:
        file_path: Fájl elérési útja
        sample_size: Mintavételezési méret
        
    Returns:
        bool: True ha bináris
    """
    try:
        with open(file_path, 'rb') as f:
            sample = f.read(sample_size)
        
        # Ha a mintában null byte van, akkor bináris
        if b'\x00' in sample:
            return True
        
        # Ellenőrizzük, hogy a minta tartalmaz-e nem nyomtatható karaktereket
        text_characters = bytearray(range(32, 127)) + b'\n\r\t\b'
        
        # Ha a minta 30%-a nem nyomtatható karakter, akkor bináris
        non_text_chars = sum(1 for byte in sample if byte not in text_characters)
        return len(sample) > 0 and (non_text_chars / len(sample)) > 0.3
    
    except Exception:
        return True


def format_file_size(size_bytes: int) -> str:
    """
    Méret formázása ember által olvasható formában
    
    Args:
        size_bytes: Méret bájtban
        
    Returns:
        str: Formázott méret
    """
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    size = float(size_bytes)
    
    while size >= 1024.0 and i < len(size_names) - 1:
        size /= 1024.0
        i += 1
    
    return f"{size:.1f} {size_names[i]}"


def get_file_language(file_path: Path) -> str:
    """
    Nyelv meghatározása fájlból
    
    Args:
        file_path: Fájl elérési útja
        
    Returns:
        str: Nyelv neve
    """
    extension_map = {
        '.py': 'python',
        '.js': 'javascript',
        '.ts': 'typescript',
        '.jsx': 'jsx',
        '.tsx': 'tsx',
        '.java': 'java',
        '.c': 'c',
        '.cpp': 'cpp',
        '.cc': 'cpp',
        '.cxx': 'cpp',
        '.h': 'c',
        '.hpp': 'cpp',
        '.cs': 'csharp',
        '.php': 'php',
        '.rb': 'ruby',
        '.go': 'go',
        '.rs': 'rust',
        '.swift': 'swift',
        '.kt': 'kotlin',
        '.scala': 'scala',
        '.dart': 'dart',
        '.lua': 'lua',
        '.r': 'r',
        '.m': 'objective-c',
        '.pl': 'perl',
        '.sh': 'bash',
        '.bash': 'bash',
        '.zsh': 'zsh',
        '.fish': 'fish',
        '.sql': 'sql',
        '.html': 'html',
        '.htm': 'html',
        '.xml': 'xml',
        '.css': 'css',
        '.scss': 'scss',
        '.sass': 'sass',
        '.less': 'less',
        '.vue': 'vue',
        '.svelte': 'svelte',
        '.elm': 'elm',
        '.hs': 'haskell',
        '.ml': 'ocaml',
        '.clj': 'clojure',
        '.cljs': 'clojurescript',
        '.ex': 'elixir',
        '.exs': 'elixir',
        '.json': 'json',
        '.yaml': 'yaml',
        '.yml': 'yaml',
        '.toml': 'toml',
        '.ini': 'ini',
        '.cfg': 'ini',
        '.conf': 'ini',
        '.config': 'ini',
        '.md': 'markdown',
        '.markdown': 'markdown',
        '.txt': 'text',
        '.rst': 'rst',
        '.adoc': 'asciidoc',
        '.tex': 'latex',
        '.csv': 'csv',
        '.tsv': 'tsv',
        '.gitignore': 'gitignore',
        '.gitattributes': 'gitattributes',
        '.editorconfig': 'ini',
        '.eslintrc': 'json',
        '.prettierrc': 'json',
        '.babelrc': 'json',
        '.dockerignore': 'gitignore',
        '.npmignore': 'gitignore',
        '.hgignore': 'gitignore',
        '.svnignore': 'gitignore',
        'dockerfile': 'dockerfile',
        'makefile': 'makefile'
    }
    
    # Kiterjesztés alapján
    extension = file_path.suffix.lower()
    if extension in extension_map:
        return extension_map[extension]
    
    # Fájlnév alapján (kiterjesztés nélküli fájlok)
    filename = file_path.name.lower()
    if filename in extension_map:
        return extension_map[filename]
    
    return 'text'


def truncate_text(text: str, max_lines: int = 100, max_chars: int = 10000) -> str:
    """
    Szöveg levágása
    
    Args:
        text: Szöveg
        max_lines: Maximális sorok száma
        max_chars: Maximális karakterek száma
        
    Returns:
        str: Levágott szöveg
    """
    if not text:
        return text
    
    lines = text.splitlines()
    
    # Sorok számának korlátozása
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        lines.append(f"\n[... Több mint {max_lines} sor levágva ...]")
    
    # Karakterek számának korlátozása
    truncated_text = '\n'.join(lines)
    if len(truncated_text) > max_chars:
        truncated_text = truncated_text[:max_chars]
        truncated_text += f"\n[... Több mint {max_chars} karakter levágva ...]"
    
    return truncated_text


def safe_filename(filename: str) -> str:
    """
    Fájlnév biztonságossá tétele
    
    Args:
        filename: Eredeti fájlnév
        
    Returns:
        str: Biztonságos fájlnév
    """
    # Csere az érvénytelen karakterekre
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    
    # Túl hosszú nevek rövidítése
    if len(filename) > 200:
        name_part, ext_part = os.path.splitext(filename)
        max_name_length = 200 - len(ext_part)
        filename = name_part[:max_name_length] + ext_part
    
    return filename


def ensure_directory_exists(dir_path: Path) -> bool:
    """
    Könyvtár létrehozása, ha nem létezik
    
    Args:
        dir_path: Könyvtár elérési útja
        
    Returns:
        bool: Sikeres létrehozás
    """
    try:
        dir_path.mkdir(parents=True, exist_ok=True)
        return True
    except Exception:
        return False


def get_relative_path(file_path: Path, base_path: Path) -> Path:
    """
    Relatív útvonal meghatározása
    
    Args:
        file_path: Fájl elérési útja
        base_path: Alapútvonal
        
    Returns:
        Path: Relatív útvonal
    """
    try:
        return file_path.relative_to(base_path)
    except ValueError:
        # Ha a fájl nincs az alapútvonal alatt, akkor a teljes útvonalat adjuk vissza
        return file_path


def print_progress(current: int, total: int, prefix: str = "", suffix: str = "", bar_length: int = 50):
    """
    Haladás kiírása a konzolra
    
    Args:
        current: Jelenlegi érték
        total: Teljes érték
        prefix: Előtag
        suffix: Utótag
        bar_length: Csík hossza
    """
    if total == 0:
        return
    
    percent = float(current) * 100 / total
    arrow = '-' * int(percent / 100 * bar_length - 1) + '>'
    spaces = ' ' * (bar_length - len(arrow))
    
    sys.stdout.write(f'\r{prefix} [{arrow}{spaces}] {percent:.1f}% {suffix}')
    sys.stdout.flush()
    
    if current == total:
        sys.stdout.write('\n')
        sys.stdout.flush()


def validate_project_path(path: Path) -> bool:
    """
    Projekt útvonal ellenőrzése
    
    Args:
        path: Projekt útvonal
        
    Returns:
        bool: Érvényes útvonal
    """
    if not path.exists():
        print(f"Hiba: Az útvonal nem létezik: {path}")
        return False
    
    if not path.is_dir():
        print(f"Hiba: Az útvonal nem egy könyvtár: {path}")
        return False
    
    # Jogosultságok ellenőrzése
    if not os.access(path, os.R_OK):
        print(f"Hiba: Nincs olvasási jogosultság: {path}")
        return False
    
    return True


def detect_project_type(project_path: Path) -> str:
    """
    Projekt típusának detektálása
    
    Args:
        project_path: Projekt útvonal
        
    Returns:
        str: Projekt típusa
    """
    indicators = {
        'python': ['requirements.txt', 'setup.py', 'pyproject.toml', 'Pipfile', 'poetry.lock', '__init__.py'],
        'javascript': ['package.json', 'package-lock.json', 'yarn.lock', 'npm-shrinkwrap.json'],
        'typescript': ['tsconfig.json', 'package.json'],
        'java': ['pom.xml', 'build.gradle', 'build.gradle.kts', 'settings.gradle'],
        'csharp': ['*.csproj', '*.sln', 'project.json', 'global.json'],
        'go': ['go.mod', 'go.sum'],
        'rust': ['Cargo.toml', 'Cargo.lock'],
        'ruby': ['Gemfile', 'Gemfile.lock'],
        'php': ['composer.json', 'composer.lock'],
        'swift': ['Package.swift', 'Podfile', 'Podfile.lock'],
        'kotlin': ['build.gradle', 'build.gradle.kts', 'settings.gradle'],
        'dart': ['pubspec.yaml', 'pubspec.lock'],
        'elixir': ['mix.exs', 'mix.lock'],
        'clojure': ['project.clj', 'deps.edn'],
        'haskell': ['cabal.project', 'stack.yaml', 'package.yaml'],
        'ocaml': ['dune-project', 'opam', 'Makefile'],
        'r': ['DESCRIPTION', 'NAMESPACE', 'Rprofile'],
        'lua': ['rockspec'],
        'perl': ['cpanfile', 'Makefile.PL'],
        'web': ['index.html', 'index.htm'],
        'docker': ['Dockerfile', 'docker-compose.yml', 'docker-compose.yaml'],
        'kubernetes': ['k8s.yaml', 'kubernetes.yaml', 'deployment.yaml'],
        'terraform': ['main.tf', 'variables.tf', 'outputs.tf'],
        'ansible': ['playbook.yml', 'ansible.cfg', 'requirements.yml']
    }
    
    for project_type, files in indicators.items():
        for file_pattern in files:
            if '*' in file_pattern:
                # Wildcard minta
                pattern = file_pattern.replace('*', '')
                for file_path in project_path.glob(f"*{pattern}*"):
                    if file_path.is_file():
                        return project_type
            else:
                # Normál fájlnév
                if (project_path / file_pattern).exists():
                    return project_type
    
    return 'unknown'