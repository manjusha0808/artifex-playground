import os
import csv
from typing import List, Dict

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options


TRIAL_PAGES = {
    "Input Prospect (Person)",
    "Input Person records (Other than Prospect)",
    "Individual Customer",
    "Corporate Customer",
    "Create Prospect",
    "Open Current Account",
    "Open Savings Account",
    "Input Prospect (Entity)",
    "Input Entity records (Other than Prospect)",
}


def traverse_menu(driver) -> List[Dict]:
    """Traverse the BrowserWeb menu and return leaf pages for TRIAL_PAGES.

    Each returned dict contains:
    - page_name: leaf caption text
    - hierarchy: parent > child > leaf path
    - locator: an XPath locator string for the <a> element

    We store an XPath instead of the WebElement itself so that we can
    re-locate the element later if the DOM changes.
    """
    leaves: List[Dict] = []

    root_ul = driver.find_element(By.CSS_SELECTOR, "ul.menuMargin")

    def dfs_ul(ul_element, ancestors: List[str]):
        li_nodes = ul_element.find_elements(By.XPATH, "./li")
        for li in li_nodes:
            classes = li.get_attribute("class") or ""

            # Expandable node
            if "clsHasKids" in classes.split():
                try:
                    span = li.find_element(By.XPATH, "./span")
                except Exception:
                    span = None

                if span is not None:
                    label_text = span.text.strip()

                    # Click to expand. We don't try to track expanded state;
                    # extra clicks should be harmless as BrowserWeb toggles.
                    try:
                        driver.execute_script("arguments[0].scrollIntoView(true);", span)
                    except Exception:
                        pass
                    try:
                        span.click()
                    except Exception:
                        pass

                    new_ancestors = ancestors + [label_text]

                    # Recurse into any child <ul>
                    child_uls = li.find_elements(By.XPATH, "./ul")
                    for child_ul in child_uls:
                        dfs_ul(child_ul, new_ancestors)

            # Leaf pages: li with direct <a> children
            links = li.find_elements(By.XPATH, "./a")
            for a in links:
                page_name = a.text.strip()
                hierarchy = " > ".join(ancestors + [page_name])
                if page_name in TRIAL_PAGES:
                    # Build a relative XPath that can be re-used later
                    locator = _build_link_xpath(a)
                    leaves.append({
                        "page_name": page_name,
                        "hierarchy": hierarchy,
                        "link_xpath": locator,
                    })

    dfs_ul(root_ul, [])
    return leaves


def _build_link_xpath(element) -> str:
    """Build a stable XPath for the given <a> element based on its text.

    This assumes the link text is unique enough within the menu. If needed,
    this can be extended to include more context (e.g. ancestors).
    """
    text = element.text.strip()
    # Escape single quotes in text for XPath literal
    # Simple case: assume no single quote in text; if there is, XPath match may fail
    if "'" in text:
        # Fallback to contains() match to avoid complex escaping
        xpath = f"//ul[@class='menuMargin']//a[contains(normalize-space(text()), \"{text}\")]"
    else:
        xpath = f"//ul[@class='menuMargin']//a[normalize-space(text()) = '{text}']"
    return xpath


def open_page_in_new_tab(driver, leaf_info: Dict, wait: WebDriverWait):
    original_handle = driver.current_window_handle
    existing_handles = set(driver.window_handles)

    # Locate the <a> element again using its XPath
    a = driver.find_element(By.XPATH, leaf_info["link_xpath"])

    try:
        driver.execute_script("arguments[0].scrollIntoView(true);", a)
    except Exception:
        pass

    a.click()

    # Wait for a new tab to appear
    wait.until(lambda d: len(d.window_handles) > len(existing_handles))

    new_handles = set(driver.window_handles) - existing_handles
    new_handle = new_handles.pop()
    driver.switch_to.window(new_handle)

    return original_handle, new_handle


def form_present(driver) -> bool:
    """Heuristic to determine if the form (with Validate button) is present."""
    try:
        driver.find_element(By.XPATH, "//img[contains(@src, 'txnvalidate.gif')]")
        return True
    except Exception:
        return False


def switch_to_form_context(driver, wait: WebDriverWait):
    """Switch into the correct context (main document or iframe) containing the form.

    Strategy:
    - Try main document first.
    - If not found, iterate through iframes and pick the first that contains
      the Validate image.
    """
    driver.switch_to.default_content()
    if form_present(driver):
        return

    iframes = driver.find_elements(By.TAG_NAME, "iframe")
    for iframe in iframes:
        driver.switch_to.default_content()
        try:
            driver.switch_to.frame(iframe)
        except Exception:
            continue
        if form_present(driver):
            return

    # Fallback: stay in default content
    driver.switch_to.default_content()


