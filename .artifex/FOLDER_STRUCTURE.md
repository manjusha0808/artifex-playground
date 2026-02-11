# XPath Crawler - Repository Folder Structure

## Repository Layout

```
xpath-crawler/
│
├── .artifex/                          # Documentation & specifications (this folder)
│   ├── GUIDELINES.md                  # DO's and DON'Ts for development
│   ├── SPECS.md                       # Technical specifications & architecture
│   └── FOLDER_STRUCTURE.md            # This file - folder organization guide
│
├── selenium_trial/                    # Main project folder (pushes to GitHub)
│   ├── extract_menu_hierarchy.py      # ⭐ MAIN CRAWLER - T24 menu extraction script
│   ├── requirements.txt               # Python dependencies for selenium_trial
│   ├── .env                           # Environment variables (credentials, config)
│   │
│   ├── Output Files (Generated after extraction)
│   ├── menu_hierarchy3.xlsx           # Primary output: Excel with 6,112 nodes
│   ├── menu_hierarchy3.json           # Hierarchical JSON format
│   ├── menu_hierarchy3.txt            # Breadcrumb text format
│   ├── na_nodes_dom_paths.xlsx        # Analysis: DevTools paths for N/A nodes
│   │
│   ├── archive_trials/                # Historical scripts & experiments
│   │   ├── README.md                  # Archive index
│   │   ├── CHECKPOINT_USAGE.md        # Checkpoint recovery documentation
│   │   │
│   │   ├── Early Crawlers (iterations 1-4)
│   │   ├── crawler.py                 # Original basic crawler
│   │   ├── crawler_fast.py            # Speed optimizations attempt
│   │   ├── crawler_iframe_aware.py    # iFrame handling iteration
│   │   ├── crawler_with_stats.py      # Stats collection prototype
│   │   │
│   │   ├── Analysis Tools
│   │   ├── analyze_crawler_output.py  # Output validation script
│   │   ├── analyze_zero_patterns.py   # Investigate zero-element pages
│   │   ├── analyze_na_patterns.py     # Analyze N/A XPath distribution
│   │   ├── analyze_na_deep.py         # Deep analysis of N/A nodes
│   │   ├── analyze_xpath_gap.py       # Compare extracted vs actual XPath
│   │   │
│   │   ├── Data Cleaning Tools
│   │   ├── check_dupes.py             # Detect duplicate entries
│   │   ├── clean_duplicates.py        # Remove duplicates from output
│   │   ├── check_invalid_xpaths.py    # Validate XPath format
│   │   │
│   │   ├── Debugging & Rescreening
│   │   ├── check_iframe_fields.py     # Debug iframe extraction issues
│   │   ├── debug_iframe_fields.py     # iFrame debugging utilities
│   │   ├── debug_rescreen.py          # Rescreen specific items
│   │   ├── debug_zero_elements.py     # Investigate zero-element issues
│   │   ├── rescreen_crawler.py        # Targeted rescreening script
│   │   ├── rescreen_zero_elements.py  # Fix zero-element pages
│   │   ├── rescreen_zero_xpath_pages.py # Fix zero-XPath pages
│   │   ├── spot_check_zero.py         # Spot check zero-element nodes
│   │   │
│   │   ├── Testing & Validation
│   │   ├── compare_crawlers_test.py   # Compare different crawler versions
│   │   ├── compare_old_new.py         # Before/after comparison
│   │   ├── read_excel.py              # Excel parsing utility
│   │   ├── test_checkpoint.py         # Checkpoint recovery testing
│   │   ├── validate_advanced.py       # Advanced validation suite
│   │   ├── validate_cleaned.py        # Validate cleaned data
│   │   ├── validate_output.py         # Basic output validation
│   │   ├── verify_output.py           # Output verification script
│   │   │
│   │   ├── Output Files (Historical)
│   │   ├── menu_hierarchy[1-3].txt    # Historical breadcrumb outputs
│   │   ├── menu_hierarchy3.json       # Historical JSON backup
│   │   ├── uiMap_*.xlsx               # Various export iterations
│   │   ├── page_stats_*.xlsx          # Page-level statistics
│   │   ├── element_count_summary.csv  # Per-page element counts
│   │   ├── zero_elements_*.csv        # Pages with zero clickable elements
│   │   ├── zero_xpath_pages.xlsx      # Pages with zero XPath matches
│   │   ├── items_to_rescreen.json     # Items flagged for rescreening
│   │   │
│   │   ├── Debug Artifacts
│   │   ├── crawler_checkpoint.json    # Full backup checkpoint
│   │   ├── crawler_fast_checkpoint.json
│   │   ├── page_screenshot_*.png      # Screenshots of problem pages
│   │   ├── debug_*.png                # Debug visual captures
│   │   └── __pycache__/               # Python bytecode cache
│   │
│   ├── __pycache__/                   # Python compiled modules
│   └── ~ (temp/lock files)            # Excel temp files (can be deleted)
│
├── .git/                              # Git repository metadata
├── .venv/                             # Python virtual environment
├── .env                               # Root-level environment file
├── uiMap_out.xlsx                     # Root-level output sample
└── uiMap_out_report.html              # Root-level report sample
```

