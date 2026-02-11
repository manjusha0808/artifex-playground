# XPath Crawler - Technical Specifications

## Project Overview

**Purpose**: Automated T24 banking system menu hierarchy extraction and XPath generation via Selenium web automation

**Target System**: T24 (Temenos banking software) - menu-driven banking operations interface

**Core Capability**: Crawls nested menu structures, extracts clickable elements, traverses hierarchy levels, and generates position-based XPath for each element

**Output**: Structured menu hierarchy in Excel (.xlsx), JSON, and text formats with complete breadcrumb paths and actual browser XPath values

---

## Technology Stack

### Dependencies
- **Python**: 3.8+ (verified on 3.10, 3.11, 3.14)
- **Selenium WebDriver**: 4.x - Browser automation and DOM traversal
- **openpyxl**: 3.x - Excel file creation and manipulation
- **python-dotenv**: Load environment variables for credentials
- **Built-in**: json, csv, logging modules

### Browser Support
- **Chrome/Chromium**: Primary driver engine with ChromeDriver
- **Firefox/Geckodriver**: Compatible, secondary option
- **Edge**: Compatible via EdgeDriver

### Database/Storage
- **Excel (.xlsx)**: Primary output format
- **JSON**: Hierarchical structure backup
- **Text (.txt)**: Human-readable breadcrumb format
- **Checkpoint JSON**: Resume recovery state

---

## Architecture

### Component Overview

```
extract_menu_hierarchy.py (Main Entry Point)
    ├── Browser Initialization
    │   ├── Selenium WebDriver setup
    │   ├── URL navigation & login
    │   └── Session management
    │
    ├── DOM Traversal
    │   ├── traverse_menu_tree() - Recursive menu walker
    │   ├── extract_node_info() - Element extraction with nested search
    │   └── get_element_xpath() - JavaScript XPath generation
    │
    ├── Data Processing
    │   ├── build_full_paths() - Breadcrumb construction
    │   ├── flatten_hierarchy() - Tree to tabular conversion
    │   └── validate_output() - Data integrity checks
    │
    └── Export Layer
        ├── export_to_excel() - openpyxl output
        ├── export_to_json() - Hierarchical JSON
        └── export_to_text() - Breadcrumb listing
```

### Key Functions

**`get_element_xpath(driver, element)`**
- Executes JavaScript in browser to extract position-based XPath
- Returns format: `//*[@id="pane_"]/ul[1]/li/ul/li[1]/ul/li[6]/ul/li[6]/a`
- Handles dynamic ID attributes and selector fallbacks
- Critical for actual browser XPath validation

**`extract_node_info(li_element, driver, level, parent_path)`**
- Searches nested elements using `.//*[self::a]` (ALL descendants, not just direct children)
- Multi-fallback text extraction:
  1. Direct `a` element text
  2. Parent `span` text
  3. Data attributes / title attributes
  4. Placeholder values
- Validates `href` contains action indicator (e.g., 'docommand')
- Returns: {text, xpath, type, unique_id, href}

**`traverse_menu_tree(element, driver, results, level, parent_path)`**
- Recursive depth-first traversal of menu structure
- Expands parent nodes, extracts children, recurses
- Maintains breadcrumb path for context
- Implements checkpoint saving every N iterations

**`build_full_paths(nodes, parent_map)`**
- Constructs full hierarchy paths: "Parent > Child > Grandchild"
- Determines node type: "Leaf" (no children) vs "Parent (Expandable)"
- Validates parent-child relationships

**`flatten_hierarchy(tree_data)`**
- Converts nested tree to tabular format (rows/columns)
- Creates columns: Node ID, Full Path, Level, Text, Type, Unique ID, XPath, Parent Node

---

## Data Flow Pipeline

