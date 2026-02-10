"""
Check if 0-element pages have iframes that weren't inspected.
The crawler might be missing fields inside iframes.
"""
import json
from crawler import setup_driver, login, get_menu_frame, expand_all_menus_recursive
from selenium.webdriver.common.by import By
import time
import os
from dotenv import load_dotenv

load_dotenv()

T24_URL = os.getenv('T24_URL')
T24_USERNAME = os.getenv('T24_USERNAME')
T24_PASSWORD = os.getenv('T24_PASSWORD')

def check_iframe_fields():
    # Load some 0-element pages
    with open('items_to_rescreen.json', 'r') as f:
        zero_pages = json.load(f)['items_to_rescreen'][:10]
    
    print("="*70)
    print("IFRAME CHECK - Do 0-element pages have iframes?")
    print("="*70)
    
    driver = setup_driver()
    
    try:
        login(driver, T24_URL, T24_USERNAME, T24_PASSWORD)
        expand_all_menus_recursive(driver)
        
        menu_frame = get_menu_frame(driver, wait=True)
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
        
        iframe_count = 0
        pages_with_iframe_fields = []
        
        for page_name in zero_pages:
            if page_name not in menu_map:
                continue
            
            idx, _ = menu_map[page_name]
            
            menu_frame = get_menu_frame(driver, wait=False)
            all_links = driver.find_elements(By.TAG_NAME, 'a')
            
            if idx < len(all_links):
                try:
                    all_links[idx].click()
                    time.sleep(2)
                    
                    if len(driver.window_handles) > 1:
                        driver.switch_to.window(driver.window_handles[-1])
                    
                    # Check for iframes
                    iframes = driver.find_elements(By.TAG_NAME, 'iframe')
                    
                    if iframes:
                        iframe_count += 1
                        print(f"\n📦 {page_name}")
                        print(f"   Found {len(iframes)} iframe(s)")
                        
                        # Check each iframe
                        for i, iframe in enumerate(iframes, 1):
                            try:
                                driver.switch_to.frame(iframe)
                                
                                inputs = driver.find_elements(By.TAG_NAME, 'input')
                                selects = driver.find_elements(By.TAG_NAME, 'select')
                                textareas = driver.find_elements(By.TAG_NAME, 'textarea')
                                
                                total = len(inputs) + len(selects) + len(textareas)
                                
                                if total > 0:
                                    print(f"   Iframe {i}: {total} fields found!")
                                    pages_with_iframe_fields.append(page_name)
                                
                                driver.switch_to.default_content()
                            except:
                                driver.switch_to.default_content()
                    
                    # Close popup
                    if len(driver.window_handles) > 1:
                        driver.close()
                        driver.switch_to.window(driver.window_handles[0])
                    
                except Exception as e:
                    pass
        
        print(f"\n{'='*70}")
        print(f"RESULTS:")
        print(f"  Checked: {len(zero_pages)} pages")
        print(f"  Pages with iframes: {iframe_count}")
        print(f"  Pages with fields in iframes: {len(pages_with_iframe_fields)}")
        
        if pages_with_iframe_fields:
            print(f"\n⚠️ FINDING: These pages have fields inside iframes!")
            for page in pages_with_iframe_fields:
                print(f"     - {page}")
            print(f"\n💡 SOLUTION: Crawler needs to check inside iframes too")
        
    finally:
        driver.quit()

if __name__ == "__main__":
    check_iframe_fields()
