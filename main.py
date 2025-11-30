#!/usr/bin/env python3
"""
GitIngest - Projekt fájlstruktúra és tartalom elemző LLM számára
"""

import argparse
import sys
from pathlib import Path

from config.config_manager import ConfigManager
from core.file_mapper import FileMapper
from core.file_filter import FileFilter
from core.content_extractor import ContentExtractor
from core.output_generator import OutputGenerator


def parse_arguments():
    """Parancssori argumentumok feldolgozása"""
    parser = argparse.ArgumentParser(
        description="Projekt fájlstruktúra és tartalom elemző LLM számára"
    )
    parser.add_argument(
        "project_path",
        help="A projektkönyvtár elérési útja"
    )
    parser.add_argument(
        "--config", "-c",
        help="Konfigurációs fájl elérési útja",
        default=None
    )
    parser.add_argument(
        "--output", "-o",
        help="Kimeneti fájl elérési útja",
        default=None
    )
    parser.add_argument(
        "--format", "-f",
        choices=["markdown", "json"],
        help="Kimeneti formátum",
        default=None
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Részletes kimenet"
    )
    return parser.parse_args()


def main():
    """Főprogram"""
    args = parse_arguments()
    
    # Projekt útvonal ellenőrzése
    project_path = Path(args.project_path)
    if not project_path.exists():
        print(f"Hiba: A megadott útvonal nem létezik: {project_path}")
        sys.exit(1)
    
    if not project_path.is_dir():
        print(f"Hiba: A megadott útvonal nem egy könyvtár: {project_path}")
        sys.exit(1)
    
    # Konfiguráció betöltése
    config_manager = ConfigManager(args.config)
    config = config_manager.load_config()
    
    # Parancssori argumentumok felülírják a konfigurációt
    if args.output:
        config["project"]["output_file"] = args.output
    if args.format:
        config["project"]["output_format"] = args.format
    
    # Komponensek inicializálása
    file_mapper = FileMapper(project_path, config, args.verbose)
    file_filter = FileFilter(config, args.verbose)
    content_extractor = ContentExtractor(config, args.verbose)
    output_generator = OutputGenerator(config, args.verbose)
    
    if args.verbose:
        print(f"Projekt feltérképezése: {project_path}")
    
    # Fájlok feltérképezése
    all_files = file_mapper.map_files()
    
    if args.verbose:
        print(f"Összes fájl: {len(all_files)}")
    
    # Fájlok szűrése
    filtered_files = file_filter.filter_files(all_files)
    
    if args.verbose:
        print(f"Szűrt fájlok: {len(filtered_files)}")
    
    # Tartalom kinyerése
    file_contents = content_extractor.extract_contents(filtered_files)
    
    if args.verbose:
        print(f"Tartalom kinyerve {len(file_contents)} fájlból")
    
    # Kimeneti generálása
    output_path = output_generator.generate_output(
        project_path, 
        all_files, 
        filtered_files, 
        file_contents
    )
    
    print(f"Kimenet létrehozva: {output_path}")


if __name__ == "__main__":
    main()