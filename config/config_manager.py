"""
Konfiguráció kezelő modul
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional


class ConfigManager:
    """Konfiguráció kezelő osztály"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Konfiguráció kezelő inicializálása
        
        Args:
            config_path: Egyéni konfigurációs fájl elérési útja
        """
        self.config_path = config_path
        self.default_config_path = Path(__file__).parent / "default_config.yaml"
        
    def load_config(self) -> Dict[str, Any]:
        """
        Konfiguráció betöltése
        
        Returns:
            Dict[str, Any]: Betöltött konfiguráció
        """
        # Alapértelmezett konfiguráció betöltése
        config = self._load_default_config()
        
        # Egyéni konfiguráció betöltése, ha meg van adva
        if self.config_path:
            custom_config = self._load_custom_config(self.config_path)
            config = self._merge_configs(config, custom_config)
        
        # Környezeti változók kezelése
        config = self._apply_env_overrides(config)
        
        return config
    
    def _load_default_config(self) -> Dict[str, Any]:
        """
        Alapértelmezett konfiguráció betöltése
        
        Returns:
            Dict[str, Any]: Alapértelmezett konfiguráció
        """
        try:
            with open(self.default_config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        except FileNotFoundError:
            print(f"Figyelmeztetés: Alapértelmezett konfigurációs fájl nem található: {self.default_config_path}")
            return {}
        except yaml.YAMLError as e:
            print(f"Hiba az alapértelmezett konfiguráció olvasásakor: {e}")
            return {}
    
    def _load_custom_config(self, config_path: str) -> Dict[str, Any]:
        """
        Egyéni konfiguráció betöltése
        
        Args:
            config_path: Konfigurációs fájl elérési útja
            
        Returns:
            Dict[str, Any]: Egyéni konfiguráció
        """
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        except FileNotFoundError:
            print(f"Figyelmeztetés: Egyéni konfigurációs fájl nem található: {config_path}")
            return {}
        except yaml.YAMLError as e:
            print(f"Hiba az egyéni konfiguráció olvasásakor: {e}")
            return {}
    
    def _merge_configs(self, default: Dict[str, Any], custom: Dict[str, Any]) -> Dict[str, Any]:
        """
        Konfigurációk összefűzése
        
        Args:
            default: Alapértelmezett konfiguráció
            custom: Egyéni konfiguráció
            
        Returns:
            Dict[str, Any]: Összefűzött konfiguráció
        """
        result = default.copy()
        
        for key, value in custom.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def _apply_env_overrides(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Környezeti változókkal való felülírás
        
        Args:
            config: Konfiguráció
            
        Returns:
            Dict[str, Any]: Módosított konfiguráció
        """
        # Kimeneti formátum
        if os.getenv('GITINGEST_OUTPUT_FORMAT'):
            config['project']['output_format'] = os.getenv('GITINGEST_OUTPUT_FORMAT')
        
        # Kimeneti fájl
        if os.getenv('GITINGEST_OUTPUT_FILE'):
            config['project']['output_file'] = os.getenv('GITINGEST_OUTPUT_FILE')
        
        # Maximális fájlméret
        if os.getenv('GITINGEST_MAX_FILE_SIZE'):
            try:
                config['filters']['max_file_size'] = int(os.getenv('GITINGEST_MAX_FILE_SIZE'))
            except ValueError:
                print(f"Figyelmeztetés: Érvénytelen GITINGEST_MAX_FILE_SIZE érték: {os.getenv('GITINGEST_MAX_FILE_SIZE')}")
        
        # Fájlfa mélység
        if os.getenv('GITINGEST_TREE_DEPTH'):
            try:
                config['tree']['max_depth'] = int(os.getenv('GITINGEST_TREE_DEPTH'))
            except ValueError:
                print(f"Figyelmeztetés: Érvénytelen GITINGEST_TREE_DEPTH érték: {os.getenv('GITINGEST_TREE_DEPTH')}")
        
        return config
    
    def save_config(self, config: Dict[str, Any], output_path: str) -> bool:
        """
        Konfiguráció mentése fájlba
        
        Args:
            config: Mentendő konfiguráció
            output_path: Kimeneti fájl elérési útja
            
        Returns:
            bool: Sikeres mentés
        """
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, default_flow_style=False, indent=2, allow_unicode=True)
            return True
        except Exception as e:
            print(f"Hiba a konfiguráció mentésekor: {e}")
            return False