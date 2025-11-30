"""
Tartalomkinyerő modul - fájltartalmak biztonságos kinyerése
"""

import chardet
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from core.file_mapper import FileInfo
from core.database_analyzer import DatabaseAnalyzer, DatabaseInfo


class FileContent:
    """Fájltartalmat tároló osztály"""
    
    def __init__(self, file_info: FileInfo, content: Optional[str] = None,
                 encoding: Optional[str] = None, error: Optional[str] = None,
                 is_binary: bool = False, truncated: bool = False,
                 database_info: Optional[DatabaseInfo] = None):
        """
        FileContent inicializálása
        
        Args:
            file_info: Fájl információ
            content: Fájl tartalma
            encoding: Karakterkódolás
            error: Hibaüzenet
            is_binary: Bináris fájl-e
            truncated: Levágott tartalom-e
            database_info: Adatbázis információ (ha adatbázis fájl)
        """
        self.file_info = file_info
        self.content = content
        self.encoding = encoding
        self.error = error
        self.is_binary = is_binary
        self.truncated = truncated
        self.database_info = database_info
        self.line_count = len(content.splitlines()) if content else 0


class ContentExtractor:
    """Tartalomkinyerő osztály"""
    
    def __init__(self, config: Dict[str, Any], verbose: bool = False):
        """
        ContentExtractor inicializálása
        
        Args:
            config: Konfiguráció
            verbose: Részletes kimenet
        """
        self.config = config
        self.verbose = verbose
        self.output_config = config.get('output', {})
        self.max_content_lines = self.output_config.get('max_content_lines', 5000)
        self.include_binary_info = self.output_config.get('include_binary_info', True)
        self.analyze_databases = self.output_config.get('analyze_databases', True)
        
        # Adatbázis elemző inicializálása
        self.database_analyzer = DatabaseAnalyzer(config=config, verbose=self.verbose)
        
        # Támogatott szöveges kiterjesztések
        self.text_extensions = {
            # Programozási nyelvek
            '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.c', '.cpp', '.cc', '.cxx',
            '.h', '.hpp', '.cs', '.php', '.rb', '.go', '.rs', '.swift', '.kt', '.scala',
            '.dart', '.lua', '.r', '.m', '.pl', '.sh', '.bash', '.zsh', '.fish',
            '.sql', '.html', '.htm', '.xml', '.css', '.scss', '.sass', '.less',
            '.vue', '.svelte', '.elm', '.hs', '.ml', '.clj', '.cljs', '.ex', '.exs',
            
            # Konfigurációs fájlok
            '.json', '.yaml', '.yml', '.toml', '.ini', '.cfg', '.conf', '.config',
            '.env', '.properties', '.plist', '.xml', '.dockerfile', 'dockerfile',
            
            # Dokumentumok
            '.md', '.markdown', '.txt', '.rst', '.adoc', '.tex', '.log',
            
            # Web fájlok
            '.html', '.htm', '.css', '.scss', '.sass', '.less', '.styl',
            
            # Szkriptek
            '.py', '.js', '.ts', '.jsx', '.tsx', '.sh', '.bash', '.zsh', '.fish',
            '.pl', '.rb', '.php', '.lua', '.r', '.m', '.go', '.rs', '.java',
            '.cs', '.cpp', '.c', '.h', '.hpp', '.scala', '.kt', '.swift',
            
            # Adatfájlok
            '.csv', '.tsv', '.json', '.xml', '.yaml', '.yml', '.toml', '.ini',
            '.cfg', '.conf', '.config', '.properties', '.sql',
            
            # Egyéb
            '.gitignore', '.gitattributes', '.editorconfig', '.eslintrc', '.prettierrc',
            '.babelrc', '.dockerignore', '.npmignore', '.hgignore', '.svnignore'
        }
        
        if self.verbose:
            print(f"Tartalomkinyerő inicializálva")
            print(f"Maximális sorok száma fájlonként: {self.max_content_lines}")
    
    def extract_contents(self, filtered_files: List[FileInfo]) -> Dict[str, FileContent]:
        """
        Fájltartalmak kinyerése
        
        Args:
            filtered_files: Szűrt fájlok listája
            
        Returns:
            Dict[str, FileContent]: Fájlok tartalmai
        """
        contents = {}
        successful = 0
        failed = 0
        binary_files = 0
        sensitive_files = 0
        
        if self.verbose:
            print("Fájltartalmak kinyerése...")
        
        for file_info in filtered_files:
            content_key = str(file_info.relative_path)
            
            # Bizalmas fájlok kezelése
            if hasattr(file_info, 'is_sensitive') and file_info.is_sensitive:
                contents[content_key] = FileContent(
                    file_info=file_info,
                    content=None,
                    error=f"Bizalmas tartalom ({file_info.sensitive_reason})",
                    is_binary=False
                )
                sensitive_files += 1
                continue
            
            # Tartalom kinyerése
            file_content = self._extract_file_content(file_info)
            contents[content_key] = file_content
            
            if file_content.error:
                failed += 1
                if self.verbose:
                    print(f"  Hiba: {file_info.relative_path} - {file_content.error}")
            elif file_content.is_binary:
                binary_files += 1
            else:
                successful += 1
            
            if self.verbose and len(contents) % 50 == 0:
                print(f"  {len(contents)} fájl feldolgozva...")
        
        if self.verbose:
            print(f"Tartalomkinyerés eredménye:")
            print(f"  Sikeres: {successful}")
            print(f"  Sikertelen: {failed}")
            print(f"  Bináris fájlok: {binary_files}")
            print(f"  Bizalmas fájlok: {sensitive_files}")
            print(f"  Összesen: {len(contents)}")
        
        return contents
    
    def _extract_file_content(self, file_info: FileInfo) -> FileContent:
        """
        Egyetlen fájl tartalmának kinyerése
        
        Args:
            file_info: Fájl információ
            
        Returns:
            FileContent: Fájl tartalma
        """
        try:
            # Ha a fájl nem létezik
            if not file_info.path.exists():
                return FileContent(
                    file_info=file_info,
                    error="A fájl nem létezik"
                )
            
            # Ha a fájl túl nagy
            if file_info.size > 10 * 1024 * 1024:  # 10MB
                return FileContent(
                    file_info=file_info,
                    error="A fájl túl nagy (10MB feletti)"
                )
            
            # Adatbázis fájlok ellenőrzése - EZT MIELŐTT KELL TENNI, MINT A SZÖVEGES FELDOLGOZÁST
            if self.analyze_databases and self.database_analyzer.is_database_file(file_info):
                if self.verbose:
                    print(f"  Adatbázis fájl észlelve: {file_info.relative_path}")
                return self._create_binary_content(file_info)
            
            # Karakterkódolás detektálása
            encoding = self._detect_encoding(file_info.path)
            
            if encoding is None:
                # Ha nem sikerült a kódolás detektálása, próbáljuk UTF-8-ként
                try:
                    with open(file_info.path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    encoding = 'utf-8'
                except UnicodeDecodeError:
                    # Ha UTF-8 sem működik, akkor binárisnak tekintjük
                    return self._create_binary_content(file_info)
            else:
                # Sikeres kódolás detektálás
                try:
                    with open(file_info.path, 'r', encoding=encoding) as f:
                        content = f.read()
                except UnicodeDecodeError:
                    # Ha a detektált kódolással sem sikerül, próbáljuk UTF-8-ként
                    try:
                        with open(file_info.path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        encoding = 'utf-8'
                    except UnicodeDecodeError:
                        # Ha ez sem működik, akkor binárisnak tekintjük
                        return self._create_binary_content(file_info)
            
            # Tartalom levágása, ha túl hosszú
            truncated = False
            if self.max_content_lines > 0:
                lines = content.splitlines()
                if len(lines) > self.max_content_lines:
                    content = '\n'.join(lines[:self.max_content_lines])
                    content += f"\n\n[... Tartalom levágva {len(lines)} sorból {self.max_content_lines} sorra ...]"
                    truncated = True
            
            return FileContent(
                file_info=file_info,
                content=content,
                encoding=encoding,
                is_binary=False,
                truncated=truncated
            )
        
        except Exception as e:
            return FileContent(
                file_info=file_info,
                error=f"Hiba a fájl olvasásakor: {str(e)}"
            )
    
    def _detect_encoding(self, file_path: Path) -> Optional[str]:
        """
        Karakterkódolás detektálása
        
        Args:
            file_path: Fájl elérési útja
            
        Returns:
            Optional[str]: Detektált kódolás vagy None
        """
        try:
            # Első 10KB olvasása a detektáláshoz
            with open(file_path, 'rb') as f:
                raw_data = f.read(10240)
            
            result = chardet.detect(raw_data)
            
            # Ha a megbízhatóság túl alacsony, nem fogadjuk el
            if result and result.get('confidence', 0) > 0.7:
                encoding = result.get('encoding')
                if encoding:
                    return encoding.lower()
            
            return None
        
        except Exception:
            return None
    
    def _create_binary_content(self, file_info: FileInfo) -> FileContent:
        """
        Bináris fájl tartalmának létrehozása
        
        Args:
            file_info: Fájl információ
            
        Returns:
            FileContent: Bináris fájl tartalma
        """
        # Adatbázis fájlok elemzése, ha engedélyezve van
        database_info = None
        content = None
        
        if self.analyze_databases:
            database_info = self.database_analyzer.analyze_database(file_info)
            
            if database_info:
                # Adatbázis információk hozzáadása a tartalomhoz - CSAK METAADATOK
                content_lines = [
                    f"[Adatbázis fájl - {database_info.db_type}]",
                    f"Fájl mérete: {file_info.size} bytes"
                ]
                
                # Verzió információ hozzáadása, ha elérhető
                if hasattr(database_info, 'version') and database_info.version:
                    content_lines.append(f"Verzió: {database_info.version}")
                
                # Táblák száma
                if database_info.table_count is not None:
                    content_lines.append(f"Táblák száma: {database_info.table_count}")
                
                # Méret információk
                if database_info.size_info:
                    if 'page_size' in database_info.size_info:
                        content_lines.append(f"Page méret: {database_info.size_info['page_size']} bytes")
                    if 'page_count' in database_info.size_info:
                        content_lines.append(f"Page-ek száma: {database_info.size_info['page_count']}")
                    if 'estimated_size' in database_info.size_info:
                        content_lines.append(f"Becsült adatbázis méret: {database_info.size_info['estimated_size']} bytes")
                    if 'file_type' in database_info.size_info:
                        content_lines.append(f"Fájl típus: {database_info.size_info['file_type']}")
                
                # Séma információk (csak összefoglaló, nem a teljes séma)
                if database_info.schema_info:
                    if isinstance(database_info.schema_info, dict):
                        table_names = list(database_info.schema_info.keys())
                        if table_names:
                            content_lines.append(f"Táblák: {', '.join(table_names)}")
                            # Oszlopok száma az első néhány táblához
                            for table_name in table_names[:3]:  # Csak az első 3 tábla
                                table_info = database_info.schema_info[table_name]
                                if 'columns' in table_info and isinstance(table_info['columns'], list):
                                    content_lines.append(f"  - {table_name}: {len(table_info['columns'])} oszlop")
                    else:
                        # Ha a schema_info string formátumú
                        content_lines.append("Séma információk elérhetők")
                
                content = "\n".join(content_lines)
            elif self.include_binary_info:
                content = f"[Bináris fájl - {file_info.size} bytes]"
        elif self.include_binary_info:
            content = f"[Bináris fájl - {file_info.size} bytes]"
        
        return FileContent(
            file_info=file_info,
            content=content,
            is_binary=True,
            database_info=database_info
        )
    
    def _is_text_file(self, file_info: FileInfo) -> bool:
        """
        Ellenőrzi, hogy a fájl szöveges fájl-e
        
        Args:
            file_info: Fájl információ
            
        Returns:
            bool: True ha szöveges fájl
        """
        # Ha a kiterjesztés ismert szöveges kiterjesztés
        if file_info.extension.lower() in self.text_extensions:
            return True
        
        # Ha nincs kiterjesztése, de a neve ismert szöveges fájlnév
        if not file_info.extension and file_info.name in [
            '.gitignore', '.gitattributes', '.editorconfig', '.eslintrc', 
            '.prettierrc', '.babelrc', '.dockerignore', '.npmignore', 
            '.hgignore', '.svnignore', 'dockerfile', 'makefile'
        ]:
            return True
        
        # Egyébként próbáljuk meg detektálni
        return self._detect_encoding(file_info.path) is not None