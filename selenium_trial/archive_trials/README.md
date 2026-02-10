# Selenium T24 Crawler

This folder contains a Selenium-based crawler for T24 Model Bank that:

✅ Detects leaf nodes with `javascript:docommand(` pattern
✅ Clicks on them to open popups
✅ Extracts XPaths from the popup forms
✅ Exports to Excel with proper element naming (txt*, btn*, ddl*, etc.)

## Setup

1. Install dependencies:
```powershell
pip install -r requirements.txt
```

2. Make sure ChromeDriver is installed or Selenium Manager will auto-download it

3. Ensure your `.env` file in the root directory has:
```
APP_USERNAME=MB.OFFICER
APP_PASSWORD=123456
APP_URL=http://10.0.251.41:18080/BrowserWeb/servlet/BrowserServlet
```

## Run

```powershell
python crawler.py
```

## Output

- Creates `uiMap_selenium.xlsx` with columns:
  - page: Menu item name
  - elementName: Prefixed name (txtUserName, btnSubmit, ddlCountry, etc.)
  - relativeXpath: XPath expression
  - id: Element ID attribute
  - name: Element name attribute
  - className: Element class
  - tagName: HTML tag
  - type: Input type (for input elements)

## Features

- **Visual feedback**: Highlights menu items in green before clicking
- **Progress tracking**: Shows "[1/4336] Clicking: Input Prospect (Person)"
- **Robust**: Re-queries elements to avoid stale references
- **Smart naming**: Automatically prefixes elements (txt, btn, ddl, chk, rad, lnk)
- **Popup handling**: Opens popup, extracts XPaths, closes popup, continues