def click_validate_and_wait(driver, wait: WebDriverWait):
    """Click the Validate button and wait for any field errors or error text."""
    validate_img = driver.find_element(By.XPATH, "//img[contains(@src, 'txnvalidate.gif')]")

    try:
        driver.execute_script("arguments[0].scrollIntoView(true);", validate_img)
    except Exception:
        pass

    validate_img.click()

    # Wait for either an error row or any fielderror="Y" element
    wait.until(lambda d: d.find_elements(By.XPATH, "//*[@fielderror='Y']") or
               d.find_elements(By.CSS_SELECTOR, "td.errorText span.captionError"))


def collect_mandatory_fields(driver) -> List[Dict]:
    """Collect all fields marked with fielderror="Y" and return their metadata."""
    elems = driver.find_elements(
        By.XPATH,
        "//input[@fielderror='Y'] | //select[@fielderror='Y'] | //textarea[@fielderror='Y']",
    )
    result: List[Dict] = []

    for el in elems:
        tag = (el.tag_name or "").lower()
        type_attr = (el.get_attribute("type") or "").lower()
        id_attr = el.get_attribute("id") or ""
        name_attr = el.get_attribute("name") or ""

        # Field logical name from id or name: fieldName:NAME:1 -> NAME
        field_code = None
        for source in (id_attr, name_attr):
            if source and "fieldName:" in source:
                parts = source.split(":")
                if len(parts) >= 3:
                    field_code = parts[1]
                    break

        fieldname = field_code or id_attr or name_attr or "UNKNOWN"

        # Prefer id-based XPath, then name-based
        if id_attr:
            field_xpath = f"//*[@id='{id_attr}']"
        elif name_attr:
            field_xpath = f"//*[@name='{name_attr}']"
        else:
            # As a fallback, we can use a generic XPath by position
            field_xpath = _build_positional_xpath(driver, el)

        input_type = f"{tag}:{type_attr}" if type_attr else tag

        result.append({
            "fieldname": fieldname,
            "field_xpath": field_xpath,
            "inputfield_type": input_type,
        })

    return result


def _build_positional_xpath(driver, element) -> str:
    """Build a very simple positional XPath for elements without id/name.

    This is a last-resort fallback and may not be stable across releases,
    but ensures we always return some XPath.
    """
    # Walk up the DOM until body, building an index-based path
    path_segments = []
    current = element
    while True:
        parent = current.find_element(By.XPATH, "..")
        children = parent.find_elements(By.XPATH, "./*")
        index = 1
        for child in children:
            if child is current:
                break
            if child.tag_name == current.tag_name:
                index += 1
        segment = f"{current.tag_name}[{index}]"
        path_segments.insert(0, segment)
        if parent.tag_name.lower() == "html":
            break
        current = parent
    return "//" + "/".join(path_segments)


def write_rows_to_csv(rows: List[Dict], csv_path: str):
    header = ["pagename", "hierarchy", "fieldname", "field_xpath", "inputfield_type"]
    write_header = not os.path.exists(csv_path)

    os.makedirs(os.path.dirname(csv_path) or ".", exist_ok=True)

    with open(csv_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=header)
        if write_header:
            writer.writeheader()
        for row in rows:
            writer.writerow(row)


def main():
    # Configure Chrome options as needed
    options = Options()
    # options.add_argument("--headless=new")  # Uncomment if you want headless mode
    options.add_argument("--start-maximized")

    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 30)

    try:
        # Navigate to the BrowserWeb URL. You will log in manually.
        driver.get("http://10.0.251.41:18080/BrowserWeb")
        input("Please log in and navigate to the main menu page, then press Enter here to continue...")

        # Traverse menu to find trial pages
        leaves = traverse_menu(driver)
        if not leaves:
            print("No trial pages found in the menu. Check TRIAL_PAGES names and menu structure.")
            return

        print(f"Found {len(leaves)} trial pages to process:")
        for leaf in leaves:
            print(f" - {leaf['hierarchy']}")

        csv_path = os.path.join(os.path.dirname(__file__), "mandatory_fields_trial.csv")

        for leaf in leaves:
            print(f"\nProcessing page: {leaf['page_name']}")

            original_handle, new_handle = open_page_in_new_tab(driver, leaf, wait)

            try:
                # Switch into correct form context (main or iframe)
                switch_to_form_context(driver, wait)

                # Click Validate and wait for errors
                click_validate_and_wait(driver, wait)

                # Collect mandatory fields
                fields = collect_mandatory_fields(driver)
                print(f"  Found {len(fields)} mandatory fields")

                rows = []
                for f in fields:
                    rows.append({
                        "pagename": leaf["page_name"],
                        "hierarchy": leaf["hierarchy"],
                        "fieldname": f["fieldname"],
                        "field_xpath": f["field_xpath"],
                        "inputfield_type": f["inputfield_type"],
                    })

                if rows:
                    write_rows_to_csv(rows, csv_path)

            finally:
                # Close the tab and return to menu
                try:
                    driver.close()
                except Exception:
                    pass
                try:
                    driver.switch_to.window(original_handle)
                except Exception:
                    pass

        print(f"\nDone. Results written to: {csv_path}")

    finally:
        driver.quit()


if __name__ == "__main__":
    main()
