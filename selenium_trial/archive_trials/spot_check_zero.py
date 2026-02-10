"""
Manual spot-check: Open random 0-element pages and pause for inspection.
Simpler than debug_zero_elements.py - just opens pages and waits.
"""
import json
import random
from crawler import setup_driver, login, get_menu_frame, expand_all_menus_recursive
from selenium.webdriver.common.by import By
import time
import os
from dotenv import load_dotenv

load_dotenv()

T24_URL = os.getenv('T24_URL')
T24_USERNAME = os.getenv('T24_USERNAME')
T24_PASSWORD = os.getenv('T24_PASSWORD')

def manual_spot_check():
    # Load 0-element pages
    with open('items_to_rescreen.json', 'r') as f:
        all_zero_pages = json.load(f)['items_to_rescreen']
    
    # Pick 5 random pages
    sample_pages = random.sample(all_zero_pages, min(5, len(all_zero_pages)))
    
    print("="*70)
    print("MANUAL SPOT CHECK - Random 0-Element Pages")
    print("="*70)
    print(f"\nSelected {len(sample_pages)} random pages:\n")
    for i, page in enumerate(sample_pages, 1):
        print(f"{i}. {page}")
    
    input("\nPress Enter to start...")
    
    driver = setup_driver()
    
    try:
        # Login
        login(driver, T24_URL, T24_USERNAME, T24_PASSWORD)
        print("✅ Logged in")
        
        # Expand menu
        expand_all_menus_recursive(driver)
        
        # Get menu frame
        menu_frame = get_menu_frame(driver, wait=True)
        
        # Find all menu links
        all_links = driver.find_elements(By.TAG_NAME, 'a')
        menu_map = {}
        
        for i, link in enumerate(all_links):
            try:
                text = link.text.strip()
                href = link.get_attribute('href') or ''
                if text and 'javascript' in href.lower():
                    menu_map[text] = (i, link)
            except:
                pass
        
        print(f"\n✅ Built menu map with {len(menu_map)} clickable items")
        
        # Open each page
        for page_name in sample_pages:
            print(f"\n{'='*70}")
            print(f"PAGE: {page_name}")
            print('='*70)
            
            if page_name not in menu_map:
                print(f"❌ Not found in menu")
                continue
            
            idx, link = menu_map[page_name]
            
            # Re-find link
            menu_frame = get_menu_frame(driver, wait=False)
            all_links = driver.find_elements(By.TAG_NAME, 'a')
            
            if idx < len(all_links):
                link = all_links[idx]
                
                try:
                    link.click()
                    time.sleep(2)
                    
                    # Switch to popup if opened
                    if len(driver.window_handles) > 1:
                        driver.switch_to.window(driver.window_handles[-1])
                    
                    print(f"\n✅ Page opened")
                    print(f"📊 Title: {driver.title}")
                    
                    # Quick check
                    inputs = driver.find_elements(By.TAG_NAME, 'input')
                    selects = driver.find_elements(By.TAG_NAME, 'select')
                    textareas = driver.find_elements(By.TAG_NAME, 'textarea')
                    
                    print(f"📊 Quick count:")
                    print(f"   INPUT: {len(inputs)}")
                    print(f"   SELECT: {len(selects)}")
                    print(f"   TEXTAREA: {len(textareas)}")
                    
                    # Check for error messages
                    body_text = driver.find_element(By.TAG_NAME, 'body').text.lower()
                    error_keywords = ['error', 'access denied', 'permission', 'not authorized', 'no data']
                    found_errors = [kw for kw in error_keywords if kw in body_text]
                    if found_errors:
                        print(f"⚠️ Found error keywords: {', '.join(found_errors)}")
                    
                    print(f"\n👁️ Browser open for inspection")
                    print(f"   Check DevTools Console for errors")
                    print(f"   Check if fields are in iframes")
                    print(f"   Check if fields load after delay")
                    
                    input("\n   Press Enter for next page...")
                    
                    # Close popup
                    if len(driver.window_handles) > 1:
                        driver.close()
                        driver.switch_to.window(driver.window_handles[0])
                    
                except Exception as e:
                    print(f"❌ Error: {e}")
        
        print("\n" + "="*70)
        print("✅ Spot check complete!")
        print("="*70)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        input("\nPress Enter to close browser...")
        driver.quit()

if __name__ == "__main__":
    manual_spot_check()