```
1. INITIALIZATION PHASE
   └─ Load .env config → Initialize WebDriver → Navigate to T24 URL → Login

2. EXTRACTION PHASE
   ├─ Find root menu element (ul#pane_ or equivalent)
   ├─ traverse_menu_tree() starts at root
   │  └─ For each <li>:
   │     ├─ Find nested <a> tags using .//*[self::a]
   │     ├─ Extract text with fallback strategies
   │     ├─ Crawl XPath via get_element_xpath()
   │     ├─ Click element to expand children if parent
   │     └─ Recurse into children
   ├─ Save checkpoint every N nodes for resume
   └─ Collect into results array

3. PROCESSING PHASE
   ├─ Flatten hierarchy tree to tabular format
   ├─ Build full breadcrumb paths
   ├─ Validate no duplicate entries
   ├─ Remove N/A or incomplete entries
   └─ Add metadata (timestamps, counts, stats)

4. EXPORT PHASE
   ├─ export_to_excel() → menu_hierarchy3.xlsx
   ├─ export_to_json() → menu_hierarchy3.json
   ├─ export_to_text() → menu_hierarchy3.txt
   └─ Verify file integrity before completion
```

---

## Data Schema

### Excel Output (menu_hierarchy3.xlsx)

| Column | Type | Example | Description |
|--------|------|---------|-------------|
| Node ID | String | NODE:1_2_3 | Internal hierarchy identifier |
| Full Path | String | Main Menu > Operations > Create | Complete breadcrumb path |
| Level | Int | 3 | Depth in hierarchy (1 = root) |
| Node Text | String | Create Order | Display text of menu item |
| Type | String | Leaf / Parent | Leaf node or expandable parent |
| Unique ID | String | btn_create_order_123 | Element HTML ID if available |
| XPath | String | `//*[@id="pane_"]/ul[1]/li/ul/li[1]/a` | Position-based XPath from browser |
| Parent Node | String | NODE:1_2 | Reference to parent NODE ID |

### JSON Output Structure

```json
{
  "metadata": {
    "timestamp": "2026-02-11T15:30:00",
    "total_nodes": 6112,
    "leaf_nodes": 3202,
    "parent_nodes": 2910,
    "extraction_duration_hours": 5.5
  },
  "hierarchy": [
    {
      "node_id": "NODE:1",
      "text": "Main Menu",
      "xpath": "//*[@id='pane_']/ul[1]/li[1]/a",
      "type": "Parent",
      "level": 1,
      "children": [
        {
          "node_id": "NODE:1_1",
          "text": "Operations",
          "xpath": "//*[@id='pane_']/ul[1]/li[1]/ul/li[1]/a",
          "type": "Parent",
          "level": 2,
          "children": [...]
        }
      ]
    }
  ]
}
```

---

## Key Modifications & Fixes

### Fix #1: Nested Element Detection
**Problem**: Original extraction used `li_element.find_elements(By.XPATH, "./*")` which only found direct children, missing deeply nested `<a>` tags buried 3+ levels in DOM.

**Solution**: Changed to `.//*[self::a]` to search ALL descendants recursively.

```python
# BEFORE (Broken)
a_elements = li_element.find_elements(By.XPATH, "./*")  # Direct children only

# AFTER (Fixed)
a_elements = li_element.find_elements(By.XPATH, ".//*[self::a]")  # All nested <a> tags
```

**Impact**: Resolved 1,556 nodes (25.46%) previously showing "N/A" XPath → Now captures actual XPath values.

### Fix #2: Multi-Fallback Text Extraction
**Problem**: Some menu items had missing or hidden text content.

**Solution**: Implemented 4-level fallback strategy:
1. Direct `a` element `.text` property
2. Parent `span` text traversal
3. Data/title attribute mining
4. Placeholder generation

```python
text = a_elem.text.strip() or ""
if not text:
    try:
        parent_span = a_elem.find_element(By.XPATH, "ancestor::span[1]")
        text = parent_span.text.strip()
    except: 
        try:
            text = a_elem.get_attribute('title').strip() or ""
        except:
            text = a_elem.get_attribute('data-text') or f"Menu Item {item_count}"
```

### Fix #3: Actual XPath Crawling
**Problem**: Constructed XPath strings didn't always match actual browser paths.

**Solution**: Use JavaScript in browser context to extract position-based XPath directly from DOM.

