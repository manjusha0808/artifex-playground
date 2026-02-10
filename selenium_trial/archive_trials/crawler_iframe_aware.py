"""
Iframe-Aware Crawler with Statistics Tracking
Outputs TWO Excel files:
1. uiMap_output.xlsx - All XPath details (including fields from iframes)
2. page_statistics.xlsx - Page-level statistics

Key Enhancement: Extracts XPaths from MAIN DOCUMENT + ALL IFRAMES
"""

import time
import os
from typing import List, Dict, Set
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
import openpyxl
from openpyxl import Workbook

# Load environment variables
load_dotenv()

# Output files
XPATH_OUTPUT_FILE = 'uiMap_output_with_iframes.xlsx'
STATS_OUTPUT_FILE = 'page_statistics_with_iframes.xlsx'

# Import functions from original crawler
from crawler import setup_driver, login, get_menu_frame, expand_all_menus_recursive


def extract_xpaths_with_iframes(driver, page_name: str, seen_rows: Set) -> List[Dict]:
    """
    Extract XPaths from main document AND all iframes.
    Returns list of dictionaries with XPath data.
    """
    all_extracted = []
    
    # CSS selector for input fields
    selector = '''
        input[type="text"], input[type="password"], input[type="email"],
        input[type="number"], input[type="tel"], input[type="date"],
        input[type="time"], input[type="datetime-local"], input[type="search"],
        input[type="url"], input[type="checkbox"], input[type="radio"],
        input:not([type]), textarea, select
    '''
    
    def extract_from_context(context_name="main"):
        """Extract fields from current context (main or iframe)."""
        extracted = []
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            
            for elem in elements:
                try:
                    # Get attributes
                    elem_id = elem.get_attribute('id') or ''
                    elem_name = elem.get_attribute('name') or ''
                    elem_class = elem.get_attribute('class') or ''
                    elem_type = elem.get_attribute('type') or ''
                    elem_placeholder = elem.get_attribute('placeholder') or ''
                    elem_value = elem.get_attribute('value') or ''
                    elem_text = elem.text.strip() or ''
                    tag_name = elem.tag_name.lower()
                    
                    # Generate element name
                    element_name = elem_id or elem_name or elem_placeholder or f"{tag_name}_{len(extracted)}"
                    
                    # Generate XPaths
                    relative_xpath = ''
                    if elem_id:
                        relative_xpath = f"//{tag_name}[@id='{elem_id}']"
                    elif elem_name:
                        relative_xpath = f"//{tag_name}[@name='{elem_name}']"
                    elif elem_placeholder:
                        relative_xpath = f"//{tag_name}[@placeholder='{elem_placeholder}']"
                    else:
                        # Fallback to index-based
                        relative_xpath = f"(//{tag_name})[{len(extracted)+1}]"
                    
                    # Full XPath (using Selenium)
                    full_xpath = ''
                    try:
                        full_xpath = driver.execute_script(
                            "function getXPath(element) {"
                            "  if (element.id !== '') return '//*[@id=\"' + element.id + '\"]';"
                            "  if (element === document.body) return '/html/body';"
                            "  var ix = 0;"
                            "  var siblings = element.parentNode.childNodes;"
                            "  for (var i = 0; i < siblings.length; i++) {"
                            "    var sibling = siblings[i];"
                            "    if (sibling === element) return getXPath(element.parentNode) + '/' + element.tagName.toLowerCase() + '[' + (ix + 1) + ']';"
                            "    if (sibling.nodeType === 1 && sibling.tagName === element.tagName) ix++;"
                            "  }"
                            "}"
                            "return getXPath(arguments[0]);", elem
                        )
                    except:
                        full_xpath = relative_xpath
                    
                    # Create unique key
                    row_key = (page_name, relative_xpath, element_name, elem_id, elem_name, 
                              elem_class, tag_name, elem_type)
                    
                    if row_key not in seen_rows:
                        seen_rows.add(row_key)
                        extracted.append({
                            'page': page_name,
                            'relativeXpath': relative_xpath,
                            'fullXpath': full_xpath,
                            'elementName': element_name,
                            'id': elem_id,
                            'name': elem_name,
                            'className': elem_class,
                            'tagName': tag_name,
                            'type': elem_type,
                            'placeholder': elem_placeholder,
                            'value': elem_value,
                            'text': elem_text,
                            'context': context_name
                        })
                except Exception as e:
                    continue
        except Exception as e:
            pass
        
        return extracted
    
    # 1. Extract from main document
    main_extracted = extract_from_context("main")
    all_extracted.extend(main_extracted)
    
    # 2. Find and process all iframes
    try:
        iframes = driver.find_elements(By.TAG_NAME, 'iframe')
        
        for idx, iframe in enumerate(iframes):
            try:
                # Switch to iframe
                driver.switch_to.frame(iframe)
                
                # Extract from iframe
                iframe_extracted = extract_from_context(f"iframe_{idx}")
                all_extracted.extend(iframe_extracted)
                
                # Switch back to main document
                driver.switch_to.default_content()
            except Exception as e:
                # If switch fails, make sure we're back in main context
                try:
                    driver.switch_to.default_content()
                except:
                    pass
    except Exception as e:
        pass
    
    return all_extracted


