"""
Extract T24 Menu Hierarchy with XPaths
Builds complete parent-child relationships for all menu items
Output: Excel, JSON tree, and indented text file
"""

import os
import time
import json
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from openpyxl import Workbook
from openpyxl import load_workbook

load_dotenv()

# Checkpoint file
CHECKPOINT_FILE = 'menu_hierarchy_checkpoint.json'


def load_checkpoint():
    """Load checkpoint data from file."""
    if os.path.exists(CHECKPOINT_FILE):
        try:
            with open(CHECKPOINT_FILE, 'r') as f:
                data = json.load(f)
                print(f"📂 Loaded checkpoint: {len(data.get('nodes_collected', []))} nodes, Section {data.get('current_section', 1)}")
                return data
        except:
            return {'nodes_collected': [], 'current_section': 1, 'node_counter': 0}
    return {'nodes_collected': [], 'current_section': 1, 'node_counter': 0}


def save_checkpoint(nodes_collected, current_section, node_counter):
    """Save checkpoint data to file with immediate flush."""
    try:
        with open(CHECKPOINT_FILE, 'w') as f:
            json.dump({
                'nodes_collected': nodes_collected,
                'current_section': current_section,
                'node_counter': node_counter,
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
            }, f, indent=2)
            f.flush()
    except Exception as e:
        print(f"⚠️ Failed to save checkpoint: {e}")


def clear_checkpoint():
    """Clear checkpoint file after successful completion."""
    try:
        if os.path.exists(CHECKPOINT_FILE):
            os.remove(CHECKPOINT_FILE)
            print("✅ Checkpoint cleared")
    except Exception as e:
        print(f"⚠️ Failed to clear checkpoint: {e}")


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
    """Expand all collapsible menu nodes"""
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
                except:
                    continue
            
            expanded_total += expanded_this_pass
            print(f"   Pass {pass_num + 1}: Expanded {expanded_this_pass} nodes (Total: {expanded_total})")
            
            if expanded_this_pass == 0:
                print(f"✅ All menus expanded")
                break
            
            time.sleep(0.1)
        except Exception as e:
            print(f"⚠️ Error: {e}")
            break
    
    return expanded_total

def get_element_xpath(driver, element):
    """Generate XPath for an element using position-based approach"""
    try:
        # Use JavaScript to get the XPath
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

