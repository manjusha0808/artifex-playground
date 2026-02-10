"""
Compare what old crawler extracted vs new crawler for "Input Prospect (Person)"
"""

import pandas as pd

print("="*70)
print("COMPARING OLD vs NEW CRAWLER OUTPUT")
print("="*70)

# Load old successful extraction
old_df = pd.read_excel('uiMap_selenium_fullrun_auto4_cleaned.xlsx')

# Filter for Input Prospect (Person)
prospect = old_df[old_df['page'].str.contains('Input Prospect \(Person\)', na=False, case=False)]

print(f"\n📊 Old Crawler Results for 'Input Prospect (Person)':")
print(f"   Total XPaths extracted: {len(prospect)}")

if len(prospect) > 0:
    print(f"\n   Tag breakdown:")
    print(prospect['tagName'].value_counts().to_string())
    
    print(f"\n   Type breakdown (for input tags):")
    input_types = prospect[prospect['tagName']=='input']['type'].value_counts()
    if len(input_types) > 0:
        print(input_types.to_string())
    else:
        print("   (No input tags with type attribute)")
    
    print(f"\n   First 10 extracted elements:")
    sample = prospect.head(10)[['relativeXpath', 'elementName', 'id', 'name', 'tagName', 'type']]
    for idx, row in sample.iterrows():
        print(f"   - XPath: {row['relativeXpath'][:60]}")
        print(f"     Name: {row['elementName']}, Tag: {row['tagName']}, Type: {row['type']}")
        print()
    
    # Check if any are from iframes or have special attributes
    print(f"\n   Sample IDs:")
    ids = prospect[prospect['id'].notna()]['id'].head(10).tolist()
    for i, elem_id in enumerate(ids, 1):
        print(f"   {i}. {elem_id}")
    
    print(f"\n   Sample Names:")
    names = prospect[prospect['name'].notna()]['name'].head(10).tolist()
    for i, elem_name in enumerate(names, 1):
        print(f"   {i}. {elem_name}")

else:
    print("   ⚠️ Old crawler also found 0 elements for this page!")

print("\n" + "="*70)
print("KEY QUESTION:")
print("="*70)
print("\nIf old crawler extracted XPaths successfully, we need to understand:")
print("1. What selector did it use?")
print("2. Did it wait longer for page load?")
print("3. Did it check different contexts?")
print("4. Were these hidden inputs included or different elements?")
