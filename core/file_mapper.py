"""
Fájltérképező modul - rekurzív könyvtárbejárás és .gitignore feldolgozás
"""

import os
from pathlib import Path
from typing import List, Dict, Any, Set, Optional
import fnmatch


class FileInfo:
    """Fájl információkat tároló osztály"""
    
    def __init__(self, path: Path, root_path: Path):
        """
        FileInfo inicializálása
        
        Args:
            path: A fájl abszolút útvonala
            root_path: A projekt gyökérkönyvtára
        """
        self.path = path
        self.root_path = root_path
        self.relative_path = path.relative_to(root_path)
        self.name = path.name
        self.extension = path.suffix.lower()
        self.size = path.stat().st_size if path.exists() else 0
        self.is_file = path.is_file()
        self.is_dir = path.is_dir()
        self.is_hidden = path.name.startswith('.')
        self.modified_time = path.stat().st_mtime if path.exists() else 0
    
    def __str__(self) -> str:
        return str(self.relative_path)
    
    def __repr__(self) -> str:
        return f"FileInfo(path={self.relative_path}, size={self.size}, is_file={self.is_file})"


class GitIgnoreParser:
    """GitIgnore fájlok feldolgozása"""
    
    def __init__(self, root_path: Path):
        """
        GitIgnore parser inicializálása
        
        Args:
            root_path: A projekt gyökérkönyvtára
        """
        self.root_path = root_path
        self.patterns: List[str] = []
        self.negated_patterns: List[str] = []
        self._load_gitignore()
    
    def _load_gitignore(self):
        """GitIgnore fájl betöltése és feldolgozása"""
        gitignore_path = self.root_path / '.gitignore'
        
        if not gitignore_path.exists():
            return
        
        try:
            with open(gitignore_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    
                    # Üres sorok és kommentek kihagyása
                    if not line or line.startswith('#'):
                        continue
                    
                    # Negált minták kezelése
                    if line.startswith('!'):
                        self.negated_patterns.append(line[1:])
                    else:
                        self.patterns.append(line)
        except Exception as e:
            print(f"Figyelmeztetés: Hiba a .gitignore fájl olvasásakor: {e}")
    
    def is_ignored(self, file_info: FileInfo) -> bool:
        """
        Ellenőrzi, hogy a fájl ki van-e zárva a .gitignore alapján
        
        Args:
            file_info: Fájl információ
            
        Returns:
            bool: True ha ki van zárva
        """
        path_str = str(file_info.relative_path)
        name_str = file_info.name
        
        # Először ellenőrizzük, hogy a negált minták közé esik-e
        for pattern in self.negated_patterns:
            if self._match_pattern(path_str, name_str, pattern):
                return False
        
        # Majd ellenőrizzük, hogy a normál minták közé esik-e
        for pattern in self.patterns:
            if self._match_pattern(path_str, name_str, pattern):
                return True
        
        return False
    
    def _match_pattern(self, path_str: str, name_str: str, pattern: str) -> bool:
        """
        Mintaillesztés a .gitignore szabályai szerint
        
        Args:
            path_str: Teljes relatív útvonal
            name_str: Fájlnév
            pattern: Mintázat
            
        Returns:
            bool: True ha egyezik
        """
        # Könyvtár minták kezelése
        if pattern.endswith('/'):
            # Könyvtár minta - ellenőrizzük a teljes útvonalat
            dir_pattern = pattern[:-1]
            if fnmatch.fnmatch(path_str, dir_pattern) or path_str.startswith(dir_pattern + '/'):
                return True
        else:
            # Normál minta - ellenőrizzük a nevet és az útvonalat is
            if fnmatch.fnmatch(name_str, pattern) or fnmatch.fnmatch(path_str, pattern):
                return True
        
        return False


class FileMapper:
    """Fájltérképező osztály"""
    
    def __init__(self, root_path: Path, config: Dict[str, Any], verbose: bool = False):
        """
        FileMapper inicializálása
        
        Args:
            root_path: A projektkönyvtár elérési útja
            config: Konfiguráció
            verbose: Részletes kimenet
        """
        self.root_path = Path(root_path).resolve()
        self.config = config
        self.verbose = verbose
        self.gitignore_parser = GitIgnoreParser(self.root_path)
        
        if self.verbose:
            print(f"Projekt gyökér: {self.root_path}")
            print(f".gitignore minták: {len(self.gitignore_parser.patterns)}")
    
    def map_files(self) -> List[FileInfo]:
        """
        Rekurzív fájltérképezés
        
        Returns:
            List[FileInfo]: Az összes fájl információja
        """
        files = []
        
        if self.verbose:
            print("Fájlok feltérképezése...")
        
        try:
            for item in self.root_path.rglob('*'):
                # Rejtett fájlok kezelése
                if not self.config.get('tree', {}).get('show_hidden', False) and item.name.startswith('.'):
                    continue
                
                file_info = FileInfo(item, self.root_path)
                
                # .gitignore ellenőrzése
                if self.gitignore_parser.is_ignored(file_info):
                    if self.verbose:
                        print(f"  .gitignore által kizárva: {file_info.relative_path}")
                    continue
                
                files.append(file_info)
                
                if self.verbose and len(files) % 100 == 0:
                    print(f"  {len(files)} fájl feldolgozva...")
        
        except Exception as e:
            print(f"Hiba a fájlok feltérképezésekor: {e}")
        
        if self.verbose:
            print(f"Összesen {len(files)} fájl és könyvtár található")
        
        return files
    
    def get_directory_tree(self, files: List[FileInfo], max_depth: int = 5) -> str:
        """
    Fájlfa generálása szöveges formában
        
        Args:
            files: Fájlok listája
            max_depth: Maximális mélység
            
        Returns:
            str: Szöveges fájlfa
        """
        if not files:
            return "Üres projekt"
        
        # Rendezés útvonal szerint
        sorted_files = sorted(files, key=lambda f: (f.relative_path.parts, not f.is_dir))
        
        # Fa struktúra építése
        tree_lines = []
        tree_lines.append(f"{self.root_path.name}/")
        
        # Útvonalak követése
        current_depth = 0
        last_parts = []
        
        for file_info in sorted_files:
            if file_info.relative_path == Path('.'):
                continue
            
            parts = list(file_info.relative_path.parts)
            
            # Mélység ellenőrzése
            if len(parts) > max_depth + 1:  # +1 a gyökér miatt
                continue
            
            # Könyvtár szint meghatározása
            depth = len(parts)
            
            # Előző elemekhez viszonyított elhelyezés
            prefix = ""
            for i in range(depth - 1):
                if i < len(last_parts) and i < depth - 1 and parts[i] == last_parts[i]:
                    prefix += "│   "
                else:
                    prefix += "    "
            
            # Utolsó elem jelölése
            if depth == 1:
                connector = "└── " if file_info == sorted_files[-1] else "├── "
            else:
                # Ellenőrizzük, hogy ez az utolsó elem a szintjén
                is_last = True
                next_file_info = None
                for next_f in sorted_files[sorted_files.index(file_info) + 1:]:
                    if len(next_f.relative_path.parts) >= depth and \
                       all(p == np for p, np in zip(parts[:depth-1], next_f.relative_path.parts[:depth-1])):
                        next_file_info = next_f
                        break
                
                if next_file_info and len(next_file_info.relative_path.parts) >= depth:
                    connector = "├── "
                else:
                    connector = "└── "
            
            # Fájl vagy könyvtár jelölése
            if file_info.is_dir:
                name = file_info.name + "/"
            else:
                name = file_info.name
            
            tree_lines.append(prefix + connector + name)
            
            last_parts = parts
        
        return "\n".join(tree_lines)