def extract_node_info(driver, li_element, level, parent_text="ROOT", node_id=0, parent_id=-1):
    """Extract information from a single LI node - crawl actual XPath from DOM"""
    try:
        text = "Unknown"
        is_leaf = False
        unique_id = None
        xpath_position = "N/A"
        xpath_unique = None
        found_element = None  # Track which element we found
        
        # PRIORITY 1: Look for ANY <a> tag (direct OR nested) with docommand
        try:
            a_elements = li_element.find_elements(By.XPATH, ".//*[self::a]")  # All nested <a> tags
            for a_elem in a_elements:
                href = a_elem.get_attribute('href') or ''
                if 'docommand' in href:
                    # Try multiple ways to extract text for nested <a> elements
                    text = a_elem.text.strip()  # Try direct text first
                    
                    if not text:
                        # If <a> has no text, try parent <span> (ancestor, not sibling)
                        try:
                            parent_span = a_elem.find_element(By.XPATH, "ancestor::span[1]")
                            text = parent_span.text.strip()
                        except:
                            pass
                    
                    if not text:
                        # If still no text, try to extract from a nearby <span> sibling
                        try:
                            # Look for span that precedes this <a>
                            prev_span = driver.execute_script(
                                """
                                let el = arguments[0];
                                let prev = el.previousElementSibling;
                                while (prev) {
                                    if (prev.tagName === 'SPAN') return prev.textContent.trim();
                                    prev = prev.previousElementSibling;
                                }
                                return null;
                                """, a_elem
                            )
                            if prev_span:
                                text = prev_span
                        except:
                            pass
                    
                    if not text:
                        # Last resort: get text from immediate parent structure
                        text = li_element.text.strip().split('\n')[0]
                    
                    is_leaf = True
                    found_element = a_elem  # CRAWL this element
                    
                    # Extract unique identifier
                    start = href.find("docommand('") + len("docommand('")
                    end = href.find("'", start)
                    if start > 0 and end > start:
                        unique_id = href[start:end]
                    break
        except:
            pass
        
        # PRIORITY 2: If no <a> found, look for <span> with ProcessMouseClick (only direct child)
        if text == "Unknown":
            children = li_element.find_elements(By.XPATH, "./*")
            for child in children:
                if child.tag_name == 'span':
                    onclick = child.get_attribute('onclick')
                    if onclick and 'ProcessMouseClick' in onclick:
                        # Get the span's own text
                        span_text = driver.execute_script(
                            "return arguments[0].childNodes[0] ? arguments[0].childNodes[0].textContent.trim() : arguments[0].textContent.trim();",
                            child
                        )
                        if span_text:
                            text = span_text
                        else:
                            text = child.text.strip()
                        
                        found_element = child  # CRAWL this element
                        
                        # For parent nodes, extract the img alt attribute as unique identifier
                        img_alt = None
                        try:
                            img = child.find_element(By.TAG_NAME, 'img')
                            img_alt = img.get_attribute('alt')
                            if img_alt:
                                unique_id = f"PARENT:{img_alt}"
                        except:
                            pass
                        
                        # Fallback: if no img alt, create unique ID from onclick
                        if not unique_id:
                            if onclick and "ProcessMouseClick('" in onclick:
                                start = onclick.find("ProcessMouseClick('") + len("ProcessMouseClick('")
                                end = onclick.find("'", start)
                                if start > 0 and end > start:
                                    click_id = onclick[start:end]
                                    unique_id = f"PARENT:{click_id}"
                            else:
                                unique_id = f"PARENT:TEXT:{text}"
                        
                        break
        
        # ==================== CRAWL ACTUAL XPATH FROM DOM ====================
        # If we found an element, get its ACTUAL XPath from the browser
        if found_element is not None:
            try:
                xpath_unique = get_element_xpath(driver, found_element)
                if not xpath_unique:
                    xpath_unique = "N/A"
            except:
                xpath_unique = "N/A"
        # ====================================================================
        
        # Final validation: ensure we have at least basic info
        if text == "Unknown" or not unique_id:
            try:
                text = li_element.text.strip().split('\n')[0] if text == "Unknown" else text
                if not unique_id:
                    unique_id = f"NODE:{node_id}:{text[:20]}"
            except:
                pass
        
        return {
            'node_id': node_id,
            'parent_id': parent_id,
            'level': level,
            'xpath_position': xpath_position,
            'xpath_unique': xpath_unique if xpath_unique else "N/A",
            'unique_id': unique_id if unique_id else f"NODE:{node_id}",
            'text': text if text else "Unknown",
            'parent': parent_text,
            'is_leaf': is_leaf
        }
    except Exception as e:
        # Even on error, return something useful
        return {
            'node_id': node_id,
            'parent_id': parent_id,
            'level': level,
            'xpath_position': 'N/A',
            'xpath_unique': 'N/A',
            'unique_id': f"ERROR:{node_id}",
            'text': f"Error extracting node {node_id}",
            'parent': parent_text,
            'is_leaf': False
        }

def traverse_menu_tree(driver, ul_element, level=0, parent_text="ROOT", results=None, node_counter=None, parent_id=-1, current_section=1, checkpoint_callback=None):
    """Recursively traverse menu tree and collect hierarchy"""
    if results is None:
        results = []
    if node_counter is None:
        node_counter = [0]  # Use list to maintain counter across recursion
    
    try:
        # Find all direct LI children of this UL
        li_elements = ul_element.find_elements(By.XPATH, "./li")
        
        for li in li_elements:
            # Assign unique node ID
            current_node_id = node_counter[0]
            node_counter[0] += 1
            
            # Progress indicator every 100 nodes
            if current_node_id % 100 == 0:
                print(f"      Processing node {current_node_id}...")
                
                # Show sample of recent nodes every 200 nodes for monitoring
                if current_node_id > 0 and current_node_id % 200 == 0 and len(results) > 0:
                    recent_node = results[-1]
                    print(f"         Recent: L{recent_node['level']} - {recent_node['text'][:35]}")
                    print(f"         Parent chain: {recent_node['parent'][:50]}")
            
            # Extract info for this node
            node_info = extract_node_info(driver, li, level, parent_text, current_node_id, parent_id)
            if node_info:
                results.append(node_info)
                current_text = node_info['text']
                
                # Debug: show what node we're processing
                if current_node_id % 50 == 0:
                    print(f"         Level {level}: {current_text[:40]}")
                
                # Save checkpoint every 100 nodes
                if current_node_id % 100 == 0 and checkpoint_callback:
                    checkpoint_callback(results, current_section, node_counter[0])
                
                # Look for child ULs
                try:
                    child_uls = li.find_elements(By.XPATH, "./ul")
                    for child_ul in child_uls:
                        # Recurse into children with current node as parent
                        traverse_menu_tree(driver, child_ul, level + 1, current_text, results, node_counter, current_node_id, current_section, checkpoint_callback)
                except:
                    pass
    except Exception as e:
        print(f"   ⚠️ Error traversing level {level}: {str(e)[:60]}")
    
    return results

