"""
Kimeneti generátor modul - Markdown és JSON formátum generálása
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

from core.file_mapper import FileInfo
from core.content_extractor import FileContent


class OutputGenerator:
    """Kimeneti generátor osztály"""
    
    def __init__(self, config: Dict[str, Any], verbose: bool = False):
        """
        OutputGenerator inicializálása
        
        Args:
            config: Konfiguráció
            verbose: Részletes kimenet
        """
        self.config = config
        self.verbose = verbose
        self.project_config = config.get('project', {})
        self.output_config = config.get('output', {})
        self.tree_config = config.get('tree', {})
        
        # Kimeneti beállítások
        self.output_format = self.project_config.get('output_format', 'markdown')
        self.output_file = self.project_config.get('output_file', 'app_summary.md')
        self.include_metadata = self.output_config.get('include_metadata', True)
        self.include_file_stats = self.output_config.get('include_file_stats', True)
        
        if self.verbose:
            print(f"Kimeneti formátum: {self.output_format}")
            print(f"Kimeneti fájl: {self.output_file}")
    
    def generate_output(self, root_path: Path, all_files: List[FileInfo], 
                        filtered_files: List[FileInfo], 
                        file_contents: Dict[str, FileContent]) -> Path:
        """
        Kimeneti fájl generálása
        
        Args:
            root_path: Projekt gyökérkönyvtára
            all_files: Az összes fájl
            filtered_files: Szűrt fájlok
            file_contents: Fájlok tartalmai
            
        Returns:
            Path: Generált kimeneti fájl elérési útja
        """
        # Projekt nevének meghatározása
        project_name = self._get_project_name(root_path)
        
        # Statisztikák gyűjtése
        stats = self._collect_stats(all_files, filtered_files, file_contents)
        
        # Fájlfa generálása
        file_tree = self._generate_file_tree(all_files)
        
        if self.verbose:
            print(f"Kimeneti fájl generálása: {self.output_format} formátumban")
        
        # Kimeneti fájl generálása a formátum szerint
        if self.output_format.lower() == 'json':
            output_path = self._generate_json_output(
                project_name, root_path, stats, file_tree, filtered_files, file_contents
            )
        else:
            output_path = self._generate_markdown_output(
                project_name, root_path, stats, file_tree, filtered_files, file_contents
            )
        
        if self.verbose:
            print(f"Kimenet elmentve: {output_path}")
        
        return output_path
    
    def _get_project_name(self, root_path: Path) -> str:
        """
        Projekt nevének meghatározása
        
        Args:
            root_path: Projekt gyökérkönyvtára
            
        Returns:
            str: Projekt neve
        """
        # Ha a konfigurációban meg van adva
        if self.project_config.get('name') and self.project_config.get('name') != 'Auto-detected':
            return self.project_config['name']
        
        # Egyébként a könyvtárnév
        return root_path.name
    
    def _collect_stats(self, all_files: List[FileInfo], filtered_files: List[FileInfo], 
                      file_contents: Dict[str, FileContent]) -> Dict[str, Any]:
        """
        Statisztikák gyűjtése
        
        Args:
            all_files: Az összes fájl
            filtered_files: Szűrt fájlok
            file_contents: Fájlok tartalmai
            
        Returns:
            Dict[str, Any]: Statisztikák
        """
        stats = {
            'total_files': len([f for f in all_files if f.is_file]),
            'total_dirs': len([f for f in all_files if f.is_dir]),
            'processed_files': len(filtered_files),
            'content_files': len([c for c in file_contents.values() if c.content and not c.is_binary]),
            'binary_files': len([c for c in file_contents.values() if c.is_binary]),
            'sensitive_files': len([c for c in file_contents.values() if c.error and 'bizalmas' in c.error.lower()]),
            'error_files': len([c for c in file_contents.values() if c.error and 'bizalmas' not in c.error.lower()]),
            'total_size': sum(f.size for f in all_files if f.is_file),
            'largest_file': None,
            'most_common_extensions': {}
        }
        
        # Legnagyobb fájl
        files_with_size = [f for f in all_files if f.is_file and f.size > 0]
        if files_with_size:
            stats['largest_file'] = {
                'name': str(max(files_with_size, key=lambda f: f.size).relative_path),
                'size': max(files_with_size, key=lambda f: f.size).size
            }
        
        # Leggyakoribb kiterjesztések
        extension_counts = {}
        for file_info in all_files:
            if file_info.is_file and file_info.extension:
                ext = file_info.extension.lower()
                extension_counts[ext] = extension_counts.get(ext, 0) + 1
        
        # Top 10 kiterjesztés
        sorted_extensions = sorted(extension_counts.items(), key=lambda x: x[1], reverse=True)
        stats['most_common_extensions'] = dict(sorted_extensions[:10])
        
        return stats
    
    def _generate_file_tree(self, all_files: List[FileInfo]) -> str:
        """
        Fájlfa generálása
        
        Args:
            all_files: Az összes fájl
            
        Returns:
            str: Fájlfa szöveges formában
        """
        from core.file_mapper import FileMapper
        
        # Ideiglenes FileMapper létrehozása a fájlfa generálásához
        temp_mapper = FileMapper(all_files[0].root_path if all_files else Path('.'), self.config, False)
        return temp_mapper.get_directory_tree(all_files, self.tree_config.get('max_depth', 5))
    
    def _generate_markdown_output(self, project_name: str, root_path: Path, stats: Dict[str, Any], 
                                 file_tree: str, filtered_files: List[FileInfo], 
                                 file_contents: Dict[str, FileContent]) -> Path:
        """
        Markdown kimeneti fájl generálása
        
        Args:
            project_name: Projekt neve
            root_path: Projekt gyökérkönyvtára
            stats: Statisztikák
            file_tree: Fájlfa
            filtered_files: Szűrt fájlok
            file_contents: Fájlok tartalmai
            
        Returns:
            Path: Generált kimeneti fájl elérési útja
        """
        output_path = Path(self.output_file)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            # Fejléc
            f.write(f"# Projekt Összefoglaló: {project_name}\n\n")
            f.write(f"**Generálva:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"**Gyökérkönyvtár:** {root_path}\n\n")
            
            # Statisztikák
            if self.include_file_stats:
                f.write("## Statisztikák\n\n")
                f.write(f"- **Összes fájl:** {stats['total_files']}\n")
                f.write(f"- **Összes könyvtár:** {stats['total_dirs']}\n")
                f.write(f"- **Feldolgozott fájlok:** {stats['processed_files']}\n")
                f.write(f"- **Tartalommal rendelkező fájlok:** {stats['content_files']}\n")
                f.write(f"- **Bináris fájlok:** {stats['binary_files']}\n")
                f.write(f"- **Bizalmas fájlok:** {stats['sensitive_files']}\n")
                f.write(f"- **Hibás fájlok:** {stats['error_files']}\n")
                f.write(f"- **Teljes méret:** {self._format_size(stats['total_size'])}\n")
                
                if stats['largest_file']:
                    f.write(f"- **Legnagyobb fájl:** {stats['largest_file']['name']} ({self._format_size(stats['largest_file']['size'])})\n")
                
                if stats['most_common_extensions']:
                    f.write("\n### Leggyakoribb kiterjesztések\n\n")
                    for ext, count in stats['most_common_extensions'].items():
                        f.write(f"- **{ext or '(nincs)'}:** {count}\n")
                
                f.write("\n")
            
            # Fájlfa
            f.write("## 1. Fájlstruktúra\n\n")
            f.write("```\n")
            f.write(file_tree)
            f.write("\n```\n\n")
            
            # Fájltartalmak
            f.write("## 2. Fájltartalmak\n\n")
            
            # Rendezés fájlnév szerint
            sorted_contents = sorted(file_contents.items(), key=lambda x: x[0])
            
            for file_path, file_content in sorted_contents:
                file_info = file_content.file_info
                
                # Fájl fejléce
                f.write(f"### [{file_path}]\n")
                
                # Metaadatok
                if self.include_metadata:
                    f.write(f"**Méret:** {self._format_size(file_info.size)}")
                    if file_content.encoding:
                        f.write(f" | **Kódolás:** {file_content.encoding}")
                    if file_content.line_count > 0:
                        f.write(f" | **Sorok:** {file_content.line_count}")
                    if file_content.truncated:
                        f.write(f" | **Levágva:** igen")
                    f.write("\n\n")
                
                # Tartalom
                if file_content.error:
                    f.write(f"**Hiba:** {file_content.error}\n\n")
                elif file_content.is_binary:
                    f.write(f"{file_content.content}\n\n")
                else:
                    # Kiterjesztés meghatározása
                    extension = file_info.extension.lower()
                    if not extension:
                        # Ha nincs kiterjesztése, próbáljuk a fájlnévből
                        if file_info.name in ['.gitignore', '.gitattributes', '.editorconfig', '.dockerfile']:
                            extension = file_info.name
                    
                    # Nyelv meghatározása
                    language = self._get_language_from_extension(extension)
                    
                    f.write(f"```{language}\n")
                    f.write(file_content.content)
                    f.write("\n```\n\n")
            
            # Lábléc
            f.write("---\n")
            f.write("*Generálva a GitIngest segítségével*\n")
        
        return output_path
    
    def _generate_json_output(self, project_name: str, root_path: Path, stats: Dict[str, Any], 
                              file_tree: str, filtered_files: List[FileInfo], 
                              file_contents: Dict[str, FileContent]) -> Path:
        """
        JSON kimeneti fájl generálása
        
        Args:
            project_name: Projekt neve
            root_path: Projekt gyökérkönyvtára
            stats: Statisztikák
            file_tree: Fájlfa
            filtered_files: Szűrt fájlok
            file_contents: Fájlok tartalmai
            
        Returns:
            Path: Generált kimeneti fájl elérési útja
        """
        output_path = Path(self.output_file)
        
        # JSON struktúra építése
        output_data = {
            'project': {
                'name': project_name,
                'root_path': str(root_path),
                'generated_at': datetime.now().isoformat(),
                'generator': 'GitIngest'
            },
            'stats': stats,
            'file_tree': file_tree,
            'files': {}
        }
        
        # Fájlok adatainak hozzáadása
        for file_path, file_content in file_contents.items():
            file_info = file_content.file_info
            
            file_data = {
                'path': str(file_info.relative_path),
                'size': file_info.size,
                'is_file': file_info.is_file,
                'is_dir': file_info.is_dir,
                'extension': file_info.extension,
                'modified_time': file_info.modified_time
            }
            
            # Metaadatok
            if self.include_metadata:
                file_data['metadata'] = {}
                if file_content.encoding:
                    file_data['metadata']['encoding'] = file_content.encoding
                if file_content.line_count > 0:
                    file_data['metadata']['line_count'] = file_content.line_count
                if file_content.truncated:
                    file_data['metadata']['truncated'] = True
            
            # Tartalom
            if file_content.error:
                file_data['error'] = file_content.error
            elif file_content.is_binary:
                file_data['binary'] = True
                if file_content.content:
                    file_data['info'] = file_content.content
            else:
                file_data['content'] = file_content.content
                file_data['language'] = self._get_language_from_extension(file_info.extension.lower())
            
            output_data['files'][file_path] = file_data
        
        # JSON fájl írása
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        return output_path
    
    def _format_size(self, size_bytes: int) -> str:
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
    
    def _get_language_from_extension(self, extension: str) -> str:
        """
        Nyelv meghatározása kiterjesztésből
        
        Args:
            extension: Fájlkiterjesztés
            
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
        
        return extension_map.get(extension.lower(), 'text')