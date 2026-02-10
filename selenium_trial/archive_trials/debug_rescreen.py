"""
DEBUG: Test rescreen on 3 specific pages with detailed logging
"""

import os
import time
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

load_dotenv()

# TEST PAGES - Replace with your 3 pages that have fields
TEST_PAGES = [
    "Activate Customer",
    "Create KYC",
    "Issue LCY Drafts against Cash"
]

def setup_driver():
    """Setup Chrome driver"""
    chrome_options = Options()
    chrome_options.add_argument('--start-maximized')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
    driver = webdriver.Chrome(options=chrome_options)
    driver.implicitly_wait(3)
    return driver

def login(driver):
    """Login to T24"""
    url = os.getenv('APP_URL', 'http://10.0.251.41:18080/BrowserWeb/servlet/BrowserServlet')
    username = os.getenv('APP_USERNAME', 'MB.OFFICER')
    password = os.getenv('APP_PASSWORD', '123456')
    
    print(f"🌐 Navigating to {url}")
    driver.get(url)
    time.sleep(2)
    
    print(f"🔐 Logging in as {username}")
    driver.find_element(By.NAME, 'signOnName').send_keys(username)
    driver.find_element(By.NAME, 'password').send_keys(password)
    driver.find_element(By.CSS_SELECTOR, 'input[type="submit"]').click()
    time.sleep(3)
    print("✅ Login successful")

def get_menu_frame(driver):
    """Switch to menu frame"""
    driver.switch_to.default_content()
    frames = driver.find_elements(By.TAG_NAME, 'frame')
    
    print(f"   🔍 Found {len(frames)} frames")
    for idx, frame in enumerate(frames):
        frame_name = frame.get_attribute('name') or ''
        print(f"      Frame {idx}: {frame_name}")
        if 'menu' in frame_name.lower():
            driver.switch_to.frame(frame)
            print(f"   ✅ Switched to menu frame: {frame_name}")
            return True
    return False

def expand_all_menus(driver):
    """Expand all menu items"""
    print("\n🔧 Expanding all menu items...")
    expanded_total = 0
    max_passes = 20
    
    for pass_num in range(max_passes):
        try:
            container = driver.find_element(By.XPATH, "//div[starts-with(@id,'pane')]")
            expand_icons = container.find_elements(By.XPATH, ".//span[contains(@onclick, 'ProcessMouseClick')]")
            
            if not expand_icons:
                break
            
            expanded_this_pass = 0
            for icon in expand_icons:
                try:
                    parent_li = icon.find_element(By.XPATH, "./ancestor::li[1]")
                    child_uls = parent_li.find_elements(By.XPATH, "./ul")
                    
                    if child_uls and not any(ul.is_displayed() for ul in child_uls):
                        icon.click()
                        expanded_this_pass += 1
                        time.sleep(0.05)
                except:
                    continue
            
            expanded_total += expanded_this_pass
            
            if expanded_this_pass == 0:
                print(f"✅ All menus expanded ({expanded_total} nodes)")
                break
            
            time.sleep(0.1)
        except:
            break
    
    return expanded_total

def debug_frame_info(driver):
    """Debug: Print all frames and their info"""
    driver.switch_to.default_content()
    frames = driver.find_elements(By.TAG_NAME, 'frame')
    print(f"\n   🔍 DEBUG: Found {len(frames)} frames:")
    
    for idx, frame in enumerate(frames):
        name = frame.get_attribute('name') or 'unnamed'
        src = frame.get_attribute('src') or 'no-src'
        print(f"      [{idx}] Name: {name}, Src: {src[:60]}...")