def build_full_paths(data):
    """Build full hierarchy path for each node"""
    # Create a map of node_id to node for quick lookup
    node_map = {node['node_id']: node for node in data}
    
    for node in data:
        path_parts = []
        current = node
        
        # Walk up the tree to build the full path
        while current:
            path_parts.insert(0, current['text'])
            
            # Find parent node
            if current['parent_id'] == -1:
                # Root level - add the parent name (Main Menu 1/2/3)
                path_parts.insert(0, current['parent'])
                break
            else:
                current = node_map.get(current['parent_id'])
        
        node['full_path'] = ' > '.join(path_parts)
    
    return data

def export_to_excel(data, filepath):
    """Export hierarchy to Excel"""
    wb = Workbook()
    ws = wb.active
    ws.title = 'Menu Hierarchy'
    
    # Headers - Full Path first for easy reading
    ws.append(['Full Path', 'Node ID', 'Level', 'Node Text', 'Type', 'Unique ID', 'XPath (Unique)', 'Parent Node'])
    
    # Data rows
    for row in data:
        node_type = 'Leaf (Clickable)' if row['is_leaf'] else 'Parent (Expandable)'
        ws.append([
            row.get('full_path', 'N/A'),
            row['node_id'],
            row['level'],
            row['text'],
            node_type,
            row['unique_id'] or 'N/A',
            row['xpath_unique'] or 'N/A',
            row['parent']
        ])
    
    # Auto-adjust column widths
    for column in ws.columns:
        max_length = 0
        column_letter = column[0].column_letter
        for cell in column:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass
        adjusted_width = min(max_length + 2, 100)
        ws.column_dimensions[column_letter].width = adjusted_width
    
    wb.save(filepath)
    print(f"   ✅ Excel: {filepath}")


def export_to_text(data, filepath):
    """Export hierarchy to indented text file"""
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write("T24 MENU HIERARCHY\n")
        f.write("=" * 80 + "\n\n")
        
        for node in data:
            indent = "  " * node['level']
            node_type = "📄" if node['is_leaf'] else "📁"
            
            f.write(f"{indent}{node_type} {node['text']}\n")
            
            if node['unique_id']:
                f.write(f"{indent}   ID: {node['unique_id']}\n")
            if node['xpath_unique']:
                f.write(f"{indent}   XPath: {node['xpath_unique']}\n")
            
            f.write("\n")
    
    print(f"   ✅ Text: {filepath}")


def build_tree_structure(data):
    """Build nested tree structure for JSON export using node_id relationships"""
    # Create node lookup map
    node_map = {node['node_id']: node for node in data}
    
    # Group children by parent_id
    children_by_parent = {}
    for node in data:
        parent_id = node['parent_id']
        if parent_id not in children_by_parent:
            children_by_parent[parent_id] = []
        children_by_parent[parent_id].append(node['node_id'])
    
    def build_node(node_id):
        """Recursively build tree node using node_id"""
        node_data = node_map[node_id]
        
        node = {
            'node_id': node_data['node_id'],
            'text': node_data['text'],
            'level': node_data['level'],
            'type': 'leaf' if node_data['is_leaf'] else 'parent',
            'unique_id': node_data['unique_id'],
            'xpath_unique': node_data['xpath_unique'],
            'full_path': node_data.get('full_path', '')
        }
        
        # Add children if any (using node_id lookup)
        if node_id in children_by_parent:
            node['children'] = [build_node(child_id) for child_id in children_by_parent[node_id]]
        
        return node
    
    # Start with root nodes (those with parent_id == -1)
    tree = []
    root_children = children_by_parent.get(-1, [])
    
    # Group root nodes by their parent text (Main Menu 1/2/3)
    sections = {}
    for child_id in root_children:
        node_data = node_map[child_id]
        section_name = node_data['parent']
        if section_name not in sections:
            sections[section_name] = []
        sections[section_name].append(child_id)
    
    for section_name, child_ids in sections.items():
        tree.append({
            'section': section_name,
            'children': [build_node(child_id) for child_id in child_ids]
        })
    
    return tree