---

## Folder Descriptions

### 📁 `.artifex/` - Documentation & Specifications
**Purpose**: Non-code documentation defining project standards, guidelines, and specifications

**Contents**:
- `GUIDELINES.md` - Development best practices and anti-patterns
- `SPECS.md` - Technical architecture and data schemas
- `FOLDER_STRUCTURE.md` - This file

**When to Use**: Reference this before coding, during code review, or when onboarding new developers

---

### 📁 `selenium_trial/` - Main Project Folder
**Purpose**: Production-ready extraction code and outputs. This folder is pushed to GitHub.

**Key Files**:

#### `extract_menu_hierarchy.py` ⭐ MAIN ENTRY POINT
- Largest and most important file (~30KB)
- Complete T24 menu extraction pipeline
- Last modified: 2026-02-10 15:44
- Key functions:
  - `get_element_xpath(driver, element)` - JavaScript XPath extraction
  - `extract_node_info(li_element, ...)` - Element text/link extraction with nested search
  - `traverse_menu_tree(...)` - Recursive menu traversal
  - `build_full_paths(...)` - Breadcrumb construction
  - `export_to_excel/json/text()` - Multi-format export

**Recent Modification**: Changed element search from `./*` (direct children) to `.//*[self::a]` (all nested descendants) to capture deeply nested menu items. This fix resolved 1,556 N/A XPath entries.

#### `requirements.txt`
```
selenium>=4.10.0
openpyxl>=3.10.0
python-dotenv>=1.0.0
```

#### `.env` (credentials)
```
T24_USERNAME=<user>
T24_PASSWORD=<password>
T24_BASE_URL=http://<server>:<port>
HEADLESS_MODE=true
WAIT_TIMEOUT=30
```

#### Output Files (Auto-Generated)

| File | Format | Rows | Purpose |
|------|--------|------|---------|
| `menu_hierarchy3.xlsx` | Excel | 6,112 | Primary structured output with all columns |
| `menu_hierarchy3.json` | JSON | Nested | Hierarchical format for programmatic access |
| `menu_hierarchy3.txt` | Text | 6,112 | Breadcrumb format for human reading |
| `na_nodes_dom_paths.xlsx` | Excel | 1,556 | Analysis of nodes with N/A XPath (obsolete with fix) |

---

### 📁 `archive_trials/` - Historical Scripts & Experiments
**Purpose**: Preserve prior development iterations and analysis tools for reference. These are NOT production code.

**Subfolder Organization**:

#### Early Crawlers
- `crawler.py` - Original iteration (slow, basic)
- `crawler_fast.py` - Optimization attempt
- `crawler_iframe_aware.py` - iFrame handling
- `crawler_with_stats.py` - Statistics collection prototype

**Why Archived**: Superseded by functionality integrated into `extract_menu_hierarchy.py`

#### Analysis Tools
- `analyze_* .py` - Scripts to investigate output patterns (NA nodes, zero elements, xpath gaps)

**Why Archived**: Used for one-time investigations; can be deleted if disk space needed

#### Data Cleaning Tools
- `check_*.py`, `clean_*.py` - Validation and data cleanup utilities

**When to Use**: If output contains duplicates or invalid entries, use these scripts to diagnose

#### Debugging & Rescreening
- `debug_*.py`, `rescreen_*.py` - Utilities to fix specific problem pages/nodes

**When to Use**: If extraction misses certain menu items or has N/A entries, use targeting rescreening tools

#### Testing & Validation
- `validate_*.py`, `test_*.py`, `compare_*.py` - Comparative testing between crawler versions

**When to Use**: After major code changes, run validation suite to ensure data quality

#### Historical Output Files
- `menu_hierarchy[1-3].*`, `uiMap_*.xlsx`, `page_stats_*.xlsx` - Outputs from prior runs

**Why Keep**: Track extraction history and compare before/after improvements

---

## File Naming Conventions

### Source Code
- `extract_menu_hierarchy.py` - Production extractor (MAIN)
- `crawler.py` / `crawler_*.py` - Crawler variants (archived)
- `analyze_*.py` - Analysis utilities (archived)
- `validate_*.py` - Validation tools (can be in root or archive)
- `debug_*.py` - Debugging utilities (archived)
- `rescreen_*.py` - Targeted rescreening (archived)

