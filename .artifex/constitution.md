# XPath Crawler - Development Guidelines

## DO's ✅

### Web Scraping & Selenium
- **DO** use headless mode for faster execution when visual inspection isn't needed
- **DO** implement explicit waits (WebDriverWait) instead of sleep() for element visibility
- **DO** handle iframes explicitly by switching context when accessing nested content
- **DO** use try-except blocks for all element interactions to gracefully handle missing elements
- **DO** implement checkpoint recovery to resume interrupted crawls without losing progress
- **DO** search for nested elements using `.//*[self::a]` instead of direct children `./*` to catch deeply nested clickable elements
- **DO** validate XPath existence in the browser DOM before storing in output
- **DO** use JavaScript execution to extract position-based XPath from the actual browser DOM

### Element Selection
- **DO** prioritize finding elements by `class`, `id`, or semantic HTML attributes
- **DO** fall back to multiple text extraction strategies (direct text, parent span, data attributes, etc.)
- **DO** verify element clickability before treating it as a valid menu item
- **DO** check for `href` attribute containing action indicators (e.g., 'docommand') to identify valid links
- **DO** preserve parent-child relationships when extracting hierarchy data

### Data Management
- **DO** use openpyxl for Excel export to maintain compatibility and avoid dependency issues
- **DO** export to multiple formats (Excel, JSON, text) for flexibility
- **DO** include metadata (timestamp, page count, extraction stats) in output files
- **DO** validate data integrity before committing to files
- **DO** maintain consistent column order in Excel export (Node ID, Full Path, Level, Text, Type, XPath, Parent)

### Environment & Configuration
- **DO** use .env file with sensitive credentials (login details, environment variables)
- **DO** load configuration via python-dotenv before starting browser automation
- **DO** log extraction progress with checkpoint files for resume capability
- **DO** implement error logging with clear messages for debugging
- **DO** validate browser driver availability before starting extraction

### Git & Repository
- **DO** commit only essential files (scripts, config samples, requirements.txt, output files)
- **DO** use .gitignore to exclude: venv, __pycache__, .env (actual credentials)
- **DO** push only the selenium_trial folder and its contents to repository
- **DO** document breaking changes in commit messages

---

## DON'Ts ❌

### Web Scraping Pitfalls
- **DON'T** use sleep(random_time) for waits - use WebDriverWait with proper conditions
- **DON'T** assume all menu items have visible XPath - some may be nested or dynamically generated
- **DON'T** click elements without checking if they're clickable/enabled
- **DON'T** search only direct children (`./*`) for menu elements - use `.//*` to find nested items
- **DON'T** ignore iframes - menu content may be iframe-nested and require explicit context switching
- **DON'T** extract XPath by string concatenation - crawl actual XPath from browser JavaScript

### Error Handling
- **DON'T** fail silently without logging - always log what went wrong and where
- **DON'T** assume elements exist without Try-except protection
- **DON'T** skip checkpoint saving - browser crashes happen and you'll lose hours of work
- **DON'T** continue extraction if login fails - validate authentication before proceeding
- **DON'T** ignore timeout errors - they indicate page load or stale element issues

### Data Quality
- **DON'T** store "N/A" or null values for XPath without investigation - search deeper in DOM
- **DON'T** export duplicate entries without deduplication
- **DON'T** use relative XPath that may break with DOM changes - use position-based absolute XPath
- **DON'T** mix text extraction methods inconsistently - establish fallback hierarchy and use it consistently
- **DON'T** forget to validate export file integrity before marking extraction complete

### Repository & File Management
- **DON'T** commit .env with real credentials - use .env.example with dummy values
- **DON'T** commit venv/ or __pycache__/ to Git
- **DON'T** delete local folders without confirming recovery method first
- **DON'T** force push without understanding what you're overwriting on GitHub
- **DON'T** commit every test/trial script - archive old experiments in archive_trials/

### Performance
- **DON'T** open new browser window for each page - reuse single driver instance
- **DON'T** re-login between every action - authenticate once and maintain session
- **DON'T** export to Excel on every page - batch export at end
- **DON'T** increase waits unnecessarily - use adaptive waits instead
- **DON'T** ignore memory leaks - close browser driver properly in finally blocks

---

## Implementation Checklist

Before running extract_menu_hierarchy.py:

- [ ] Python environment configured with venv
- [ ] requirements.txt dependencies installed
- [ ] .env file populated with valid T24 credentials
- [ ] Browser driver version matches installed browser
- [ ] Config file has correct base URL and menu selectors
- [ ] Previous checkpoint files cleaned or recovery plan ready
- [ ] Output folder has write permissions
- [ ] Email alerts (if enabled) configured correctly

Before committing code:

- [ ] All hardcoded credentials removed
- [ ] Checkpoint files tested for resume functionality
- [ ] Error logging includes actionable information
- [ ] XPath extraction verified with sample elements
- [ ] Nested element search (.*//*) validated for deep DOM structures
- [ ] Fallback text extraction tested with missing attributes
- [ ] Excel export file format validated

---

## Common Issues & Solutions

| Issue | Cause | Solution |
|-------|-------|----------|
| "N/A" XPath values | Nested `<a>` elements not found by `./*` search | Change to `.//*[self::a]` to search all descendants |
| Stale element reference | Element referenced after page reload | Re-query element after navigation |
| Timeout errors | Slow page loads or missing waits | Increase explicit wait duration or check network |
| Login failures | Session expired or wrong credentials | Validate .env config and re-authenticate |
| iFrame elements not found | Not switching to iFrame context | Use `driver.switch_to.frame()` before querying |
| Memory leak/crash | Driver not closed properly | Ensure `driver.quit()` in finally block |
| Duplicate entries | Same element crawled multiple times | Implement Set-based deduplication before export |
| Zero elements extracted | Selector mismatch or DOM structure changed | Update selectors and test in browser DevTools |

