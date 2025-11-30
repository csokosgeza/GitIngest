# GitIngest

<p align="center">
  <img src="gitingest_fedlap.png" alt="GitIngest Fedlap">
</p>

[![Python Version](https://img.shields.io/badge/python-3.7%2B-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A GitIngest egy Python program, amely egy adott projektkönyvtár fájlstruktúráját feltérképezi, a forrásfájlok tartalmát kigyűjti, és egy strukturált, tömörített szöveges formátumban (Markdown vagy JSON) rendezi, amelyet egy Nagy Nyelvi Modell (LLM) könnyedén elemezhet.

## 🎯 Fő Funkciók

- **Rekurzív fájltérképezés**: Teljes projektstruktúra feltérképezése
- **Intelligens szűrés**: .gitignore alapú szűrés, kiterjesztés és méret alapú kizárás
- **Biztonságos tartalomkezelés**: Bizalmas adatok automatikus detektálása és kizárása
- **Adatbázis elemzés**: Több adatbázis típus támogatása metaadatok kinyerésével
- **Több formátum**: Markdown és JSON kimeneti formátumok támogatása
- **Konfigurálhatóság**: YAML konfigurációs fájl és parancssori argumentumok
- **LLM-optimalizált kimenet**: Strukturált, könnyen feldolgozható kimenet

## 📦 Telepítés

1. Klónozd a repository-t:
```bash
git clone https://github.com/csokosgeza/GitIngest.git
cd GitIngest
```

2. Telepítsd a függőségeket:
```bash
pip install -r requirements.txt
```

## 🚀 Gyors Kezdés

### Alap használat

```bash
python main.py /path/to/project
```

### Konfigurációs fájl megadása

```bash
python main.py /path/to/project --config examples/sample_config.yaml
```

### Kimeneti fájl és formátum megadása

```bash
python main.py /path/to/project --output my_summary.md --format markdown
```

### Részletes kimenet

```bash
python main.py /path/to/project --verbose
```

## ⚙️ Konfiguráció

A program YAML konfigurációs fájllal állítható be. A konfigurációs fájlban a következőket lehet beállítani:

### Projekt beállítások

```yaml
project:
  name: "My Project"  # Projekt neve
  output_format: "markdown"  # markdown vagy json
  output_file: "project_summary.md"
```

### Szűrési beállítások

```yaml
filters:
  # Kizárt mappák
  exclude_dirs:
    - "node_modules"
    - "vendor"
    - "build"
    - "dist"
    - ".git"
    - "__pycache__"
  
  # Kizárt fájlkiterjesztések
  exclude_extensions:
    - ".log"
    - ".tmp"
    - ".zip"
    - ".min.js"
    - ".lock"
  
  # Maximális fájlméret (KB)
  max_file_size: 200
  
  # Bizalmas fájlok nevei
  sensitive_patterns:
    - "secret"
    - "key"
    - "credential"
    - "password"
    - ".env"
  
  # Bizalmas tartalom minták
  sensitive_content_patterns:
    - "API_KEY\\s*="
    - "password\\s*="
    - "client_secret\\s*="
```

### Fájlfa beállítások

```yaml
tree:
  max_depth: 5  # Maximális mélység
  show_hidden: false  # Rejtett fájlok mutatása
```

### Kimeneti beállítások

```yaml
output:
  include_metadata: true  # Fájlméret, módosítás dátuma
  include_file_stats: true  # Statisztikák
  max_content_lines: 5000  # Maximális sorok száma fájlonként
  include_binary_info: true  # Információ a bináris fájlokról
  analyze_databases: true  # Adatbázis fájlok elemzése metaadatok kinyeréséhez
```

### Adatbázis elemzési beállítások

```yaml
database_analysis:
  enabled: true  # Adatbázis elemzés engedélyezése
  extract_schema: false  # Séma információk kinyerése (SQLite esetén)
```

## 🗄️ Adatbázis Elemzés

A GitIngest támogatja a különböző adatbázis fájlok elemzését és metaadatainak kinyerését:

### Támogatott Adatbázis Típusok

- **SQLite**: `.db`, `.sqlite`, `.sqlite3`
  - Táblák számának kinyerése
  - Opcionális séma információk (oszlopok, típusok, kulcsok)
  - Méret információk (oldalméret, oldalszám)

- **MySQL**: `.frm`, `.myd`, `.myi`, `.ibd`
  - Fájl típus azonosítása (tábla definíció, adat, index)
  - Bináris formátum információk

- **PostgreSQL**: `.pgc`, `.pgd`
  - Fájl típus azonosítása (globális cache, adatfájl)
  - Bináris formátum információk

- **MongoDB**: `.bson`, `.wt`
  - Fájl típus azonosítása (BSON adat, WiredTiger adat)
  - Bináris formátum információk

- **Redis**: `.rdb`
  - Redis RDB fájl azonosítása
  - Bináris formátum információk

- **Microsoft Access**: `.mdb`, `.accdb`
  - Access adatbázis fájl azonosítása
  - Bináris formátum információk

- **dBASE**: `.dbf`, `.dbc`
  - dBASE adatbázis fájl azonosítása
  - Bináris formátum információk

### Adatbázis Elemzés Konfigurációja

Az adatbázis elemzés a `config/default_config.yaml` vagy egyéni konfigurációs fájlban állítható be:

```yaml
# Kimeneti beállítások
output:
  include_binary_info: true  # Információ a bináris fájlokról
  analyze_databases: true  # Adatbázis fájlok elemzése metaadatok kinyeréséhez

# Adatbázis elemzési beállítások
database_analysis:
  enabled: true  # Adatbázis elemzés engedélyezése
  extract_schema: false  # Séma információk kinyerése (SQLite esetén)
```

### Adatbázis Információk a Kimeneti Fájlban

A kimeneti fájlban az adatbázis fájlok a következő információkat tartalmazzák:

**Markdown formátumban:**
```markdown
### [data/database.sqlite]
**Méret:** 2.5 MB | **Adatbázis típusa:** sqlite | **Táblák száma:** 5

**Séma információ:**
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL
);
```
```

**JSON formátumban:**
```json
{
  "data/database.sqlite": {
    "path": "data/database.sqlite",
    "size": 2621440,
    "binary": true,
    "database": {
      "type": "sqlite",
      "table_count": 5,
      "schema_info": {
        "users": {
          "create_sql": "CREATE TABLE users (...)",
          "columns": [
            {
              "name": "id",
              "type": "INTEGER",
              "not_null": true,
              "primary_key": true
            }
          ]
        }
      }
    }
  }
}
```

## 📋 Parancssori Argumentumok

- `project_path`: A projektkönyvtár elérési útja (kötelező)
- `--config, -c`: Konfigurációs fájl elérési útja
- `--output, -o`: Kimeneti fájl elérési útja
- `--format, -f`: Kimeneti formátum (markdown vagy json)
- `--verbose, -v`: Részletes kimenet

## 🛡️ Biztonság

A program több szinten is védi a bizalmas adatokat:

1. **Fájlnév alapú szűrés**: Kizárja a bizalmas neveket tartalmazó fájlokat
2. **Tartalom alapú szűrés**: Reguláris kifejezésekkel keres bizalmas tartalmakat
3. **.gitignore támogatás**: Tiszteletben tartja a .gitignore szabályokat
4. **Méret korlátozás**: Kizárja a túlságosan nagy fájlokat

## 📊 Kimeneti Formátumok

### Markdown

A Markdown kimenet a következő struktúrát követi:

```markdown
# Projekt Összefoglaló: [Projekt Név]

## Statisztikák
- Összes fájl: X
- Feldolgozott fájlok: Y
- ...

## 1. Fájlstruktúra
```
project_root/
├── src/
│   ├── main.py
│   └── utils/
└── README.md
```

## 2. Fájltartalmak

### [src/main.py] - python
```python
def main():
    print("Hello, World!")
```
```

### JSON

A JSON kimenet strukturált adatokat tartalmaz:

```json
{
  "project": {
    "name": "My Project",
    "root_path": "/path/to/project",
    "generated_at": "2025-11-30T10:20:00",
    "generator": "GitIngest"
  },
  "stats": {
    "total_files": 42,
    "processed_files": 38
  },
  "file_tree": "...",
  "files": {
    "src/main.py": {
      "path": "src/main.py",
      "size": 123,
      "content": "def main():\n    print(\"Hello, World!\")",
      "language": "python"
    }
  }
}
```

## 🔧 Fejlesztés

A projekt a következő struktúrát követi:

```
gitingest/
├── main.py                 # Főprogram
├── config/
│   ├── __init__.py
│   ├── config_manager.py   # Konfiguráció kezelő
│   └── default_config.yaml # Alapértelmezett konfiguráció
├── core/
│   ├── __init__.py
│   ├── file_mapper.py      # Fájltérképező
│   ├── file_filter.py      # Szűrési logika
│   ├── content_extractor.py# Tartalom kinyerő
│   ├── database_analyzer.py# Adatbázis elemző
│   └── output_generator.py # Kimeneti generátor
├── utils/
│   ├── __init__.py
│   └── helpers.py          # Segédfüggvények
├── examples/
│   └── sample_config.yaml  # Példa konfiguráció
├── requirements.txt         # Függőségek
└── README.md               # Dokumentáció
```

## 📝 Példák

### Python projekt elemzése

```bash
python main.py ~/projects/my_python_app --verbose
```

### Webalkalmazás elemzése JSON formátumban

```bash
python main.py ~/projects/web_app --format json --output web_app_summary.json
```

### Egyéni konfigurációval

```bash
python main.py ~/projects/enterprise_app --config custom_config.yaml --verbose
```

### Adatbázis elemzése SQLite fájlokra

```bash
python main.py ~/projects/database_app --config examples/sample_config.yaml --verbose
```

### Adatbázis séma kinyerése SQLite esetén

```bash
# Módosítsd a konfigurációt: database_analysis.extract_schema: true
python main.py ~/projects/database_app --config custom_config.yaml --verbose
```

## 🤝 Hozzájárulás

A hozzájárulások szívesen látottak! Kérlek, kövesd a következő lépéseket:

1. Forkold a repository-t
2. Hozz létre egy feature branchet (`git checkout -b feature/amazing-feature`)
3. Commitold a változtatásaidat (`git commit -m 'Add some amazing feature'`)
4. Pushold a branchet (`git push origin feature/amazing-feature`)
5. Nyiss egy Pull Requestet

## 📄 Licensz

Ez a projekt MIT licensz alatt érhető el. Lásd a [LICENSE](LICENSE) fájlt a részletekért.

## 🙏 Köszönet

Köszönet minden hozzájárulónak, akik segítettek a projekt fejlesztésében!

## 🔗 Linkek

- [Repository](https://github.com/csokosgeza/GitIngest)
- [Issues](https://github.com/csokosgeza/GitIngest/issues)
- [Pull Requests](https://github.com/csokosgeza/GitIngest/pulls)