def initialize_xlsx_files():
    """Create fresh Excel files."""
    # XPath file
    xpath_wb = Workbook()
    xpath_ws = xpath_wb.active
    xpath_ws.title = 'XPaths'
    xpath_headers = [
        'page', 'relativeXpath', 'fullXpath', 'elementName', 'id', 'name',
        'className', 'tagName', 'type', 'placeholder', 'value', 'text', 'context'
    ]
    xpath_ws.append(xpath_headers)
    
    # Stats file
    stats_wb = Workbook()
    stats_ws = stats_wb.active
    stats_ws.title = 'Page Statistics'
    stats_headers = [
        'PageName', 'ElementCount', 'PopupOpened', 'WindowCount', 'HasIframes',
        'IframeCount', 'ProcessingTime_ms', 'PageURL', 'PageTitle', 'ErrorOccurred',
        'ErrorMessage', 'Timestamp', 'InputCount', 'SelectCount', 'TextareaCount',
        'TotalInputElements', 'VisibleInputs', 'HiddenInputs', 'ExtractedFromMain',
        'ExtractedFromIframes'
    ]
    stats_ws.append(stats_headers)
    
    print(f"📊 Created fresh files:")
    print(f"   1. {XPATH_OUTPUT_FILE}")
    print(f"   2. {STATS_OUTPUT_FILE}")
    
    return xpath_wb, xpath_ws, stats_wb, stats_ws


def analyze_page(driver, page_name: str) -> Dict:
    """Analyze a page and collect detailed statistics."""
    stats = {
        'PageName': page_name,
        'ElementCount': 0,
        'PopupOpened': False,
        'WindowCount': 1,
        'HasIframes': False,
        'IframeCount': 0,
        'ProcessingTime_ms': 0,
        'PageURL': '',
        'PageTitle': '',
        'ErrorOccurred': False,
        'ErrorMessage': '',
        'Timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'InputCount': 0,
        'SelectCount': 0,
        'TextareaCount': 0,
        'TotalInputElements': 0,
        'VisibleInputs': 0,
        'HiddenInputs': 0,
        'ExtractedFromMain': 0,
        'ExtractedFromIframes': 0
    }
    
    start_time = time.time()
    
    try:
        stats['WindowCount'] = len(driver.window_handles)
        stats['PopupOpened'] = stats['WindowCount'] > 1
        
        try:
            stats['PageURL'] = driver.current_url
            stats['PageTitle'] = driver.title
        except:
            pass
        
        # Check for iframes
        try:
            iframes = driver.find_elements(By.TAG_NAME, 'iframe')
            stats['IframeCount'] = len(iframes)
            stats['HasIframes'] = len(iframes) > 0
        except:
            pass
        
        # Count inputs
        try:
            all_inputs = driver.find_elements(By.TAG_NAME, 'input')
            stats['InputCount'] = len(all_inputs)
            visible = sum(1 for inp in all_inputs if inp.is_displayed())
            stats['VisibleInputs'] = visible
            stats['HiddenInputs'] = len(all_inputs) - visible
        except:
            pass
        
        # Count selects
        try:
            selects = driver.find_elements(By.TAG_NAME, 'select')
            stats['SelectCount'] = len(selects)
        except:
            pass
        
        # Count textareas
        try:
            textareas = driver.find_elements(By.TAG_NAME, 'textarea')
            stats['TextareaCount'] = len(textareas)
        except:
            pass
        
        stats['TotalInputElements'] = stats['InputCount'] + stats['SelectCount'] + stats['TextareaCount']
        
    except Exception as e:
        stats['ErrorOccurred'] = True
        stats['ErrorMessage'] = str(e)[:200]
    
    stats['ProcessingTime_ms'] = int((time.time() - start_time) * 1000)
    
    return stats


