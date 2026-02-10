"""
Debug script to investigate why specific pages return 0 elements.
Opens a few pages and shows what's actually on them.
"""
import json
import sys
import os
from dotenv import load_dotenv
from crawler import setup_driver, login, get_menu_frame, expand_all_menus_recursive
from selenium.webdriver.common.by import By
import time

# Load environment variables
load_dotenv()

T24_URL = os.getenv('BASE_URL')
T24_USERNAME = os.getenv('APP_USERNAME')
T24_PASSWORD = os.getenv('APP_PASSWORD')

# Pages to debug (first 5 from the list)
DEBUG_PAGES = [
    "AA - Product Catalog",
    "ADR/GDR Conversions Details", 
    "API Designer",
    "Acceptance of Documents",
    "Account Closure"
]

def analyze_page_content(driver, page_name):
    """Analyze what's actually on the page."""
    print(f"\n{'='*70}")
    print(f"ANALYZING: {page_name}")
    print('='*70)
    
    # Get current windows
    windows = driver.window_handles
    if len(windows) > 1:
        driver.switch_to.window(windows[-1])
        print(f"✓ Switched to popup window")
    
    # Wait for page to load
    time.sleep(2)
    
    # Check 1: All input elements
    all_inputs = driver.find_elements(By.TAG_NAME, 'input')
    print(f"\n📊 INPUT elements found: {len(all_inputs)}")
    if all_inputs:
        for i, inp in enumerate(all_inputs[:10], 1):
            inp_type = inp.get_attribute('type') or 'no-type'
            inp_name = inp.get_attribute('name') or 'no-name'
            inp_id = inp.get_attribute('id') or 'no-id'
            visible = inp.is_displayed()
            print(f"   [{i}] type={inp_type:15s} name={inp_name[:20]:20s} visible={visible}")
        if len(all_inputs) > 10:
            print(f"   ... and {len(all_inputs) - 10} more")
    
    # Check 2: Select dropdowns
    selects = driver.find_elements(By.TAG_NAME, 'select')
    print(f"\n📊 SELECT elements found: {len(selects)}")
    if selects:
        for i, sel in enumerate(selects[:5], 1):
            sel_name = sel.get_attribute('name') or 'no-name'
            visible = sel.is_displayed()
            print(f"   [{i}] name={sel_name[:30]:30s} visible={visible}")
    
    # Check 3: Textarea
    textareas = driver.find_elements(By.TAG_NAME, 'textarea')
    print(f"\n📊 TEXTAREA elements found: {len(textareas)}")
    
    # Check 4: Buttons and links (not in crawler but might indicate why no inputs)
    buttons = driver.find_elements(By.TAG_NAME, 'button')
    links = driver.find_elements(By.TAG_NAME, 'a')
    print(f"\n📊 Other elements:")
    print(f"   BUTTON: {len(buttons)}")
    print(f"   LINK: {len(links)}")
    
    # Check 5: Is it an iframe?
    iframes = driver.find_elements(By.TAG_NAME, 'iframe')
    print(f"   IFRAME: {len(iframes)}")
    
    # Check 6: Page source keywords
    page_source = driver.page_source.lower()
    keywords = ['no data', 'empty', 'error', 'access denied', 'permission']
    print(f"\n📊 Page content check:")
    for keyword in keywords:
        if keyword in page_source:
            print(f"   ⚠️ Contains '{keyword}'")
    
    # Check 7: Screenshot page title
    try:
        title = driver.title
        print(f"\n📊 Page title: {title}")
    except:
        pass
    
    # Wait for user inspection
    print(f"\n👁️ Browser window is open for manual inspection")
    input("   Press Enter to continue to next page...")
    
    # Close popup if opened
    if len(driver.window_handles) > 1:
        driver.close()
        driver.switch_to.window(driver.window_handles[0])


def main():
    print("="*70)
    print("DEBUG: Zero Element Pages Investigation")
    print("="*70)
    print(f"\nWill investigate {len(DEBUG_PAGES)} pages to understand why they have 0 elements")
    
    driver = setup_driver()
    
    try:
        # Login
        print("\n🔐 Logging in...")
        login(driver, T24_URL, T24_USERNAME, T24_PASSWORD)
        print("✅ Login successful")
        
        # Expand menu
        print("\n🔧 Expanding menu...")
        expand_all_menus_recursive(driver)
        time.sleep(2)
        
        # Get menu items - try multiple selectors
        menu_frame = get_menu_frame(driver, wait=True)
        
        # Try different selectors
        menu_items = driver.find_elements(By.CSS_SELECTOR, 'a.menuitem[href*="javascript:doit"]')
        if not menu_items:
            menu_items = driver.find_elements(By.CSS_SELECTOR, 'a[href*="javascript:doit"]')
        if not menu_items:
            menu_items = driver.find_elements(By.CSS_SELECTOR, 'a.menuitem')
        if not menu_items:
            menu_items = driver.find_elements(By.CSS_SELECTOR, 'a[class*="menu"]')
        
        print(f"✅ Found {len(menu_items)} menu items")
        
        if len(menu_items) == 0:
            print("\n❌ No menu items found! Showing all links in menu frame:")
            all_links = driver.find_elements(By.TAG_NAME, 'a')
            print(f"   Total <a> tags: {len(all_links)}")
            for i, link in enumerate(all_links[:10], 1):
                href = link.get_attribute('href') or 'no-href'
                text = link.text.strip() or 'no-text'
                classes = link.get_attribute('class') or 'no-class'
                print(f"   [{i}] {text[:30]:30s} | class={classes[:20]} | href={href[:40]}")
            print("\n⚠️ Cannot proceed without menu items")
            return
        
        # Build menu map
        menu_map = {}
        for i, link in enumerate(menu_items):
            try:
                text = link.text.strip()
                menu_map[text] = (i, link)
            except:
                pass
        
        # Process each debug page
        for page_name in DEBUG_PAGES:
            if page_name not in menu_map:
                print(f"\n❌ Page not found in menu: {page_name}")
                continue
            
            idx, link = menu_map[page_name]
            
            print(f"\n{'='*70}")
            print(f"Opening: {page_name}")
            print('='*70)
            
            # Re-find the element (menu might refresh)
            menu_frame = get_menu_frame(driver, wait=False)
            current_menu_items = driver.find_elements(By.CSS_SELECTOR, 'a.menuitem[href*="javascript:doit"]')
            
            if idx < len(current_menu_items):
                link = current_menu_items[idx]
                
                try:
                    link.click()
                    time.sleep(2)
                    
                    # Analyze the page
                    analyze_page_content(driver, page_name)
                    
                except Exception as e:
                    print(f"❌ Error opening page: {e}")
                    continue
        
        print("\n" + "="*70)
        print("✅ Investigation complete!")
        print("="*70)
        
    except KeyboardInterrupt:
        print("\n\n👋 Interrupted")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        try:
            driver.quit()
        except:
            pass


if __name__ == "__main__":
    main()
