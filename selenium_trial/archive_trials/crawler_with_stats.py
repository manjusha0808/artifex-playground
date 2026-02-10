"""
Fresh Crawler with Statistics Tracking
Outputs TWO Excel files:
1. uiMap_output.xlsx - All XPath details
2. page_statistics.xlsx - Page-level statistics (element counts, iframe info, etc.)

NO checkpoint logic - processes everything fresh from start.
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
XPATH_OUTPUT_FILE = 'uiMap_output.xlsx'
STATS_OUTPUT_FILE = 'page_statistics.xlsx'

# Import functions from original crawler
from crawler import (
    setup_driver, login, get_menu_frame, expand_all_menus_recursive,
    extract_xpaths_from_page
)


def initialize_xlsx_files():
    """Create fresh Excel files."""
    # XPath file
    xpath_wb = Workbook()
    xpath_ws = xpath_wb.active
    xpath_ws.title = 'XPaths'
    xpath_headers = [
        'page', 'relativeXpath', 'fullXpath', 'elementName', 'id', 'name',
        'className', 'tagName', 'type', 'placeholder', 'value', 'text'
    ]
    xpath_ws.append(xpath_headers)
    
    # Stats file
    stats_wb = Workbook()
    stats_ws = stats_wb.active
    stats_ws.title = 'Page Statistics'
    stats_headers = [
        'PageName',
        'ElementCount',
        'PopupOpened',
        'WindowCount',
        'HasIframes',
        'IframeCount',
        'ProcessingTime_ms',
        'PageURL',
        'PageTitle',
        'ErrorOccurred',
        'ErrorMessage',
        'Timestamp',
        'InputCount',
        'SelectCount',
        'TextareaCount',
        'TotalInputElements',
        'VisibleInputs',
        'HiddenInputs'
    ]
    stats_ws.append(stats_headers)
    
    print(f"📊 Created fresh files:")
    print(f"   1. {XPATH_OUTPUT_FILE}")
    print(f"   2. {STATS_OUTPUT_FILE}")
    
    return xpath_wb, xpath_ws, stats_wb, stats_ws


def analyze_page(driver, page_name: str) -> Dict:
    """
    Analyze a page and collect detailed statistics.
    Returns a dictionary with all the debug info we need.
    """
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
        'HiddenInputs': 0
    }
    
    start_time = time.time()
    
    try:
        # Get window count
        stats['WindowCount'] = len(driver.window_handles)
        stats['PopupOpened'] = stats['WindowCount'] > 1
        
        # Get URL and title
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
        
        # Count all input elements (including hidden)
        try:
            all_inputs = driver.find_elements(By.TAG_NAME, 'input')
            stats['InputCount'] = len(all_inputs)
            
            # Count visible vs hidden
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
    
    # Calculate processing time
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
        xpath_data.get('text', '')
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
        stats['HiddenInputs']
    ])


def crawl_with_stats():
    """Main crawler with statistics tracking."""
    print("="*70)
    print("FRESH CRAWLER WITH STATISTICS TRACKING")
    print("="*70)
    print(f"\nOutputs:")
    print(f"  1. {XPATH_OUTPUT_FILE} - XPath details")
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
        time.sleep(2)
        
        # Get menu items
        get_menu_frame(driver, wait=True)
        
        # Find all leaf nodes (clickable items) - use the correct XPath selector
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
                    
                    # Record error in stats
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
                        'ErrorOccurred': True,
                        'ErrorMessage': 'Could not find menu link',
                        'Timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                        'InputCount': 0,
                        'SelectCount': 0,
                        'TextareaCount': 0,
                        'TotalInputElements': 0,
                        'VisibleInputs': 0,
                        'HiddenInputs': 0
                    }
                    save_stats_row(stats_ws, stats)
                    continue
            
            main_window = driver.current_window_handle
            
            try:
                # Click link
                try:
                    link.click()
                except:
                    driver.execute_script("arguments[0].click();", link)
                
                time.sleep(0.5)  # Wait for popup
                
                # Check if popup opened
                windows = driver.window_handles
                if len(windows) > 1:
                    driver.switch_to.window(windows[-1])
                    time.sleep(0.5)  # Wait for page load
                    
                    # ANALYZE PAGE - collect statistics
                    stats = analyze_page(driver, page_name)
                    
                    # EXTRACT XPATHS
                    extracted = extract_xpaths_from_page(driver, page_name, global_seen_rows)
                    
                    # Save XPath rows
                    for xpath_data in extracted:
                        save_xpath_row(xpath_ws, xpath_data)
                        xpath_count += 1
                    
                    # Update stats with actual extraction count
                    stats['ElementCount'] = len(extracted)
                    
                    print(f"    ✅ {len(extracted)} elements | Inputs:{stats['InputCount']} Selects:{stats['SelectCount']} Textareas:{stats['TextareaCount']}")
                    if stats['HasIframes']:
                        print(f"       ⚠️ Has {stats['IframeCount']} iframe(s) - fields might be inside!")
                    
                    # Save stats row
                    save_stats_row(stats_ws, stats)
                    
                    # Close popup
                    driver.close()
                    driver.switch_to.window(main_window)
                else:
                    print(f"    ⚠️ No popup opened")
                    
                    # Record in stats
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
                        'ErrorOccurred': True,
                        'ErrorMessage': 'Popup did not open',
                        'Timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                        'InputCount': 0,
                        'SelectCount': 0,
                        'TextareaCount': 0,
                        'TotalInputElements': 0,
                        'VisibleInputs': 0,
                        'HiddenInputs': 0
                    }
                    save_stats_row(stats_ws, stats)
                
                # Save files every 50 items
                if (i + 1) % 50 == 0:
                    xpath_wb.save(XPATH_OUTPUT_FILE)
                    stats_wb.save(STATS_OUTPUT_FILE)
                    print(f"    💾 Checkpoint: {xpath_count} XPaths, {i+1} pages")
                
            except Exception as e:
                print(f"    ❌ Error: {str(e)[:100]}")
                
                # Record error in stats
                stats = {
                    'PageName': page_name,
                    'ElementCount': 0,
                    'PopupOpened': False,
                    'WindowCount': 0,
                    'HasIframes': False,
                    'IframeCount': 0,
                    'ProcessingTime_ms': 0,
                    'PageURL': '',
                    'PageTitle': '',
                    'ErrorOccurred': True,
                    'ErrorMessage': str(e)[:200],
                    'Timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'InputCount': 0,
                    'SelectCount': 0,
                    'TextareaCount': 0,
                    'TotalInputElements': 0,
                    'VisibleInputs': 0,
                    'HiddenInputs': 0
                }
                save_stats_row(stats_ws, stats)
                
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
    crawl_with_stats()
