"""
Debug script to inspect iframe contents and understand why fields aren't being extracted.
Opens "Input Prospect (Person)" page and prints detailed iframe analysis.
"""

import time
import os
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By

load_dotenv()

from crawler import setup_driver, login, get_menu_frame, expand_all_menus_recursive


def debug_page_structure(driver, page_name="Input Prospect (Person)"):
    """Debug a specific page to see iframe structure."""
    
    print("="*70)
    print(f"DEBUGGING: {page_name}")
    print("="*70)
    
    # Open the page
    driver.switch_to.default_content()
    get_menu_frame(driver)
    
    try:
        link = driver.find_element(By.XPATH, f".//a[starts-with(@href,'javascript:docommand(') and text()='{page_name}']")
    except:
        link = driver.find_element(By.XPATH, f".//a[starts-with(@href,'javascript:docommand(') and contains(text(),'{page_name[:20]}')]")
    
    main_window = driver.current_window_handle
    link.click()
    time.sleep(0.5)
    
    # Switch to popup
    windows = driver.window_handles
    if len(windows) > 1:
        driver.switch_to.window(windows[-1])
        
        # Wait longer for page to fully load
        print("\n⏱️ Waiting 5 seconds for page to fully load...")
        time.sleep(5)
        
        # Take screenshot
        try:
            screenshot_path = f"page_screenshot_{int(time.time())}.png"
            driver.save_screenshot(screenshot_path)
            print(f"📸 Screenshot saved: {screenshot_path}")
        except:
            pass
        
        print("\n📍 MAIN DOCUMENT ANALYSIS")
        print("-" * 70)
        
        # Check main document
        main_inputs = driver.find_elements(By.TAG_NAME, 'input')
        main_selects = driver.find_elements(By.TAG_NAME, 'select')
        main_textareas = driver.find_elements(By.TAG_NAME, 'textarea')
        
        print(f"Main document elements:")
        print(f"  <input> tags: {len(main_inputs)}")
        print(f"  <select> tags: {len(main_selects)}")
        print(f"  <textarea> tags: {len(main_textareas)}")
        
        if len(main_inputs) > 0:
            print(f"\nFirst 3 input samples from main:")
            for i, inp in enumerate(main_inputs[:3]):
                print(f"  {i+1}. type={inp.get_attribute('type')} id={inp.get_attribute('id')} name={inp.get_attribute('name')}")
        
        # Find iframes
        iframes = driver.find_elements(By.TAG_NAME, 'iframe')
        print(f"\n📦 Found {len(iframes)} iframe(s)")
        
        # Analyze each iframe
        for idx, iframe in enumerate(iframes):
            print(f"\n{'='*70}")
            print(f"IFRAME #{idx}")
            print("-" * 70)
            
            # Get iframe attributes
            iframe_id = iframe.get_attribute('id')
            iframe_name = iframe.get_attribute('name')
            iframe_src = iframe.get_attribute('src')
            
            print(f"Attributes:")
            print(f"  id: {iframe_id}")
            print(f"  name: {iframe_name}")
            print(f"  src: {iframe_src[:100] if iframe_src else 'None'}")
            
            try:
                # Switch into iframe
                driver.switch_to.frame(iframe)
                
                # Count elements
                iframe_inputs = driver.find_elements(By.TAG_NAME, 'input')
                iframe_selects = driver.find_elements(By.TAG_NAME, 'select')
                iframe_textareas = driver.find_elements(By.TAG_NAME, 'textarea')
                
                print(f"\nElements inside iframe:")
                print(f"  <input> tags: {len(iframe_inputs)}")
                print(f"  <select> tags: {len(iframe_selects)}")
                print(f"  <textarea> tags: {len(iframe_textareas)}")
                
                # Show samples
                if len(iframe_inputs) > 0:
                    print(f"\n  First 5 input samples:")
                    for i, inp in enumerate(iframe_inputs[:5]):
                        inp_type = inp.get_attribute('type') or 'text'
                        inp_id = inp.get_attribute('id') or ''
                        inp_name = inp.get_attribute('name') or ''
                        inp_class = inp.get_attribute('class') or ''
                        displayed = "visible" if inp.is_displayed() else "hidden"
                        print(f"    {i+1}. <input type='{inp_type}' id='{inp_id}' name='{inp_name}' class='{inp_class[:30]}' [{displayed}]")
                
                if len(iframe_selects) > 0:
                    print(f"\n  First 3 select samples:")
                    for i, sel in enumerate(iframe_selects[:3]):
                        sel_id = sel.get_attribute('id') or ''
                        sel_name = sel.get_attribute('name') or ''
                        displayed = "visible" if sel.is_displayed() else "hidden"
                        print(f"    {i+1}. <select id='{sel_id}' name='{sel_name}' [{displayed}]")
                
                # Check for nested iframes
                nested_iframes = driver.find_elements(By.TAG_NAME, 'iframe')
                if len(nested_iframes) > 0:
                    print(f"\n  ⚠️ Found {len(nested_iframes)} NESTED iframe(s) inside this iframe!")
                    for nidx, niframe in enumerate(nested_iframes):
                        nid = niframe.get_attribute('id')
                        nname = niframe.get_attribute('name')
                        print(f"    Nested iframe {nidx}: id={nid} name={nname}")
                
                # Test the CSS selector
                print(f"\n  Testing CSS selector:")
                selector = '''
                    input[type="text"], input[type="password"], input[type="email"],
                    input[type="number"], input[type="tel"], input[type="date"],
                    input[type="time"], input[type="datetime-local"], input[type="search"],
                    input[type="url"], input[type="checkbox"], input[type="radio"],
                    input:not([type]), textarea, select
                '''
                matched_elements = driver.find_elements(By.CSS_SELECTOR, selector)
                print(f"    CSS selector matched: {len(matched_elements)} elements")
                
                if len(matched_elements) == 0 and len(iframe_inputs) > 0:
                    print(f"    🔥 ISSUE: {len(iframe_inputs)} inputs exist but 0 matched by selector!")
                    print(f"    Checking input types:")
                    type_counts = {}
                    for inp in iframe_inputs[:20]:
                        inp_type = inp.get_attribute('type') or 'no-type'
                        type_counts[inp_type] = type_counts.get(inp_type, 0) + 1
                    for itype, count in type_counts.items():
                        print(f"      type='{itype}': {count}")
                
                # Switch back to main
                driver.switch_to.default_content()
                
            except Exception as e:
                print(f"\n  ❌ Error accessing iframe: {e}")
                driver.switch_to.default_content()
        
        # Close popup
        driver.close()
        driver.switch_to.window(main_window)
        
        print("\n" + "="*70)
        print("✅ Debug complete")


def main():
    driver = setup_driver()
    
    try:
        # Login
        print("🔐 Logging in...")
        url = os.getenv('T24_URL')
        username = os.getenv('T24_USERNAME')
        password = os.getenv('T24_PASSWORD')
        login(driver, url, username, password)
        print("✅ Logged in\n")
        
        # Expand menu
        print("🔧 Expanding menu...")
        expand_all_menus_recursive(driver)
        time.sleep(1)
        
        # Debug the page
        debug_page_structure(driver, "Input Prospect (Person)")
        
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