```javascript
function getElementXPath(element) {
    if (element.id !== '')
      return "//*[@id=\"" + element.id + "\"]";
    if (element === document.body)
      return element.tagName.toLowerCase();
    
    var ix = 0;
    var siblings = element.parentNode.childNodes;
    for (var i = 0; i < siblings.length; i++) {
        var sibling = siblings[i];
        if (sibling === element)
          return getElementXPath(element.parentNode) + '/' + element.tagName.toLowerCase() + '[' + (ix + 1) + ']';
        if (sibling.nodeType === 1 && sibling.tagName.toLowerCase() === element.tagName.toLowerCase())
          ix++;
    }
}
```

---

## Configuration & Environment

### .env Variables Required
```
T24_USERNAME=<banking_user_id>
T24_PASSWORD=<secure_password>
T24_BASE_URL=http://<t24_server_ip>:<port>
CHROME_DRIVER_PATH=./chromedriver
HEADLESS_MODE=true
WAIT_TIMEOUT=30
EXTRACTION_BATCH_SIZE=50
CHECKPOINT_INTERVAL=100
LOG_LEVEL=INFO
```

### Configuration File (config.yaml)
```yaml
browser:
  type: chrome
  headless: true
  window_size: [1920, 1080]
  
navigation:
  base_url: "http://t24-server/ibis"
  login_url: "/login"
  menu_root_selector: "ul#pane_"
  
selectors:
  menu_item: "li"
  clickable: "a[href*='docommand']"
  parent_indicator: ".expandable"
  
extraction:
  wait_timeout: 30
  batch_size: 50
  checkpoint_interval: 100
  max_retries: 3
  
export:
  formats: ["excel", "json", "text"]
  output_dir: "./"
  filename_prefix: "menu_hierarchy"
```

---

## Known Limitations

1. **JavaScript-Heavy Pages**: Some T24 dynamics may require additional JavaScript execution waits
2. **User Permissions**: Extracted menu reflects logged-in user's role - may vary by user role
3. **Popup Dialogs**: Unexpected popups can block extraction - implement popup detection/closure
4. **Performance**: Full extraction takes 3-8 hours depending on menu depth and network latency
5. **Session Timeouts**: Long extractions may hit T24 session timeouts - implement re-login logic
6. **Browser Memory**: Headless Chrome may consume significant memory on complex DOMs
7. **Dynamic Content**: Menu items loaded via AJAX may be missed if timing is too fast

---

## Performance Metrics

| Metric | Value | Notes |
|--------|-------|-------|
| Nodes Extracted | ~6,100 | Per full T24 menu |
| Extraction Time | 3-8 hours | Varies by depth and server |
| Memory Usage | 500-800 MB | Headless Chrome + DOM in memory |
| XPath Generation | ~100-200 ms per element | Via JavaScript execution |
| Excel File Size | 3-5 MB | 6,100 rows × 8 columns |
| Checkpoint Interval | 100 nodes | Trades disk I/O for resume

---

## Error Recovery & Checkpointing

### Checkpoint Structure
```json
{
  "last_extracted_node": "NODE:1_2_3_4",
  "progress": {
    "nodes_extracted": 523,
    "extraction_start_time": "2026-02-11T10:00:00",
    "current_path": "Main Menu > Operations > Create",
    "browser_state": "ready"
  },
  "nodes": [...]
}
```

### Resume Process
```python
# Load last checkpoint if exists
if Path("crawler_checkpoint.json").exists():
    with open("crawler_checkpoint.json") as f:
        checkpoint = json.load(f)
    results = checkpoint["nodes"]
    last_node = checkpoint["last_extracted_node"]
    print(f"Resuming from {last_node_id}...")
else:
    results = []
    last_node_id = None

# Continue extraction from checkpoint...
```

---

## Testing & Validation

### Unit Tests
- `test_xpath_generation.py`: Validates JavaScript XPath extraction
- `validate_output.py`: Checks for duplicates, missing XPath, hierarchy consistency
- `test_checkpoint.py`: Verifies checkpoint save/load functionality

### Integration Tests
- Full extraction run on test T24 instance
- Compare against known menu structure
- Validate all leaf nodes have XPath values
- Check zero N/A entries in XPath column

### Data Quality Checks
- No duplicate entries
- XPath count matches element count
- All nodes have breadcrumb path
- Parent-child relationships valid
- Level numbers sequential and accurate

