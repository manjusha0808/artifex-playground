"""
Analyze both Excel files to understand zero-element pages and plan next steps.
"""

import pandas as pd

print("="*70)
print("ANALYZING CRAWLER OUTPUT FILES")
print("="*70)

# Load both files
print("\n📊 Loading files...")
stats_df = pd.read_excel('page_statistics.xlsx')
xpath_df = pd.read_excel('uiMap_output.xlsx')

print(f"\n✅ Loaded:")
print(f"   - page_statistics.xlsx: {len(stats_df)} pages")
print(f"   - uiMap_output.xlsx: {len(xpath_df)} XPath records")

# Basic statistics
print("\n" + "="*70)
print("OVERALL STATISTICS")
print("="*70)

total_pages = len(stats_df)
zero_element_pages = len(stats_df[stats_df['ElementCount'] == 0])
non_zero_pages = total_pages - zero_element_pages

print(f"\n📈 Element Count Distribution:")
print(f"   Total pages processed: {total_pages}")
print(f"   Pages with 0 elements: {zero_element_pages} ({zero_element_pages/total_pages*100:.1f}%)")
print(f"   Pages with >0 elements: {non_zero_pages} ({non_zero_pages/total_pages*100:.1f}%)")

# Element count statistics for non-zero pages
if non_zero_pages > 0:
    non_zero_df = stats_df[stats_df['ElementCount'] > 0]
    print(f"\n   Non-zero element statistics:")
    print(f"     Min: {non_zero_df['ElementCount'].min()}")
    print(f"     Max: {non_zero_df['ElementCount'].max()}")
    print(f"     Average: {non_zero_df['ElementCount'].mean():.1f}")
    print(f"     Median: {non_zero_df['ElementCount'].median():.0f}")

# Analyze zero-element pages
print("\n" + "="*70)
print("ZERO-ELEMENT PAGES ANALYSIS")
print("="*70)

zero_df = stats_df[stats_df['ElementCount'] == 0]

if len(zero_df) > 0:
    # Check iframe presence
    zero_with_iframes = len(zero_df[zero_df['HasIframes'] == 'Yes'])
    zero_without_iframes = len(zero_df) - zero_with_iframes
    
    print(f"\n🔍 Iframe Analysis (0-element pages):")
    print(f"   Pages with iframes: {zero_with_iframes} ({zero_with_iframes/len(zero_df)*100:.1f}%)")
    print(f"   Pages without iframes: {zero_without_iframes} ({zero_without_iframes/len(zero_df)*100:.1f}%)")
    
    # Check if they have actual input elements
    zero_with_inputs = len(zero_df[zero_df['TotalInputElements'] > 0])
    zero_without_inputs = len(zero_df) - zero_with_inputs
    
    print(f"\n💡 Input Element Presence (0-element pages):")
    print(f"   Pages with input/select/textarea: {zero_with_inputs} ({zero_with_inputs/len(zero_df)*100:.1f}%)")
    print(f"   Pages truly without inputs: {zero_without_inputs} ({zero_without_inputs/len(zero_df)*100:.1f}%)")
    
    # Show breakdown
    if zero_with_inputs > 0:
        zero_with_inputs_df = zero_df[zero_df['TotalInputElements'] > 0]
        print(f"\n   🔥 CRITICAL: {zero_with_inputs} pages have inputs but returned 0 XPaths!")
        print(f"      Average inputs on these pages: {zero_with_inputs_df['TotalInputElements'].mean():.1f}")
        print(f"      Max inputs: {zero_with_inputs_df['TotalInputElements'].max()}")
        
        # Show if these have iframes
        zero_inputs_with_iframes = len(zero_with_inputs_df[zero_with_inputs_df['HasIframes'] == 'Yes'])
        print(f"      Of these, {zero_inputs_with_iframes} have iframes ({zero_inputs_with_iframes/len(zero_with_inputs_df)*100:.1f}%)")
    
    # Error analysis
    zero_with_errors = len(zero_df[zero_df['ErrorOccurred'] == 'Yes'])
    print(f"\n⚠️ Error Analysis (0-element pages):")
    print(f"   Pages with errors: {zero_with_errors} ({zero_with_errors/len(zero_df)*100:.1f}%)")
    
    if zero_with_errors > 0:
        error_types = zero_df[zero_df['ErrorOccurred'] == 'Yes']['ErrorMessage'].value_counts()
        print(f"\n   Error types:")
        for error, count in error_types.head(5).items():
            print(f"     - {error[:60]}: {count}")

# Analyze non-zero pages
print("\n" + "="*70)
print("NON-ZERO ELEMENT PAGES ANALYSIS")
print("="*70)

non_zero_df = stats_df[stats_df['ElementCount'] > 0]