def wait_for_page_and_detect_fields(driver, page_name):
    """Wait for page to load and detect fields with detailed debugging"""
    print(f"\n   ⏳ Waiting for page to load...")
    
    try:
        # Store main window
        main_window = driver.current_window_handle
        
        # Wait for popup window to open
        time.sleep(1)
        windows = driver.window_handles
        print(f"   🪟 Window handles: {len(windows)} windows")
        
        if len(windows) > 1:
            # Switch to popup window
            driver.switch_to.window(windows[-1])
            print(f"   ✅ Switched to popup window")
        else:
            print(f"   ⚠️ No popup window opened, checking frames...")
            # Fallback: check frames
            driver.switch_to.default_content()
            frames = driver.find_elements(By.TAG_NAME, 'frame')
            
            for frame in frames:
                frame_name = frame.get_attribute('name') or ''
                if 'display' in frame_name.lower() or 'content' in frame_name.lower():
                    driver.switch_to.frame(frame)
                    print(f"   ✅ Switched to display frame: {frame_name}")
                    break
        
        # Wait for page to complete
        WebDriverWait(driver, 8).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        time.sleep(2)
        print(f"   ✅ Page ready state: complete")
        
        # Take screenshot for debugging
        try:
            screenshot_path = f"debug_{page_name.replace('/', '_')[:30]}.png"
            driver.save_screenshot(screenshot_path)
            print(f"   📸 Screenshot saved: {screenshot_path}")
        except:
            pass
        
        # Check for iframes in the popup/frame
        try:
            iframes = driver.find_elements(By.TAG_NAME, 'iframe')
            if iframes:
                print(f"   🔍 Found {len(iframes)} nested iframes")
                driver.switch_to.frame(iframes[0])
                print(f"   ✅ Switched to nested iframe")
                time.sleep(0.5)
        except:
            pass
        
        # CRITICAL: Check for FRAMES in the popup (not iframes)
        try:
            frames = driver.find_elements(By.TAG_NAME, 'frame')
            if frames:
                print(f"   🔍 Found {len(frames)} frames in popup")
                # Try first frame (usually contains the form)
                driver.switch_to.frame(frames[0])
                print(f"   ✅ Switched to frame: {frames[0].get_attribute('name')}")
                time.sleep(0.5)
        except Exception as e:
            print(f"   ⚠️ Could not switch to frame: {e}")
        
        # Now detect fields with detailed debugging
        print(f"\n   🔍 Detecting fields...")
        
        # Enhanced selector
        selector = '''
            input[type="text"],
            input[type="password"],
            input[type="email"],
            input[type="number"],
            input[type="tel"],
            input[type="date"],
            input[type="time"],
            input[type="datetime-local"],
            input[type="search"],
            input[type="url"],
            input[type="checkbox"],
            input[type="radio"],
            input:not([type]),
            input[id^="value:"],
            input[name^="value:"],
            input[class*="enqsel"],
            input[class*="field"],
            input[class*="data"],
            textarea,
            select
        '''
        
        all_fields = driver.find_elements(By.CSS_SELECTOR, selector)
        print(f"   📊 Found {len(all_fields)} total elements matching selector")
        
        # Filter visible fields
        visible_fields = []
        hidden_count = 0
        button_count = 0
        
        for field in all_fields:
            try:
                if not field.is_displayed():
                    hidden_count += 1
                    continue
                
                field_type = field.get_attribute('type') or ''
                if field_type.lower() in ['button', 'submit', 'image', 'reset']:
                    button_count += 1
                    continue
                
                visible_fields.append(field)
            except:
                continue
        
        print(f"   📊 Filtered: {len(visible_fields)} visible input fields")
        print(f"   📊 Hidden: {hidden_count}, Buttons: {button_count}")
        
        # Show first 5 fields
        if visible_fields:
            print(f"\n   ✅ FOUND FIELDS! Sample details:")
            for idx, field in enumerate(visible_fields[:5], 1):
                try:
                    field_id = field.get_attribute('id') or 'no-id'
                    field_name = field.get_attribute('name') or 'no-name'
                    field_type = field.get_attribute('type') or 'text'
                    field_class = field.get_attribute('class') or 'no-class'
                    
                    print(f"      [{idx}] id='{field_id}', name='{field_name}', type='{field_type}'")
                    print(f"           class='{field_class[:60]}'")
                except Exception as e:
                    print(f"      [{idx}] Error reading field: {e}")
        else:
            print(f"   ❌ NO VISIBLE FIELDS FOUND")
            print(f"   🔍 Let's check page HTML structure...")
            
            # Check for frames/iframes
            try:
                frames = driver.find_elements(By.TAG_NAME, 'frame')
                iframes = driver.find_elements(By.TAG_NAME, 'iframe')
                print(f"   📊 Frames in popup: {len(frames)} frame, {len(iframes)} iframe")
                
                if frames or iframes:
                    print(f"   ⚠️ FOUND FRAMES! Fields might be inside them")
                    for idx, frame in enumerate(frames[:3]):
                        print(f"      Frame {idx}: {frame.get_attribute('name') or 'unnamed'}")
            except:
                pass
            
            page_source = driver.page_source[:1000]
            print(f"   📄 First 1000 chars of page source:")
            print(f"   {page_source}")
        
        return len(visible_fields)
        
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 0