### Output Files (Generated)
- `menu_hierarchy3.xlsx` - Excel primary output (v3, latest)
- `menu_hierarchy3.json` - JSON backup (v3)
- `menu_hierarchy3.txt` - Text breadcrumb (v3)
- `na_nodes_dom_paths.xlsx` - Special analysis file
- `page_stats_*.xlsx` - Per-page statistics
- `zero_elements_*.csv` - Problem nodes list
- `*_checkpoint.json` - Resume points

### Configuration & Data
- `.env` - Environment variables (NEVER commit with real credentials)
- `requirements.txt` - Python dependencies
- `config.yaml` - Application configuration
- `*.png` - Debug screenshots
- `~$*.xlsx` - Excel lock files (temporary, ignore)

---

## GitHub Push Strategy

**What Gets Pushed**: Only `selenium_trial/` folder

**What Gets Excluded**:
- `.venv/` - Local Python environment
- `__pycache__/` - Compiled Python bytecode
- `.env` - Real credentials (use `.env.example` instead)
- `.git/` - Git metadata (auto-handled)
- Root-level output files (generated, not source)

**Git Configuration** (.gitignore):
```
.venv/
__pycache__/
.env
.env.local
*.pyc
~$*.xlsx
uiMap_out.xlsx
uiMap_out_report.html
```

**Commands to Push**:
```bash
cd xpath-crawler
git add selenium_trial/
git commit -m "Update XPath extraction with nested element fix"
git push origin main
```

---

## Folder Size Reference

| Folder | Size | Reason |
|--------|------|--------|
| `archive_trials/` | ~50 MB | Many Excel output files, screenshots, checkpoints |
| `selenium_trial/` (excl. archive) | ~10 MB | Main scripts, current outputs |
| `.venv/` | ~200 MB | Full Python environment |
| Total | ~260 MB | Can be reduced by deleting archive_trials |

---

## Development Workflow

### Initial Setup
```bash
cd xpath-crawler
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r selenium_trial/requirements.txt
cp selenium_trial/.env.example selenium_trial/.env
# Edit .env with real credentials
```

### Running Extraction
```bash
cd selenium_trial
python extract_menu_hierarchy.py
# Waits 3-8 hours... generates menu_hierarchy3.xlsx
```

### Data Validation
```bash
cd selenium_trial/archive_trials
python validate_output.py  # Check for duplicates, missing XPath
python analyze_na_patterns.py  # Investigate remaining N/A nodes
```

### Committing Changes
```bash
cd ..
git add selenium_trial/
git commit -m "Descriptive message of changes"
git push origin main
```

---

## Maintenance Instructions

### Cleaning Up After Extraction
1. **Delete temp files**: Remove `~$*.xlsx` lock files
2. **Backup checkpoint**: Save `*_checkpoint.json` in case of future failures
3. **Remove .pyc files**: `rm -r selenium_trial/__pycache__/`
4. **Archive old outputs**: Move `menu_hierarchy[1-2].*` to archive_trials/

### Archiving Trial Scripts
1. When a script is no longer needed, move it to `archive_trials/`
2. Update `archive_trials/README.md` with description
3. Keep only for reference/history—don't clutter main folder

### Reducing Repo Size
- Archive very old output files: `.xlsx` files consume most space
- Remove unused `.png` screenshots after archiving
- Keep only recent 2-3 extraction outputs as references
- Current practical size: 10-15 MB for active code + recent outputs

---

## Troubleshooting by Folder

### Problem: `extract_menu_hierarchy.py` crashes midway
→ Check `selenium_trial/*_checkpoint.json` exists
→ Restart script—it will resume from checkpoint
→ If checkpoint missing, script starts from beginning

### Problem: Output file shows N/A in XPath column
→ This was **FIXED** by nested element detection
→ Old archive files in `archive_trials/` may still show N/A
→ Re-run `extract_menu_hierarchy.py` to get fresh output with XPath values

### Problem: Duplicate entries in output
→ Run `archive_trials/clean_duplicates.py` on output file
→ Or run `archive_trials/compare_crawlers_test.py` for analysis

### Problem: Zero clickable elements on certain pages
→ Check `archive_trials/zero_elements_WITH_inputs.csv` for problem pages
→ Use `archive_trials/rescreen_zero_elements.py` to investigate

### Problem: Can't find a menu item in output
→ Try `archive_trials/spot_check_zero.py` to find missing items
→ May need to adjust selectors if DOM structure changed

