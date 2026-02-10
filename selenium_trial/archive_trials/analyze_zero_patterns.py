"""
Analyze patterns in pages that returned 0 elements vs pages with elements.
Look for URL patterns, page name patterns, timing correlations.
"""
import openpyxl
import json
from collections import defaultdict

EXCEL_FILE = "uiMap_selenium_fullrun_auto4_cleaned.xlsx"
RESCREEN_FILE = "items_to_rescreen.json"

def analyze_patterns():
    print("="*70)
    print("PATTERN ANALYSIS: 0-Element Pages")
    print("="*70)
    
    print("\n⚠️ NOTE: '0-element' is inferred, not measured directly!")
    print("   Logic: Pages in checkpoint but NOT in Excel = 0 elements")
    print("   Could be:")
    print("     - Truly no input fields (read-only pages)")
    print("     - Fields in iframes (not checked)")
    print("     - Timing issues (page didn't load)")
    print("     - Popup didn't open properly")
    print("     - Silent errors during extraction")
    
    # Load Excel
    wb = openpyxl.load_workbook(EXCEL_FILE)
    ws = wb.active
    
    # Load 0-element list
    with open(RESCREEN_FILE, 'r') as f:
        zero_element_pages = set(json.load(f)['items_to_rescreen'])
    
    # Collect data
    pages_with_elements = defaultdict(int)
    urls_with_elements = set()
    urls_zero_elements = set()
    
    for row in ws.iter_rows(min_row=2, values_only=True):
        page_name = row[0]
        url = row[2] if len(row) > 2 else None
        
        if page_name and page_name not in zero_element_pages:
            pages_with_elements[page_name] += 1
            if url:
                urls_with_elements.add(url)
    
    print(f"\n📊 Summary:")
    print(f"   Pages with 0 elements: {len(zero_element_pages)}")
    print(f"   Pages with elements: {len(pages_with_elements)}")
    print(f"   Total unique pages: {len(zero_element_pages) + len(pages_with_elements)}")
    
    # Pattern 1: Page name patterns
    print(f"\n🔍 Pattern Analysis - Common Words in 0-Element Pages:")
    word_counts = defaultdict(int)
    for page in zero_element_pages:
        words = page.lower().split()
        for word in words:
            if len(word) > 3:  # Skip short words
                word_counts[word] += 1
    
    # Show top 20 words
    top_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)[:20]
    for word, count in top_words:
        print(f"   {word:20s}: {count:4d} pages")
    
    # Pattern 2: Check if certain types return 0
    print(f"\n🔍 Pattern Analysis - Page Type Keywords:")
    keywords = ['enquiry', 'enquiries', 'query', 'search', 'report', 'list', 'view', 
                'create', 'new', 'input', 'entry', 'maintenance', 'setup', 'definition']
    
    for keyword in keywords:
        zero_with_keyword = sum(1 for p in zero_element_pages if keyword in p.lower())
        total_with_keyword = zero_with_keyword + sum(1 for p in pages_with_elements if keyword in p.lower())
        if total_with_keyword > 0:
            pct = (zero_with_keyword / total_with_keyword) * 100
            print(f"   {keyword:20s}: {zero_with_keyword:3d}/{total_with_keyword:3d} are zero ({pct:5.1f}%)")
    
    # Pattern 3: Show some examples
    print(f"\n📋 Sample 0-Element Pages (first 30):")
    for i, page in enumerate(sorted(list(zero_element_pages))[:30], 1):
        print(f"   {i:2d}. {page}")
    
    print(f"\n📋 Sample Pages WITH Elements (first 30):")
    for i, page in enumerate(sorted(list(pages_with_elements.keys()))[:30], 1):
        count = pages_with_elements[page]
        print(f"   {i:2d}. {page} ({count} elements)")

if __name__ == "__main__":
    analyze_patterns()
