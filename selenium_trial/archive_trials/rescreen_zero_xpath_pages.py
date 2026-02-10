"""
Rescreen Zero XPath Pages with Enhanced Detection
Handles slow-loading pages and alternative field patterns like id="value:1:1:1"
"""

import os
import time
import pandas as pd
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from openpyxl import Workbook

load_dotenv()

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
    for frame in frames:
        frame_name = frame.get_attribute('name') or ''
        if 'menu' in frame_name.lower():
            driver.switch_to.frame(frame)
            return True
    return False

def expand_all_menus(driver):
    """Expand all menu items so pages are visible"""
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
        except Exception as e:
            break
    
    return expanded_total

def wait_for_page_load(driver, timeout=8):
    """Wait for page to fully load - handles slow pages"""
    try:
        # Store main window
        main_window = driver.current_window_handle
        
        # Wait for popup window to open
        time.sleep(1)
        windows = driver.window_handles
        
        if len(windows) > 1:
            # Switch to popup window
            driver.switch_to.window(windows[-1])
            
            # Wait for page to complete
            WebDriverWait(driver, timeout).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
            time.sleep(2)
            
            # Try switching to first frame if exists (best effort, may fail but fields still accessible)
            try:
                frames = driver.find_elements(By.TAG_NAME, 'frame')
                if frames:
                    driver.switch_to.frame(frames[0])
                    time.sleep(0.5)
            except:
                pass  # Fields are accessible even without switching
            
            return True
        
        return False
    except:
        return False

def close_popup(driver):
    """Close popup window"""
    try:
        windows = driver.window_handles
        if len(windows) > 1:
            driver.close()
            driver.switch_to.window(windows[0])
            return True
        return False
    except:
        return False

def enhanced_field_detection(driver):
    """
    Enhanced field detection that catches:
    1. Standard fields (input[type="text"], textarea, select)
    2. Alternative patterns (id="value:1:1:1", name="value:1:1:1")
    3. Fields with class containing "enqsel", "field", "data"
    """
    
    # Comprehensive selector including alternative patterns
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
    
    try:
        fields = driver.find_elements(By.CSS_SELECTOR, selector)
        
        # Filter out hidden fields and buttons
        visible_fields = []
        for field in fields:
            try:
                # Skip if not displayed or is a button/submit
                if not field.is_displayed():
                    continue
                
                field_type = field.get_attribute('type') or ''
                if field_type.lower() in ['button', 'submit', 'image', 'reset']:
                    continue
                
                visible_fields.append(field)
            except:
                continue
        
        return visible_fields
    except:
        return []

def extract_field_details(field):
    """Extract detailed information from a field element"""
    try:
        return {
            'tagName': field.tag_name,
            'type': field.get_attribute('type') or 'text',
            'id': field.get_attribute('id') or '',
            'name': field.get_attribute('name') or '',
            'className': field.get_attribute('class') or '',
            'value': field.get_attribute('value') or '',
            'placeholder': field.get_attribute('placeholder') or ''
        }
    except:
        return None

def generate_xpath(driver, element):
    """Generate XPath for an element"""
    try:
        xpath = driver.execute_script("""
            function getXPath(element) {
                if (element.id !== '')
                    return '//*[@id="' + element.id + '"]';
                if (element === document.body)
                    return '/html/body';
                
                var ix = 0;
                var siblings = element.parentNode.childNodes;
                for (var i = 0; i < siblings.length; i++) {
                    var sibling = siblings[i];
                    if (sibling === element)
                        return getXPath(element.parentNode) + '/' + element.tagName.toLowerCase() + '[' + (ix + 1) + ']';
                    if (sibling.nodeType === 1 && sibling.tagName === element.tagName)
                        ix++;
                }
            }
            return getXPath(arguments[0]);
        """, element)
        return xpath
    except:
        return "N/A"

