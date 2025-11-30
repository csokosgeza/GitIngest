"""
Adatbázis elemző modul - adatbázis fájlok metaadatainak kinyerése
"""

import struct
import sqlite3
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import re

from core.file_mapper import FileInfo


class DatabaseInfo:
    """Adatbázis információkat tároló osztály"""
    
    def __init__(self, file_info: FileInfo, db_type: str, 
                 table_count: Optional[int] = None, 
                 schema_info: Optional[Dict[str, Any]] = None,
                 size_info: Optional[Dict[str, Any]] = None):
        """
        DatabaseInfo inicializálása
        
        Args:
            file_info: Fájl információ
            db_type: Adatbázis típusa
            table_count: Táblák száma
            schema_info: Séma információk
            size_info: Méret információk
        """
        self.file_info = file_info
        self.db_type = db_type
        self.table_count = table_count
        self.schema_info = schema_info or {}
        self.size_info = size_info or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Konvertálás dict-be"""
        return {
            'file_path': str(self.file_info.relative_path),
            'file_size': self.file_info.size,
            'db_type': self.db_type,
            'table_count': self.table_count,
            'schema_info': self.schema_info,
            'size_info': self.size_info
        }


class DatabaseAnalyzer:
    """Adatbázis elemző osztály"""
    
    def __init__(self, config: Dict[str, Any], verbose: bool = False):
        """
        DatabaseAnalyzer inicializálása
        
        Args:
            config: Konfiguráció
            verbose: Részletes kimenet
        """
        self.config = config
        self.verbose = verbose
        self.db_config = config.get('database_analysis', {})
        
        # Adatbázis fájlok kiterjesztései
        self.database_extensions = {}
        
        # SQLite
        for ext in ['.db', '.sqlite', '.sqlite3']:
            self.database_extensions[ext] = 'sqlite'
        
        # MySQL
        for ext in ['.frm', '.myd', '.myi', '.ibd']:
            self.database_extensions[ext] = 'mysql'
        
        # PostgreSQL
        for ext in ['.pgc', '.pgd']:
            self.database_extensions[ext] = 'postgresql'
        
        # MongoDB
        for ext in ['.bson', '.wt']:
            self.database_extensions[ext] = 'mongodb'
        
        # Redis
        self.database_extensions['.rdb'] = 'redis'
        
        # Microsoft Access
        for ext in ['.mdb', '.accdb']:
            self.database_extensions[ext] = 'access'
        
        # dBASE
        for ext in ['.dbf', '.dbc']:
            self.database_extensions[ext] = 'dbase'
        
        # Egyéb
        self.database_extensions['.db'] = 'generic_database'
        
        if self.verbose:
            print(f"Adatbázis elemző inicializálva")
            print(f"Adatbázis elemzés engedélyezve: {self.db_config.get('enabled', True)}")
    
    def is_database_file(self, file_info: FileInfo) -> bool:
        """
        Ellenőrzi, hogy a fájl adatbázis fájl-e
        
        Args:
            file_info: Fájl információ
            
        Returns:
            bool: True ha adatbázis fájl
        """
        if not self.db_config.get('enabled', True):
            return False
        
        extension = file_info.extension.lower()
        
        # Pontos egyezés keresése
        for ext_pattern, db_type in self.database_extensions.items():
            if isinstance(ext_pattern, tuple):
                if extension in ext_pattern:
                    return True
            elif extension == ext_pattern:
                return True
        
        return False
    
    def get_database_type(self, file_info: FileInfo) -> Optional[str]:
        """
        Meghatározza az adatbázis típusát
        
        Args:
            file_info: Fájl információ
            
        Returns:
            Optional[str]: Adatbázis típusa vagy None
        """
        extension = file_info.extension.lower()
        
        for ext_pattern, db_type in self.database_extensions.items():
            if isinstance(ext_pattern, tuple):
                if extension in ext_pattern:
                    return db_type
            elif extension == ext_pattern:
                return db_type
        
        return None
    
    def analyze_database(self, file_info: FileInfo) -> Optional[DatabaseInfo]:
        """
        Adatbázis fájl elemzése
        
        Args:
            file_info: Fájl információ
            
        Returns:
            Optional[DatabaseInfo]: Adatbázis információk vagy None
        """
        if not self.is_database_file(file_info):
            return None
        
        db_type = self.get_database_type(file_info)
        
        if self.verbose:
            print(f"  Adatbázis fájl elemzése: {file_info.relative_path} ({db_type})")
        
        try:
            if db_type == 'sqlite':
                return self._analyze_sqlite(file_info)
            elif db_type == 'mysql':
                return self._analyze_mysql(file_info)
            elif db_type == 'postgresql':
                return self._analyze_postgresql(file_info)
            elif db_type == 'mongodb':
                return self._analyze_mongodb(file_info)
            elif db_type == 'redis':
                return self._analyze_redis(file_info)
            else:
                return self._analyze_generic(file_info, db_type)
        
        except Exception as e:
            if self.verbose:
                print(f"    Hiba az adatbázis elemzésekor: {e}")
            return DatabaseInfo(file_info, db_type or 'unknown')
    
    def _analyze_sqlite(self, file_info: FileInfo) -> DatabaseInfo:
        """SQLite adatbázis elemzése"""
        try:
            # Kapcsolódás az adatbázishoz (read-only módban)
            conn = sqlite3.connect(f"file:{file_info.path}?mode=ro", uri=True)
            cursor = conn.cursor()
            
            # Táblák száma
            cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
            table_count = cursor.fetchone()[0]
            
            schema_info = {}
            if self.db_config.get('extract_schema', False):
                # Táblák sémájának kinyerése
                cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='table'")
                tables = cursor.fetchall()
                
                for table_name, create_sql in tables:
                    # Oszlopok kinyerése
                    cursor.execute(f"PRAGMA table_info({table_name})")
                    columns = cursor.fetchall()
                    
                    schema_info[table_name] = {
                        'create_sql': create_sql,
                        'columns': [
                            {
                                'name': col[1],
                                'type': col[2],
                                'not_null': bool(col[3]),
                                'default_value': col[4],
                                'primary_key': bool(col[5])
                            }
                            for col in columns
                        ]
                    }
            
            # Adatbázis méret információk
            cursor.execute("PRAGMA page_size")
            page_size = cursor.fetchone()[0]
            cursor.execute("PRAGMA page_count")
            page_count = cursor.fetchone()[0]
            
            size_info = {
                'page_size': page_size,
                'page_count': page_count,
                'estimated_size': page_size * page_count
            }
            
            conn.close()
            
            return DatabaseInfo(
                file_info=file_info,
                db_type='sqlite',
                table_count=table_count,
                schema_info=schema_info,
                size_info=size_info
            )
            
        except Exception as e:
            if self.verbose:
                print(f"    SQLite elemzési hiba: {e}")
            return DatabaseInfo(file_info, 'sqlite')
    
    def _analyze_mysql(self, file_info: FileInfo) -> DatabaseInfo:
        """MySQL adatbázis fájl elemzése"""
        # MySQL fájlok binárisak, csak alapvető információkat tudunk kinyerni
        extension = file_info.extension.lower()
        
        file_type_info = {
            '.frm': 'Table definition file',
            '.myd': 'MyISAM data file',
            '.myi': 'MyISAM index file',
            '.ibd': 'InnoDB data file'
        }
        
        size_info = {
            'file_type': file_type_info.get(extension, 'Unknown MySQL file'),
            'binary_format': True
        }
        
        return DatabaseInfo(
            file_info=file_info,
            db_type='mysql',
            table_count=None,
            size_info=size_info
        )
    
    def _analyze_postgresql(self, file_info: FileInfo) -> DatabaseInfo:
        """PostgreSQL adatbázis fájl elemzése"""
        extension = file_info.extension.lower()
        
        file_type_info = {
            '.pgc': 'PostgreSQL global cache file',
            '.pgd': 'PostgreSQL data file'
        }
        
        size_info = {
            'file_type': file_type_info.get(extension, 'Unknown PostgreSQL file'),
            'binary_format': True
        }
        
        return DatabaseInfo(
            file_info=file_info,
            db_type='postgresql',
            table_count=None,
            size_info=size_info
        )
    
    def _analyze_mongodb(self, file_info: FileInfo) -> DatabaseInfo:
        """MongoDB adatbázis fájl elemzése"""
        extension = file_info.extension.lower()
        
        file_type_info = {
            '.bson': 'MongoDB BSON data file',
            '.wt': 'MongoDB WiredTiger data file'
        }
        
        size_info = {
            'file_type': file_type_info.get(extension, 'Unknown MongoDB file'),
            'binary_format': True
        }
        
        return DatabaseInfo(
            file_info=file_info,
            db_type='mongodb',
            table_count=None,
            size_info=size_info
        )
    
    def _analyze_redis(self, file_info: FileInfo) -> DatabaseInfo:
        """Redis adatbázis fájl elemzése"""
        size_info = {
            'file_type': 'Redis RDB file',
            'binary_format': True
        }
        
        return DatabaseInfo(
            file_info=file_info,
            db_type='redis',
            table_count=None,
            size_info=size_info
        )
    
    def _analyze_generic(self, file_info: FileInfo, db_type: str) -> DatabaseInfo:
        """Általános adatbázis fájl elemzése"""
        size_info = {
            'file_type': f'{db_type} database file',
            'binary_format': True
        }
        
        return DatabaseInfo(
            file_info=file_info,
            db_type=db_type,
            table_count=None,
            size_info=size_info
        )