def save_xpath_row(ws, xpath_data: Dict):
    """Save a single XPath row."""
    ws.append([
        xpath_data.get('page', ''),
        xpath_data.get('relativeXpath', ''),
        xpath_data.get('fullXpath', ''),
        xpath_data.get('elementName', ''),
        xpath_data.get('id', ''),
        xpath_data.get('name', ''),
        xpath_data.get('className', ''),
        xpath_data.get('tagName', ''),
        xpath_data.get('type', ''),
        xpath_data.get('placeholder', ''),
        xpath_data.get('value', ''),
        xpath_data.get('text', ''),
        xpath_data.get('context', 'main')
    ])


def save_stats_row(ws, stats: Dict):
    """Save a single stats row."""
    ws.append([
        stats['PageName'],
        stats['ElementCount'],
        'Yes' if stats['PopupOpened'] else 'No',
        stats['WindowCount'],
        'Yes' if stats['HasIframes'] else 'No',
        stats['IframeCount'],
        stats['ProcessingTime_ms'],
        stats['PageURL'],
        stats['PageTitle'],
        'Yes' if stats['ErrorOccurred'] else 'No',
        stats['ErrorMessage'],
        stats['Timestamp'],
        stats['InputCount'],
        stats['SelectCount'],
        stats['TextareaCount'],
        stats['TotalInputElements'],
        stats['VisibleInputs'],
        stats['HiddenInputs'],
        stats['ExtractedFromMain'],
        stats['ExtractedFromIframes']
    ])