if len(non_zero_df) > 0:
    # Iframe presence
    nonzero_with_iframes = len(non_zero_df[non_zero_df['HasIframes'] == 'Yes'])
    
    print(f"\n🔍 Iframe Analysis (non-zero pages):")
    print(f"   Pages with iframes: {nonzero_with_iframes} ({nonzero_with_iframes/len(non_zero_df)*100:.1f}%)")
    
    # Compare ElementCount vs TotalInputElements
    print(f"\n📊 XPath Extraction Efficiency:")
    non_zero_df['ExtractionRate'] = (non_zero_df['ElementCount'] / non_zero_df['TotalInputElements'] * 100).round(1)
    avg_extraction = non_zero_df['ExtractionRate'].mean()
    print(f"   Average extraction rate: {avg_extraction:.1f}%")
    print(f"   (How many of the total inputs were successfully extracted as XPaths)")
    
    low_extraction = len(non_zero_df[non_zero_df['ExtractionRate'] < 50])
    if low_extraction > 0:
        print(f"\n   ⚠️ {low_extraction} pages extracted <50% of available inputs")

# Sample pages to investigate
print("\n" + "="*70)
print("SAMPLE PAGES TO INVESTIGATE")
print("="*70)

print("\n🔬 Zero elements WITH inputs (should have been extracted):")
if zero_with_inputs > 0:
    sample_zero = zero_df[zero_df['TotalInputElements'] > 0].head(5)
    for idx, row in sample_zero.iterrows():
        print(f"   - {row['PageName']}")
        print(f"     Inputs:{row['InputCount']} Selects:{row['SelectCount']} Textareas:{row['TextareaCount']}")
        print(f"     HasIframes: {row['HasIframes']} (Count: {row['IframeCount']})")
        print()

print("\n✅ Working pages (for comparison):")
if non_zero_pages > 0:
    sample_working = non_zero_df.head(5)
    for idx, row in sample_working.iterrows():
        print(f"   - {row['PageName']}")
        print(f"     ElementCount: {row['ElementCount']} | TotalInputs: {row['TotalInputElements']}")
        print(f"     HasIframes: {row['HasIframes']} (Count: {row['IframeCount']})")
        print()

# Next steps recommendation
print("\n" + "="*70)
print("RECOMMENDED NEXT STEPS")
print("="*70)

print("\n1. 🎯 ROOT CAUSE PRIORITIES:")

if zero_with_inputs > 0:
    zero_inputs_with_iframes = len(zero_df[(zero_df['TotalInputElements'] > 0) & (zero_df['HasIframes'] == 'Yes')])
    zero_inputs_no_iframes = zero_with_inputs - zero_inputs_with_iframes
    
    if zero_inputs_with_iframes > 0:
        print(f"   🔥 HIGH: {zero_inputs_with_iframes} pages have inputs in iframes (not checked by crawler)")
        print(f"      → Fix: Modify extract_xpaths_from_page() to switch into iframes")
    
    if zero_inputs_no_iframes > 0:
        print(f"   ⚠️ MEDIUM: {zero_inputs_no_iframes} pages have inputs but no iframes")
        print(f"      → Investigate: Timing issue? Hidden fields? CSS selector issue?")

if zero_without_inputs > 0:
    print(f"   ℹ️ LOW: {zero_without_inputs} pages truly have no input elements")
    print(f"      → These are likely enquiry/report pages (read-only)")

print("\n2. 🔧 IMPLEMENTATION PLAN:")
print("   a) Create iframe-aware crawler version")
print("   b) Test on sample zero-element pages")
print("   c) Compare before/after extraction counts")
print("   d) Re-run full crawl with iframe support")

print("\n3. 📋 VALIDATION:")
print("   a) Manually inspect 5-10 zero-element pages with inputs")
print("   b) Confirm if fields are in iframes vs main document")
print("   c) Check browser console for any JavaScript errors")

print("\n" + "="*70)

# Save detailed analysis
print("\n💾 Generating detailed CSV reports...")

# Export zero-element pages with inputs for investigation
if zero_with_inputs > 0:
    zero_priority = zero_df[zero_df['TotalInputElements'] > 0].sort_values('TotalInputElements', ascending=False)
    zero_priority.to_csv('zero_elements_WITH_inputs.csv', index=False)
    print(f"   ✅ zero_elements_WITH_inputs.csv ({len(zero_priority)} pages)")

# Export all zero-element pages
zero_df.to_csv('zero_elements_ALL.csv', index=False)
print(f"   ✅ zero_elements_ALL.csv ({len(zero_df)} pages)")

# Export summary
summary_df = stats_df.groupby('ElementCount').agg({
    'PageName': 'count',
    'HasIframes': lambda x: (x == 'Yes').sum(),
    'TotalInputElements': 'mean'
}).round(1)
summary_df.columns = ['PageCount', 'PagesWithIframes', 'AvgTotalInputs']
summary_df.to_csv('element_count_summary.csv')
print(f"   ✅ element_count_summary.csv")

print("\n✨ Analysis complete!")