def export_to_json(data, filepath):
    """Export hierarchy to JSON tree structure"""
    tree = build_tree_structure(data)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(tree, f, indent=2, ensure_ascii=False)
    
    print(f"   ✅ JSON: {filepath}")

def main():
    print("="*70)
    print("T24 MENU HIERARCHY EXTRACTOR")
    print("="*70)
    
    # Load checkpoint
    checkpoint = load_checkpoint()
    start_section = checkpoint.get('current_section', 1)
    all_nodes = checkpoint.get('nodes_collected', [])
    node_counter_start = checkpoint.get('node_counter', 0)
    
    if start_section > 1 or node_counter_start > 0:
        print(f"\n🔄 RESUMING from Section {start_section} ({len(all_nodes)} nodes already collected)\n")
    
    driver = setup_driver()
    
    try:
        # Login
        login(driver)
        
        # Switch to menu frame
        if not get_menu_frame(driver):
            print("❌ Failed to find menu frame")
            return
        
        # Expand all menus
        expanded = expand_all_menus(driver)
        print(f"\n📊 Expanded {expanded} nodes")
        
        # Re-switch to menu frame after expansion
        driver.switch_to.default_content()
        get_menu_frame(driver)
        
        # Find the main UL elements
        print("\n🔍 Extracting menu hierarchy...")
        container = driver.find_element(By.XPATH, "//div[starts-with(@id,'pane')]")
        main_uls = container.find_elements(By.XPATH, "./ul")
        
        print(f"   Found {len(main_uls)} UL elements")
        
        # Initialize node counter from checkpoint
        node_counter = [node_counter_start]
        
        # Check if we have one UL with multiple top-level LI items, or multiple ULs
        if len(main_uls) == 1:
            # Single UL with top-level sections inside it
            print("   Detected single UL structure - extracting top-level sections...")
            main_ul = main_uls[0]
            top_level_lis = main_ul.find_elements(By.XPATH, "./li")
            
            print(f"   Found {len(top_level_lis)} top-level menu sections")
            
            # Process each top-level LI as a main section
            for idx in range(start_section, len(top_level_lis) + 1):
                li = top_level_lis[idx - 1]
                
                # Extract the section name from this LI
                section_name = "Unknown Section"
                try:
                    # Try to get text from span or anchor
                    span = li.find_element(By.XPATH, "./span")
                    section_name = driver.execute_script(
                        "return arguments[0].childNodes[0] ? arguments[0].childNodes[0].textContent.trim() : arguments[0].textContent.trim();",
                        span
                    )
                except:
                    try:
                        anchor = li.find_element(By.XPATH, "./a")
                        section_name = anchor.text.strip()
                    except:
                        section_name = f"Section {idx}"
                
                print(f"\n   📂 Processing section {idx}: {section_name}")
                
                # Create checkpoint callback
                def checkpoint_callback(nodes, section, counter):
                    save_checkpoint(nodes, section, counter)
                
                # Process this LI and its children
                # First add this node itself
                current_node_id = node_counter[0]
                node_counter[0] += 1
                
                node_info = extract_node_info(driver, li, level=1, parent_text="ROOT", node_id=current_node_id, parent_id=-1)
                if node_info:
                    all_nodes.append(node_info)
                    
                    # Show the section header info
                    print(f"      Section Header: {node_info['text']}")
                    print(f"         Unique ID: {node_info['unique_id']}")
                    print(f"         Level: {node_info['level']}, Parent: {node_info['parent']}")
                    
                    # Now process children ULs under this LI
                    child_uls = li.find_elements(By.XPATH, "./ul")
                    for child_ul in child_uls:
                        traverse_menu_tree(
                            driver,
                            child_ul,
                            level=2,
                            parent_text=section_name,
                            results=all_nodes,
                            node_counter=node_counter,
                            parent_id=current_node_id,
                            current_section=idx,
                            checkpoint_callback=checkpoint_callback
                        )
                
                print(f"      Total nodes so far: {len(all_nodes)}")
                
                # Show sample hierarchy after first section for verification
                if idx == 1 and len(all_nodes) > 0:
                    print(f"\n   📋 VERIFICATION - Sample nodes from first section:")
                    print(f"   " + "="*60)
                    
                    # Build temporary full paths for first 10 nodes
                    temp_nodes = build_full_paths(all_nodes[:min(30, len(all_nodes))])
                    
                    for i, node in enumerate(temp_nodes[:15]):
                        indent = "   " + "  " * (node['level'] - 1)
                        node_type = "🍃" if node['is_leaf'] else "📁"
                        print(f"{indent}{node_type} L{node['level']}: {node['text'][:40]}")
                        if 'full_path' in node:
                            print(f"{indent}   Path: {node['full_path']}")
                    
                    if len(temp_nodes) > 15:
                        print(f"   ... and {len(temp_nodes) - 15} more nodes")
                    
                    print(f"   " + "="*60)
                    print(f"\n   ⚠️  Check the hierarchy above!")
                    print(f"   Does it show: '{section_name} > Customer Relationship > Person' ?")
                    response = input(f"   Continue with remaining sections? (y/n): ").strip().lower()
                    
                    if response != 'y':
                        print(f"\n   ⏸️  Stopping after first section. {len(all_nodes)} nodes collected.")
                        print(f"   Review the output, then:")
                        print(f"   - Delete checkpoint: del menu_hierarchy_checkpoint.json")
                        print(f"   - Run again when ready")
                        break
                
                # Save checkpoint after completing each section
                save_checkpoint(all_nodes, idx + 1, node_counter[0])
        
        else:
            # Multiple ULs - treat each as a separate section
            print("   Detected multiple UL structure - processing each UL...")
            
            for idx in range(start_section, len(main_uls) + 1):
                ul = main_uls[idx - 1]
                print(f"\n   📂 Processing UL {idx}...")
                
                # Create checkpoint callback
                def checkpoint_callback(nodes, section, counter):
                    save_checkpoint(nodes, section, counter)
                
                nodes = traverse_menu_tree(
                    driver,
                    ul,
                    level=1,
                    parent_text=f"Main Menu {idx}",
                    results=all_nodes if idx == start_section else None,
                    node_counter=node_counter,
                    parent_id=-1,
                    current_section=idx,
                    checkpoint_callback=checkpoint_callback
                )
                
                # If this is not a resume, add nodes to all_nodes
                if idx != start_section:
                    all_nodes.extend(nodes)
                
                print(f"      Collected {len(nodes)} nodes from this section")
                
                # Save checkpoint after completing each section
                save_checkpoint(all_nodes, idx + 1, node_counter[0])
        
        print(f"\n✅ Total nodes collected: {len(all_nodes)}")
        
        # Build full paths for easy interpretation
        print("\n🔗 Building full hierarchy paths...")
        all_nodes = build_full_paths(all_nodes)
        
        # Export to all 3 formats
        print("\n📤 Exporting to multiple formats...")
        export_to_excel(all_nodes, 'menu_hierarchy4.xlsx')
        export_to_text(all_nodes, 'menu_hierarchy4.txt')
        export_to_json(all_nodes, 'menu_hierarchy4.json')
        
        # Print summary
        print("\n" + "="*70)
        print("SUMMARY")
        print("="*70)
        levels = {}
        leaf_count = 0
        parent_count = 0
        
        for node in all_nodes:
            levels[node['level']] = levels.get(node['level'], 0) + 1
            if node['is_leaf']:
                leaf_count += 1
            else:
                parent_count += 1
        
        print(f"Total Nodes: {len(all_nodes)}")
        print(f"Leaf Nodes (Clickable): {leaf_count}")
        print(f"Parent Nodes (Expandable): {parent_count}")
        print(f"\nNodes by Level:")
        for level in sorted(levels.keys()):
            print(f"   Level {level}: {levels[level]} nodes")
        
        print(f"\n📄 Output Files:")
        print(f"   1. menu_hierarchy4.xlsx - Excel with all details")
        print(f"   2. menu_hierarchy4.txt - Indented tree view")
        print(f"   3. menu_hierarchy4.json - Nested JSON structure")
        print("="*70)
        
        # Clear checkpoint after successful completion
        clear_checkpoint()
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        print(f"\n💾 Progress saved in checkpoint. Run script again to resume.")
    finally:
        print("\n🔚 Closing browser...")
        driver.quit()

if __name__ == '__main__':
    main()