def crawl_with_iframe_support():
    """Main crawler with iframe support and statistics tracking."""
    print("="*70)
    print("IFRAME-AWARE CRAWLER WITH STATISTICS TRACKING")
    print("="*70)
    print(f"\nOutputs:")
    print(f"  1. {XPATH_OUTPUT_FILE} - XPath details (main + iframes)")
    print(f"  2. {STATS_OUTPUT_FILE} - Page statistics")
    print()
    
    # Initialize fresh files
    xpath_wb, xpath_ws, stats_wb, stats_ws = initialize_xlsx_files()
    
    # Track what we've seen to avoid duplicates
    global_seen_rows = set()
    xpath_count = 0
    
    # Setup driver
    driver = setup_driver()
    
    try:
        # Login
        print("\n🔐 Logging in...")
        url = os.getenv('T24_URL')
        username = os.getenv('T24_USERNAME')
        password = os.getenv('T24_PASSWORD')
        login(driver, url, username, password)
        print("✅ Login successful")
        
        # Expand menu
        print("\n🔧 Expanding menu...")
        expand_all_menus_recursive(driver)
        time.sleep(1)
        
        # Get menu items
        get_menu_frame(driver, wait=True)
        
        # Find all leaf nodes
        all_leaves = driver.find_elements(By.XPATH, ".//li[.//a[starts-with(@href,'javascript:docommand(')]]")
        
        print(f"\n📋 Building menu item list...")
        items_to_process = []
        for leaf in all_leaves:
            if leaf.is_displayed():
                try:
                    link = leaf.find_element(By.XPATH, ".//a")
                    if link.is_displayed():
                        text = link.text.strip() or "Unknown"
                        items_to_process.append(text)
                except:
                    pass
        
        total = len(items_to_process)
        print(f"🎯 Found {total} pages to process\n")
        
        # Process each page
        for i in range(total):
            page_name = items_to_process[i]
            
            print(f"[{i+1}/{total}] 🖱️ {page_name}")
            
            # Re-find link
            driver.switch_to.default_content()
            get_menu_frame(driver)
            
            try:
                link = driver.find_element(By.XPATH, f".//a[starts-with(@href,'javascript:docommand(') and text()='{page_name}']")
            except:
                try:
                    link = driver.find_element(By.XPATH, f".//a[starts-with(@href,'javascript:docommand(') and contains(text(),'{page_name[:20]}')]")
                except:
                    print(f"    ⚠️ Could not find link")
                    continue
            
            main_window = driver.current_window_handle
            
            try:
                # Click link
                try:
                    link.click()
                except:
                    driver.execute_script("arguments[0].click();", link)
                
                time.sleep(0.3)
                
                # Check if popup opened
                windows = driver.window_handles
                if len(windows) > 1:
                    driver.switch_to.window(windows[-1])
                    time.sleep(0.3)
                    
                    # ANALYZE PAGE
                    stats = analyze_page(driver, page_name)
                    
                    # EXTRACT XPATHS (with iframe support)
                    extracted = extract_xpaths_with_iframes(driver, page_name, global_seen_rows)
                    
                    # Count context breakdown
                    main_count = sum(1 for x in extracted if x.get('context') == 'main')
                    iframe_count = len(extracted) - main_count
                    
                    stats['ExtractedFromMain'] = main_count
                    stats['ExtractedFromIframes'] = iframe_count
                    
                    # Save XPath rows
                    for xpath_data in extracted:
                        save_xpath_row(xpath_ws, xpath_data)
                        xpath_count += 1
                    
                    stats['ElementCount'] = len(extracted)
                    
                    print(f"    ✅ {len(extracted)} elements (Main:{main_count} Iframes:{iframe_count}) | Total:{stats['TotalInputElements']}")
                    if stats['HasIframes']:
                        print(f"       📦 {stats['IframeCount']} iframe(s) processed")
                    
                    # Save stats row
                    save_stats_row(stats_ws, stats)
                    
                    # Close popup
                    driver.close()
                    driver.switch_to.window(main_window)
                else:
                    print(f"    ⚠️ No popup opened")
                
                # Save files every 50 items
                if (i + 1) % 50 == 0:
                    xpath_wb.save(XPATH_OUTPUT_FILE)
                    stats_wb.save(STATS_OUTPUT_FILE)
                    print(f"    💾 Checkpoint: {xpath_count} XPaths, {i+1} pages")
                
            except Exception as e:
                print(f"    ❌ Error: {str(e)[:100]}")
                try:
                    driver.switch_to.window(main_window)
                except:
                    pass
        
        # Final save
        print(f"\n✨ Complete!")
        print(f"   XPaths extracted: {xpath_count}")
        print(f"   Pages processed: {total}")
        
        xpath_wb.save(XPATH_OUTPUT_FILE)
        stats_wb.save(STATS_OUTPUT_FILE)
        
        print(f"\n📊 Output files:")
        print(f"   1. {XPATH_OUTPUT_FILE} - {xpath_count} XPath records")
        print(f"   2. {STATS_OUTPUT_FILE} - {total} page statistics")
        
    except KeyboardInterrupt:
        print("\n\n⏸️ Interrupted - Saving progress...")
        xpath_wb.save(XPATH_OUTPUT_FILE)
        stats_wb.save(STATS_OUTPUT_FILE)
        print("✅ Progress saved")
        
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
    crawl_with_iframe_support()
