# .artifex Documentation Index

This folder contains comprehensive specifications, guidelines, and documentation for the xpath-crawler project.

## Quick Navigation

### 📋 [GUIDELINES.md](GUIDELINES.md)
**Development Best Practices & Anti-Patterns**

What to do and what NOT to do when working with this codebase.

**Sections**:
- ✅ DO's - Web scraping, element selection, data management, git workflow
- ❌ DON'Ts - Common pitfalls to avoid
- 🔍 Implementation checklist before running extraction
- 🐛 Common issues and solutions table

**Read this**: Before writing code or modifying extract_menu_hierarchy.py

---

### 🏗️ [SPECS.md](SPECS.md)
**Technical Specifications & Architecture**

Complete technical documentation of the system architecture, data flow, and implementation details.

**Sections**:
- Project overview and goals
- Technology stack (Python, Selenium, openpyxl)
- Architecture components and key functions
- Data flow pipeline (4 phases)
- Data schemas (Excel, JSON formats)
- Key modifications & fixes applied
- Configuration & environment variables
- Known limitations
- Performance metrics
- Error recovery & checkpointing
- Testing & validation approaches

**Read this**: When you need to understand how the system works or modify core functionality

---

### 📁 [FOLDER_STRUCTURE.md](FOLDER_STRUCTURE.md)
**Repository Organization & File Inventory**

Complete directory tree with descriptions of every folder and file, plus usage guidelines.

**Sections**:
- Full repository directory structure with visual tree
- Detailed descriptions of each folder (purpose, when to use)
- Key file descriptions and purposes
- File naming conventions used in project
- GitHub push strategy (what gets committed)
- Folder size references
- Development workflow (setup, running, committing)
- Maintenance instructions
- Troubleshooting guide by folder

**Read this**: To find where files are located or understand folder organization

---

## Getting Started

### First Time? Start Here
1. Read [FOLDER_STRUCTURE.md](FOLDER_STRUCTURE.md) - Understand the layout
2. Read [SPECS.md](SPECS.md) - Learn how the system works
3. Read [GUIDELINES.md](GUIDELINES.md) - Learn the do's and don'ts

### Need to Debug Something?
1. Check [GUIDELINES.md](GUIDELINES.md) → "Common Issues & Solutions" table
2. Review [FOLDER_STRUCTURE.md](FOLDER_STRUCTURE.md) → "Troubleshooting by Folder"
3. Look for relevant script in `selenium_trial/archive_trials/`

### Running Extraction for First Time
```bash
cd selenium_trial
python extract_menu_hierarchy.py
```
**Duration**: 3-8 hours  
**Output**: menu_hierarchy3.xlsx (6,112 nodes with XPath values)

### Modifying Code?
1. Review [GUIDELINES.md](GUIDELINES.md) - Prevention checklist
2. Review [SPECS.md](SPECS.md) - Architecture to understand impact
3. Refer to affected sections in both documents
4. Run validation scripts in `archive_trials/` after changes

---

## Key Takeaways

### Most Important Guidelines
🚨 **Critical DO's**:
- Search for nested elements using `.//*[self::a]` not `./*`
- Use explicit waits (WebDriverWait) not sleep()
- Always wrap element interactions in try-except
- Save checkpoints every N iterations for resume
- Generate XPath from browser JavaScript, not string construction

🚨 **Critical DON'Ts**:
- DON'T search only direct children - you'll miss nested elements (causes N/A!)
- DON'T skip error logging - browser crashes happen
- DON'T force push without understanding what you overwrite
- DON'T store real credentials in committed .env files
- DON'T assume elements exist - use try-except

### Project Scope
- **What**: Automated T24 banking menu extraction with XPath generation
- **Why**: Enable UI automation and element identification in banking system
- **How**: Selenium WebDriver DOM traversal + JavaScript XPath generation
- **Output**: Excel (6,112 nodes), JSON, text formats with complete hierarchy

### Current Status
✅ **Working**: Full menu extraction with nested element detection  
✅ **Fixed**: N/A XPath issue (was caused by shallow search, now uses deep nested search)  
✅ **Archived**: 53 trial/analysis scripts in archive_trials/ folder  
📊 **Output**: menu_hierarchy3.xlsx with 6,112 menu nodes

---

## File Quick Reference

| Document | Purpose | Read When |
|----------|---------|-----------|
| GUIDELINES.md | DO's/DON'Ts, implementation checklist, issues table | Before coding or debugging |
| SPECS.md | Architecture, data schemas, technical details | Understanding component details |
| FOLDER_STRUCTURE.md | Directory tree, file inventory, organization | Finding files or understanding layout |

---

## Accessing Documentation

All files are in Markdown format and can be:
- 📖 Opened in any text editor
- 🌐 Viewed on GitHub
- ⚡ Searched with Ctrl+F (or Cmd+F on Mac)
- 📱 Read on phone/tablet with any Markdown viewer

## Contact / Issues

For questions or issues, refer to:
1. [GUIDELINES.md](GUIDELINES.md) - "Common Issues & Solutions"
2. [FOLDER_STRUCTURE.md](FOLDER_STRUCTURE.md) - "Troubleshooting by Folder"
3. Check `selenium_trial/archive_trials/` for example analysis/debug scripts

---

**Last Updated**: February 11, 2026  
**Version**: 1.0  
**Scope**: XPath Crawler for T24 menu extraction via Selenium
