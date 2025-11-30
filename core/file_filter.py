"""
Fájlszűrő modul - kiterjesztés, méret és bizalmas tartalmak szűrése
"""

import re
from pathlib import Path
from typing import List, Dict, Any, Set, Tuple

from core.file_mapper import FileInfo


class FileFilter:
    """Fájlszűrő osztály"""
    
    def __init__(self, config: Dict[str, Any], verbose: bool = False):
        """
        FileFilter inicializálása
        
        Args:
            config: Konfiguráció
            verbose: Részletes kimenet
        """
        self.config = config
        self.verbose = verbose
        self.filters_config = config.get('filters', {})
        
        # Kizárt mappák
        self.exclude_dirs = set(self.filters_config.get('exclude_dirs', []))
        
        # Kizárt kiterjesztések
        self.exclude_extensions = set(self.filters_config.get('exclude_extensions', []))
        
        # Maximális fájlméret (KB-ban)
        self.max_file_size = self.filters_config.get('max_file_size', 200) * 1024  # Bájtba váltás
        
        # Bizalmas fájlnév minták
        self.sensitive_patterns = self.filters_config.get('sensitive_patterns', [])
        
        # Bizalmas tartalom minták (reguláris kifejezések)
        self.sensitive_content_patterns = []
        for pattern in self.filters_config.get('sensitive_content_patterns', []):
            try:
                self.sensitive_content_patterns.append(re.compile(pattern, re.IGNORECASE))
            except re.error as e:
                print(f"Figyelmeztetés: Érvénytelen reguláris kifejezés: {pattern} - {e}")
        
        if self.verbose:
            print(f"Kizárt mappák: {len(self.exclude_dirs)}")
            print(f"Kizárt kiterjesztések: {len(self.exclude_extensions)}")
            print(f"Maximális fájlméret: {self.max_file_size / 1024:.1f} KB")
            print(f"Bizalmas fájlnév minták: {len(self.sensitive_patterns)}")
            print(f"Bizalmas tartalom minták: {len(self.sensitive_content_patterns)}")
    
    def filter_files(self, files: List[FileInfo]) -> List[FileInfo]:
        """
        Fájlok szűrése a konfiguráció szerint
        
        Args:
            files: Szűrendő fájlok listája
            
        Returns:
            List[FileInfo]: Szűrt fájlok listája
        """
        filtered_files = []
        excluded_by_dir = 0
        excluded_by_ext = 0
        excluded_by_size = 0
        excluded_by_sensitive = 0
        excluded_by_content = 0
        
        if self.verbose:
            print("Fájlok szűrése...")
        
        for file_info in files:
            # Csak fájlokat dolgozunk fel (a könyvtárakat a fájlfa generálásánál kezeljük)
            if not file_info.is_file:
                continue
            
            # Mappa alapú szűrés
            if self._is_excluded_by_dir(file_info):
                excluded_by_dir += 1
                if self.verbose:
                    print(f"  Kizárva mappa alapján: {file_info.relative_path}")
                continue
            
            # Kiterjesztés alapú szűrés
            if self._is_excluded_by_extension(file_info):
                excluded_by_ext += 1
                if self.verbose:
                    print(f"  Kizárva kiterjesztés alapján: {file_info.relative_path}")
                continue
            
            # Méret alapú szűrés
            if self._is_excluded_by_size(file_info):
                excluded_by_size += 1
                if self.verbose:
                    print(f"  Kizárva méret alapján: {file_info.relative_path} ({file_info.size} bytes)")
                continue
            
            # Bizalmas fájlnév alapú szűrés
            if self._is_sensitive_filename(file_info):
                excluded_by_sensitive += 1
                if self.verbose:
                    print(f"  Kizárva bizalmas fájlnév alapján: {file_info.relative_path}")
                # A bizalmas fájlokat megőrizzük a listában, de jelezzük
                file_info.is_sensitive = True
                file_info.sensitive_reason = "filename"
                filtered_files.append(file_info)
                continue
            
            # Tartalom alapú szűrés
            is_sensitive, reason = self._has_sensitive_content(file_info)
            if is_sensitive:
                excluded_by_content += 1
                if self.verbose:
                    print(f"  Kizárva bizalmas tartalom alapján: {file_info.relative_path} ({reason})")
                # A bizalmas fájlokat megőrizzük a listában, de jelezzük
                file_info.is_sensitive = True
                file_info.sensitive_reason = reason
                filtered_files.append(file_info)
                continue
            
            # Normál fájl
            file_info.is_sensitive = False
            file_info.sensitive_reason = None
            filtered_files.append(file_info)
        
        if self.verbose:
            print(f"Szűrés eredménye:")
            print(f"  Eredeti fájlok: {len([f for f in files if f.is_file])}")
            print(f"  Kizárva mappa alapján: {excluded_by_dir}")
            print(f"  Kizárva kiterjesztés alapján: {excluded_by_ext}")
            print(f"  Kizárva méret alapján: {excluded_by_size}")
            print(f"  Kizárva bizalmas fájlnév alapján: {excluded_by_sensitive}")
            print(f"  Kizárva bizalmas tartalom alapán: {excluded_by_content}")
            print(f"  Feldolgozott fájlok: {len(filtered_files)}")
        
        return filtered_files
    
    def _is_excluded_by_dir(self, file_info: FileInfo) -> bool:
        """
        Ellenőrzi, hogy a fájl kizárt mappában van-e
        
        Args:
            file_info: Fájl információ
            
        Returns:
            bool: True ha kizárt mappában van
        """
        parts = file_info.relative_path.parts
        
        for part in parts[:-1]:  # Az utolsó rész a fájlnév
            if part in self.exclude_dirs:
                return True
        
        return False
    
    def _is_excluded_by_extension(self, file_info: FileInfo) -> bool:
        """
        Ellenőrzi, hogy a fájl kizárt kiterjesztésű-e
        
        Args:
            file_info: Fájl információ
            
        Returns:
            bool: True ha kizárt kiterjesztésű
        """
        return file_info.extension in self.exclude_extensions
    
    def _is_excluded_by_size(self, file_info: FileInfo) -> bool:
        """
        Ellenőrzi, hogy a fájl mérete meghaladja-e a limitet
        
        Args:
            file_info: Fájl információ
            
        Returns:
            bool: True ha túl nagy
        """
        return file_info.size > self.max_file_size
    
    def _is_sensitive_filename(self, file_info: FileInfo) -> bool:
        """
        Ellenőrzi, hogy a fájlnév bizalmas információt tartalmaz-e
        
        Args:
            file_info: Fájl információ
            
        Returns:
            bool: True ha bizalmas fájlnév
        """
        filename_lower = file_info.name.lower()
        
        for pattern in self.sensitive_patterns:
            if pattern.lower() in filename_lower:
                return True
        
        return False
    
    def _has_sensitive_content(self, file_info: FileInfo) -> Tuple[bool, str]:
        """
        Ellenőrzi, hogy a fájl tartalma bizalmas információt tartalmaz-e
        
        Args:
            file_info: Fájl információ
            
        Returns:
            Tuple[bool, str]: (van_bizalmas_tartalom, ok)
        """
        try:
            # Csak szöveges fájlokat ellenőrzünk
            if not self._is_text_file(file_info):
                return False, ""
            
            # Első 50 sor ellenőrzése
            with open(file_info.path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = []
                for i, line in enumerate(f):
                    if i >= 50:  # Csak az első 50 sort ellenőrizzük
                        break
                    lines.append(line)
                
                content = ''.join(lines)
                
                for pattern in self.sensitive_content_patterns:
                    if pattern.search(content):
                        return True, pattern.pattern
        
        except Exception as e:
            if self.verbose:
                print(f"  Hiba a fájl tartalmának ellenőrzésekor: {file_info.relative_path} - {e}")
        
        return False, ""
    
    def _is_text_file(self, file_info: FileInfo) -> bool:
        """
        Ellenőrzi, hogy a fájl szöveges fájl-e
        
        Args:
            file_info: Fájl információ
            
        Returns:
            bool: True ha szöveges fájl
        """
        # Bináris kiterjesztések
        binary_extensions = {
            '.exe', '.dll', '.so', '.dylib', '.bin', '.wasm', '.obj', '.o',
            '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.ico', '.svg', '.webp',
            '.mp3', '.mp4', '.avi', '.mov', '.wav', '.flac', '.ogg',
            '.zip', '.tar', '.gz', '.rar', '.7z', '.bz2', '.xz',
            '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx'
        }
        
        # Ha a kiterjesztés bináris, akkor nem szöveges
        if file_info.extension.lower() in binary_extensions:
            return False
        
        # Ha nincs kiterjesztése, valószínűleg szöveges
        if not file_info.extension:
            return True
        
        # Egyébként feltételezzük, hogy szöveges
        return True