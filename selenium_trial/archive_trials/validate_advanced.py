"""
Advanced validation for XPath Excel files - checks for noise and quality issues.
"""
import openpyxl
import sys
from collections import Counter, defaultdict

filename = sys.argv[1] if len(sys.argv) > 1 else 'uiMap_selenium_fullrun_auto4_cleaned.xlsx'

print(f"📁 Detailed Validation: {filename}")
print("=" * 70)

wb = openpyxl.load_workbook(filename)
ws = wb.active

# Collect all data
rows_data = []
for row_cells in ws.iter_rows(min_row=2, values_only=True):
    row = {
        'pageName': row_cells[0] or '',
        'elementName': row_cells[1] or '',
        'xpath': row_cells[2] or '',
        'elementId': row_cells[3] or '',
        'elementNameAttr': row_cells[4] or '',
        'className': row_cells[5] or '',
        'tagName': row_cells[6] or '',
        'inputType': row_cells[7] if len(row_cells) > 7 else ''
    }
    rows_data.append(row)

print(f"\n📊 Basic Statistics:")
print(f"   Total rows: {len(rows_data)}")
print(f"   Unique pages: {len(set(r['pageName'] for r in rows_data))}")

# Check for suspicious patterns
print(f"\n🔍 Quality Checks:")

# 1. Check for rows where elementName == xpath (potential bug)
name_equals_xpath = [r for r in rows_data if r['elementName'] and r['elementName'] == r['xpath']]
print(f"   ⚠️ ElementName = XPath: {len(name_equals_xpath)}")
if name_equals_xpath:
    print(f"      Example: {name_equals_xpath[0]['pageName']} -> {name_equals_xpath[0]['elementName']}")

# 2. Check for invalid XPaths (not starting with //)
invalid_xpaths = [r for r in rows_data if r['xpath'] and not str(r['xpath']).startswith('//')]
print(f"   ⚠️ Invalid XPath format: {len(invalid_xpaths)}")
if invalid_xpaths:
    print(f"      Examples:")
    for ex in invalid_xpaths[:3]:
        print(f"        - {ex['pageName']}: {ex['xpath']}")

# 3. Check for duplicate XPaths across different pages
xpath_pages = defaultdict(set)
for r in rows_data:
    if r['xpath']:
        xpath_pages[r['xpath']].add(r['pageName'])

duplicate_xpaths = {xpath: pages for xpath, pages in xpath_pages.items() if len(pages) > 1}
print(f"   📋 XPaths appearing on multiple pages: {len(duplicate_xpaths)}")
if duplicate_xpaths:
    example = list(duplicate_xpaths.items())[0]
    print(f"      Example: {example[0][:60]}... appears on {len(example[1])} pages")

# 4. Check for rows with minimal info (no ID, no name, no class)
minimal_info = [r for r in rows_data if not r['elementId'] and not r['elementNameAttr'] and not r['className']]
print(f"   ⚠️ Rows with minimal identifiers: {len(minimal_info)}")

# 5. Distribution by tag type
tag_distribution = Counter(r['tagName'] for r in rows_data if r['tagName'])
print(f"\n📊 Tag Distribution:")
for tag, count in tag_distribution.most_common(10):
    print(f"   {tag}: {count}")

# 6. Distribution by input type
input_distribution = Counter(r['inputType'] for r in rows_data if r['inputType'])
print(f"\n📊 Input Type Distribution:")
for itype, count in input_distribution.most_common(10):
    print(f"   {itype}: {count}")

# 7. Pages with most elements
page_counts = Counter(r['pageName'] for r in rows_data)
print(f"\n📊 Top 10 Pages by Element Count:")
for page, count in page_counts.most_common(10):
    print(f"   {count:4d} elements: {page}")

# 8. Pages with least elements
print(f"\n📊 Pages with Fewest Elements:")
for page, count in sorted(page_counts.items(), key=lambda x: x[1])[:10]:
    print(f"   {count:4d} elements: {page}")

# 9. Check for potential noise patterns
noise_patterns = []

# Empty elementName
empty_names = [r for r in rows_data if not r['elementName']]
if empty_names:
    noise_patterns.append(f"Empty elementName: {len(empty_names)}")

# XPath contains specific noise indicators
suspicious_xpaths = [r for r in rows_data if r['xpath'] and any(x in str(r['xpath']).lower() for x in ['hidden', 'display:none', 'disabled'])]
if suspicious_xpaths:
    noise_patterns.append(f"Potentially hidden/disabled elements: {len(suspicious_xpaths)}")

if noise_patterns:
    print(f"\n⚠️ Potential Noise Detected:")
    for pattern in noise_patterns:
        print(f"   - {pattern}")
else:
    print(f"\n✅ No obvious noise patterns detected")

# Final verdict
print(f"\n{'=' * 70}")
issues = []
if name_equals_xpath:
    issues.append("ElementName = XPath mismatch")
if invalid_xpaths:
    issues.append("Invalid XPath format")
if minimal_info:
    issues.append("Rows with minimal identifiers")

if issues:
    print(f"⚠️ FILE HAS {len(issues)} POTENTIAL ISSUES")
    for issue in issues:
        print(f"   - {issue}")
else:
    print(f"✅ FILE APPEARS CLEAN")
print("=" * 70)