def rescreen_page(driver, page_name):
    """Rescreen a single page with enhanced detection"""
    result = {
        'page_name': page_name,
        'status': 'Unknown',
        'field_count': 0,
        'fields_found': [],
        'notes': ''
    }
    
    try:
        # Click the menu item
        driver.switch_to.default_content()
        
        # Switch to menu frame
        if not get_menu_frame(driver):
            result['status'] = 'Error'
            result['notes'] = 'Could not find menu frame'
            return result
        
        # Find and click the page
        try:
            # Try docommand link
            link = driver.find_element(By.XPATH, f".//a[contains(text(), '{page_name}')]")
            link.click()
            print(f"   📄 Clicked: {page_name}")
            
            # CRITICAL: Wait and switch to the display frame where form fields appear
            time.sleep(1)
            
        except:
            result['status'] = 'Page Not Found'
            result['notes'] = 'Could not find menu item'
            return result
        
        # Wait for page to load (extended timeout for slow pages)
        if not wait_for_page_load(driver, timeout=8):
            result['status'] = 'Load Timeout'
            result['notes'] = 'Page took too long to load'
            return result
        
        # Detect fields with enhanced logic
        fields = enhanced_field_detection(driver)
        
        if len(fields) == 0:
            result['status'] = 'No Fields (Genuine)'
            result['notes'] = 'Page has no input fields'
        else:
            result['status'] = 'Fields Found'
            result['field_count'] = len(fields)
            
            # Extract details for first 10 fields (avoid overwhelming output)
            for field in fields[:10]:
                details = extract_field_details(field)
                if details:
                    xpath = generate_xpath(driver, field)
                    result['fields_found'].append({
                        'xpath': xpath,
                        'id': details['id'],
                        'name': details['name'],
                        'type': details['type'],
                        'tag': details['tagName']
                    })
            
            if len(fields) > 10:
                result['notes'] = f'Showing 10 of {len(fields)} fields'
        
        # Close the popup before moving to next page
        close_popup(driver)
        
    except Exception as e:
        result['status'] = 'Error'
        result['notes'] = str(e)[:100]
        
        # Try to close popup even on error
        try:
            close_popup(driver)
        except:
            pass
    
    return result

def export_results(results, filepath):
    """Export results to Excel"""
    wb = Workbook()
    ws = wb.active
    ws.title = 'Rescreen Results'
    
    # Headers
    ws.append(['Page Name', 'Status', 'Field Count', 'Sample Field 1', 'Sample Field 2', 'Notes'])
    
    for result in results:
        fields = result['fields_found']
        sample1 = f"{fields[0]['id'] or fields[0]['name']} ({fields[0]['type']})" if len(fields) > 0 else ''
        sample2 = f"{fields[1]['id'] or fields[1]['name']} ({fields[1]['type']})" if len(fields) > 1 else ''
        
        ws.append([
            result['page_name'],
            result['status'],
            result['field_count'],
            sample1,
            sample2,
            result['notes']
        ])
    
    # Auto-adjust columns
    for column in ws.columns:
        max_length = 0
        column_letter = column[0].column_letter
        for cell in column:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass
        adjusted_width = min(max_length + 2, 80)
        ws.column_dimensions[column_letter].width = adjusted_width
    
    wb.save(filepath)
    print(f"\n✅ Results saved to: {filepath}")

def main():
    print("="*70)
    print("RESCREEN ZERO XPATH PAGES")
    print("="*70)
    
    # Read zero xpath pages
    try:
        df = pd.read_excel('zero_xpath_pages.xlsx')
        if 'pageName' in df.columns:
            page_list = df['pageName'].tolist()
        elif 'page' in df.columns:
            page_list = df['page'].tolist()
        elif 'Page Name' in df.columns:
            page_list = df['Page Name'].tolist()
        else:
            page_list = df.iloc[:, 0].tolist()
        
        print(f"\n📋 Found {len(page_list)} pages to rescreen")
    except Exception as e:
        print(f"❌ Error reading zero_xpath_pages.xlsx: {e}")
        return
    
    driver = setup_driver()
    results = []
    
    try:
        login(driver)
        
        # Expand all menus first
        if not get_menu_frame(driver):
            print("❌ Failed to find menu frame")
            return
        
        expand_all_menus(driver)
        
        print("\n🔍 Starting rescreen...\n")
        
        for idx, page_name in enumerate(page_list, 1):
            print(f"[{idx}/{len(page_list)}] Processing: {page_name}")
            
            result = rescreen_page(driver, page_name)
            results.append(result)
            
            status_icon = "✅" if result['field_count'] > 0 else "⚪" if result['status'] == 'No Fields (Genuine)' else "❌"
            print(f"   {status_icon} {result['status']} - {result['field_count']} fields")
            
            # Small delay between pages
            time.sleep(0.5)
        
        # Export results
        export_results(results, 'rescreen_results.xlsx')
        
        # Print summary
        print("\n" + "="*70)
        print("SUMMARY")
        print("="*70)
        
        fields_found = sum(1 for r in results if r['field_count'] > 0)
        genuine_empty = sum(1 for r in results if r['status'] == 'No Fields (Genuine)')
        errors = sum(1 for r in results if r['status'] in ['Error', 'Load Timeout', 'Page Not Found'])
        
        print(f"Total Pages Rescreened: {len(results)}")
        print(f"Fields Found (Previously Missed): {fields_found}")
        print(f"Genuinely Empty Pages: {genuine_empty}")
        print(f"Errors/Timeouts: {errors}")
        print("="*70)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\n🔚 Closing browser...")
        driver.quit()

if __name__ == '__main__':
    main()
