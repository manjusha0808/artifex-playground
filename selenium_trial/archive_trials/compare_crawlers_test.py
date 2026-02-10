"""
Side-by-side comparison: Old crawler vs New fast crawler
Tests on specific pages to see what's different.
"""

import time
import os
import pandas as pd
from dotenv import load_dotenv
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

load_dotenv()

from crawler import setup_driver, login, get_menu_frame, expand_all_menus_recursive

# Load old crawler results
print("="*70)
print("LOADING OLD CRAWLER RESULTS")
print("="*70)

old_df = pd.read_excel('uiMap_selenium_fullrun_auto4_cleaned.xlsx')
print(f"✅ Loaded {len(old_df)} records from old crawler\n")

# Test pages
TEST_PAGES = [
    "Input Prospect (Person)",
    "Authorise / Delete Person records",
    "Input Prospect (Entity)"
]

def extract_from_page_new_method(driver, page_name):
    """Use new fast extraction method."""
    extracted = []
    selector = 'input, select, textarea'
    
    def extract_from_context(context_name="main"):
        found = []
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            for elem in elements:
                try:
                    tag = elem.tag_name
                    elem_id = elem.get_attribute('id') or ''
                    elem_name = elem.get_attribute('name') or ''
                    elem_type = elem.get_attribute('type') or ''
                    
                    # Skip hidden inputs
                    if tag == 'input' and elem_type == 'hidden':
                        continue
                    
                    if not elem_id and not elem_name:
                        continue
                    
                    if elem_id:
                        xpath = f"//{tag}[@id='{elem_id}']"
                    elif elem_name:
                        xpath = f"//{tag}[@name='{elem_name}']"
                    else:
                        continue
                    
                    found.append({
                        'xpath': xpath,
                        'id': elem_id,
                        'name': elem_name,
                        'tag': tag,
                        'type': elem_type,
                        'context': context_name
                    })
                except:
                    continue
        except:
            pass
        return found
    
    # Main document
    main_results = extract_from_context("main")
    extracted.extend(main_results)
    
    # Iframes
    try:
        iframes = driver.find_elements(By.TAG_NAME, 'iframe')
        for idx, iframe in enumerate(iframes):
            try:
                driver.switch_to.frame(iframe)
                iframe_results = extract_from_context(f"iframe_{idx}")
                extracted.extend(iframe_results)
                driver.switch_to.default_content()
            except:
                try:
                    driver.switch_to.default_content()
                except:
                    pass
    except:
        pass
    
    return extracted


def compare_page(driver, page_name):
    """Open page and compare old vs new extraction."""
    
    print("\n" + "="*70)
    print(f"TESTING: {page_name}")
    print("="*70)
    
    # Get old crawler results for this page
    old_results = old_df[old_df['pageName'] == page_name]
    
    print(f"\n📊 OLD CRAWLER (from auto4_cleaned.xlsx):")
    print(f"   Total XPaths: {len(old_results)}")
    if len(old_results) > 0:
        tag_counts = old_results['tagName'].value_counts()
        print(f"   Tags: {dict(tag_counts)}")
        print(f"\n   Sample (first 5):")
        for idx, row in old_results.head(5).iterrows():
            print(f"   - {row['relativeXpath'][:60]}")
            print(f"     ID: {row['elementId']}, Name: {row['elementNameAttr']}, Tag: {row['tagName']}")
    
    # Open page with new method
    driver.switch_to.default_content()
    get_menu_frame(driver)
    
    try:
        link = driver.find_element(By.XPATH, f".//a[starts-with(@href,'javascript:docommand(') and text()='{page_name}']")
    except:
        link = driver.find_element(By.XPATH, f".//a[starts-with(@href,'javascript:docommand(') and contains(text(),'{page_name[:20]}')]")
    
    main_window = driver.current_window_handle
    link.click()
    
    # Wait for popup
    WebDriverWait(driver, 2).until(lambda d: len(d.window_handles) > 1)
    driver.switch_to.window(driver.window_handles[-1])
    
    # Wait for fields to load
    WebDriverWait(driver, 2).until(EC.presence_of_element_located((By.TAG_NAME, 'body')))
    try:
        WebDriverWait(driver, 3).until(
            lambda d: len(d.find_elements(By.CSS_SELECTOR, 'input, select, textarea')) > 0
        )
    except:
        pass
    
    # Extract with new method
    new_results = extract_from_page_new_method(driver, page_name)
    
    print(f"\n⚡ NEW CRAWLER (fast method with iframes):")
    print(f"   Total XPaths: {len(new_results)}")
    
    if len(new_results) > 0:
        # Count by tag
        tag_counts = {}
        context_counts = {}
        for r in new_results:
            tag_counts[r['tag']] = tag_counts.get(r['tag'], 0) + 1
            context_counts[r['context']] = context_counts.get(r['context'], 0) + 1
        
        print(f"   Tags: {tag_counts}")
        print(f"   Context: {context_counts}")
        
        print(f"\n   Sample (first 5):")
        for r in new_results[:5]:
            print(f"   - {r['xpath'][:60]}")
            print(f"     ID: {r['id']}, Name: {r['name']}, Tag: {r['tag']}, Context: {r['context']}")
    
    # Comparison
    print(f"\n📈 COMPARISON:")
    diff = len(new_results) - len(old_results)
    if diff > 0:
        print(f"   ✅ New crawler found {diff} MORE XPaths (+{diff/len(old_results)*100:.1f}%)")
        
        # Show what's new
        old_ids = set(old_results['elementId'].dropna())
        new_ids = set(r['id'] for r in new_results if r['id'])
        additional_ids = new_ids - old_ids
        if len(additional_ids) > 0:
            print(f"   New unique IDs found: {len(additional_ids)}")
            print(f"   Examples: {list(additional_ids)[:5]}")
    elif diff < 0:
        print(f"   ⚠️ New crawler found {abs(diff)} FEWER XPaths ({diff/len(old_results)*100:.1f}%)")
    else:
        print(f"   ✅ Both found the same number of XPaths")
    
    # Check if new crawler found fields in iframes
    iframe_fields = [r for r in new_results if 'iframe' in r['context']]
    if len(iframe_fields) > 0:
        print(f"\n   🔥 NEW: Found {len(iframe_fields)} fields inside iframes!")
        print(f"   Sample iframe fields:")
        for r in iframe_fields[:3]:
            print(f"   - {r['xpath'][:60]} [{r['context']}]")
    
    # Close popup
    driver.close()
    driver.switch_to.window(main_window)


def main():
    driver = setup_driver()
    
    try:
        # Login
        print("\n🔐 Logging in...")
        url = os.getenv('T24_URL')
        username = os.getenv('T24_USERNAME')
        password = os.getenv('T24_PASSWORD')
        login(driver, url, username, password)
        
        # Expand menu
        print("🔧 Expanding menu...")
        expand_all_menus_recursive(driver)
        time.sleep(1)
        
        # Test each page
        for page in TEST_PAGES:
            try:
                compare_page(driver, page)
            except Exception as e:
                print(f"\n❌ Error testing {page}: {e}")
        
        print("\n" + "="*70)
        print("✅ COMPARISON COMPLETE")
        print("="*70)
        
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        try:
            driver.quit()
        except:
            pass


if __name__ == "__main__":
    main()