def close_popup(driver):
    """Close popup with multiple strategies"""
    print(f"\n   🔒 Attempting to close popup...")
    
    try:
        # Check if we're in a popup window
        windows = driver.window_handles
        if len(windows) > 1:
            driver.close()
            driver.switch_to.window(windows[0])
            print(f"   ✅ Closed popup window")
            return True
        
        # Otherwise try frame-based close
        driver.switch_to.default_content()
        
        # Strategy 1: Try common close button selectors
        close_selectors = [
            "img[src*='close']",
            "img[alt='Close']",
            "img[src*='menu_close']",
            "a[title*='Close']",
            "input[value='Close']",
            "img[onclick*='doclose']"
        ]
        
        for selector in close_selectors:
            try:
                close_btn = driver.find_element(By.CSS_SELECTOR, selector)
                if close_btn.is_displayed():
                    close_btn.click()
                    time.sleep(0.5)
                    print(f"   ✅ Closed popup using: {selector}")
                    return True
            except:
                continue
        
        # Strategy 2: Try ESC key
        try:
            from selenium.webdriver.common.keys import Keys
            driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
            time.sleep(0.5)
            print(f"   ✅ Closed popup using ESC key")
            return True
        except:
            pass
        
        # Strategy 3: Look for close in all frames
        frames = driver.find_elements(By.TAG_NAME, 'frame')
        for frame in frames:
            try:
                driver.switch_to.frame(frame)
                for selector in close_selectors:
                    try:
                        close_btn = driver.find_element(By.CSS_SELECTOR, selector)
                        if close_btn.is_displayed():
                            close_btn.click()
                            time.sleep(0.5)
                            driver.switch_to.default_content()
                            print(f"   ✅ Closed popup from frame using: {selector}")
                            return True
                    except:
                        continue
                driver.switch_to.default_content()
            except:
                driver.switch_to.default_content()
                continue
        
        print(f"   ⚠️ Could not find close button")
        return False
        
    except Exception as e:
        print(f"   ❌ Error closing popup: {e}")
        return False

def test_page(driver, page_name):
    """Test a single page"""
    print(f"\n{'='*70}")
    print(f"TESTING: {page_name}")
    print(f"{'='*70}")
    
    try:
        # Switch to menu frame
        if not get_menu_frame(driver):
            print("   ❌ Failed to find menu frame")
            return
        
        # Find and click
        try:
            link = driver.find_element(By.XPATH, f".//a[contains(text(), '{page_name}')]")
            print(f"   ✅ Found menu link")
            link.click()
            print(f"   ✅ Clicked: {page_name}")
            time.sleep(1)
        except Exception as e:
            print(f"   ❌ Failed to find/click page: {e}")
            return
        
        # Detect fields
        field_count = wait_for_page_and_detect_fields(driver, page_name)
        
        print(f"\n   {'✅' if field_count > 0 else '❌'} RESULT: {field_count} fields found")
        
        # Close popup
        close_popup(driver)
        time.sleep(1)
        
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

def main():
    print("="*70)
    print("DEBUG RESCREEN - 3 PAGE TEST")
    print("="*70)
    print(f"\nTesting pages:")
    for idx, page in enumerate(TEST_PAGES, 1):
        print(f"  {idx}. {page}")
    
    driver = setup_driver()
    
    try:
        login(driver)
        
        # Expand menus
        if not get_menu_frame(driver):
            print("❌ Failed to find menu frame")
            return
        
        expand_all_menus(driver)
        
        # Test each page
        for page in TEST_PAGES:
            test_page(driver, page)
            input("\nPress Enter to continue to next page...")
        
        print("\n" + "="*70)
        print("DEBUG TEST COMPLETE")
        print("="*70)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        input("\nPress Enter to close browser...")
        driver.quit()

if __name__ == '__main__':
    main()
