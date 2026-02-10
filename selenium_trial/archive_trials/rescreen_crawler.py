"""
Rescreen-only crawler: processes specific menu items that had 0 elements.
Uses items_to_rescreen.json to target specific menu items by name.
"""
import json
import sys
from crawler import (
    setup_driver, login, get_menu_frame, expand_all_menus_recursive,
    extract_xpaths_from_page, export_to_excel, load_existing_data
)
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

# Configuration
RESCREEN_LIST_FILE = "items_to_rescreen.json"
OUTPUT_FILE = "uiMap_selenium_fullrun_auto4_cleaned.xlsx"

def load_rescreen_list():
    """Load list of items that need rescreening."""
    try:
        with open(RESCREEN_LIST_FILE, 'r') as f:
            data = json.load(f)
        items = set(data['items_to_rescreen'])
        print(f"📋 Loaded {len(items)} items to rescreen")
        return items
    except FileNotFoundError:
        print(f"❌ File not found: {RESCREEN_LIST_FILE}")
        print("   Run 'rescreen_zero_elements.py' first to generate the list")
        sys.exit(1)

def rescreen_menu(driver):
    """Re-screen only specific menu items."""
    print("\n🔄 Starting Rescreening Process")
    print("=" * 70)
    
    # Load items to rescreen
    items_to_rescreen = load_rescreen_list()
    
    # Load existing data
    all_data = []
    global_seen_rows = set()
    
    if os.path.exists(OUTPUT_FILE):
        all_data = load_existing_data(OUTPUT_FILE)
        print(f"📂 Loaded {len(all_data)} existing records")
        # Build global seen set
        for item in all_data:
            row_key = (
                item.get('page', ''),
                item.get('relativeXpath', ''),
                item.get('elementName', ''),
                item.get('id', ''),
                item.get('name', ''),
                item.get('className', ''),
                item.get('tagName', ''),
                item.get('type', '')
            )
            global_seen_rows.add(row_key)
    
    # Expand menu
    print("\n🔧 Expanding menu structure...")
    expand_all_menus_recursive(driver)
    
    # Get all menu items (build once)
    print("📋 Building menu list...")
    menu_frame = get_menu_frame(driver, wait=True)
    menu_items = driver.find_elements(By.CSS_SELECTOR, 'a.menuitem[href*="javascript:doit"]')
    print(f"   Found {len(menu_items)} clickable items")
    
    # Filter to only items that need rescreening
    items_to_process = []
    for i, link in enumerate(menu_items):
        try:
            text = link.text.strip()
            if text in items_to_rescreen:
                items_to_process.append((i, link, text))
        except:
            continue
    
    print(f"\n🎯 Found {len(items_to_process)} items to rescreen (out of {len(items_to_rescreen)} requested)")
    
    # Process each item
    new_elements_found = 0
    processed_count = 0
    
    for idx, (original_idx, link, text) in enumerate(items_to_process, 1):
        print(f"\n[{idx}/{len(items_to_process)}] {text}")
        
        try:
            # Rebuild menu list before each click
            menu_frame = get_menu_frame(driver, wait=False)
            current_menu_items = driver.find_elements(By.CSS_SELECTOR, 'a.menuitem[href*="javascript:doit"]')
            link = current_menu_items[original_idx]
            
            # Click the link
            main_window = driver.current_window_handle
            
            try:
                link.click()
            except:
                driver.execute_script("arguments[0].click();", link)
            
            time.sleep(0.3)
            
            # Check if popup opened
            windows = driver.window_handles
            if len(windows) > 1:
                driver.switch_to.window(windows[-1])
                time.sleep(0.2)
                
                # Extract XPaths
                extracted = extract_xpaths_from_page(driver, text, global_seen_rows)
                all_data.extend(extracted)
                
                if extracted:
                    new_elements_found += len(extracted)
                    print(f"    ✅ {len(extracted)} new elements")
                else:
                    print(f"    ⚠️ Still 0 elements")
                
                # Close popup
                driver.close()
                driver.switch_to.window(main_window)
            else:
                print(f"    ⚠️ No popup opened")
            
            processed_count += 1
            
            # Save every 10 items
            if processed_count % 10 == 0:
                export_to_excel(all_data, OUTPUT_FILE)
                print(f"\n💾 Progress saved ({new_elements_found} new elements so far)")
        
        except Exception as e:
            print(f"    ❌ Error: {e}")
            continue
    
    # Final save
    print(f"\n{'=' * 70}")
    print(f"🎉 Rescreening Complete!")
    print(f"{'=' * 70}")
    print(f"   Items processed: {processed_count}")
    print(f"   New elements found: {new_elements_found}")
    print(f"   Total elements: {len(all_data)}")
    
    export_to_excel(all_data, OUTPUT_FILE)
    print(f"\n💾 Final data saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    import os
    
    driver = setup_driver()
    
    try:
        print("🔐 Logging in...")
        if not login(driver):
            print("❌ Login failed")
            driver.quit()
            sys.exit(1)
        
        print("✅ Login successful")
        
        # Run rescreening
        rescreen_menu(driver)
        
    except KeyboardInterrupt:
        print("\n\n⚠️ Interrupted by user")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        driver.quit()
        print("\n✅ Browser closed")
