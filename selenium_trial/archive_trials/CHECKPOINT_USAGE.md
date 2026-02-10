# Checkpoint/Resume Feature

The crawler now supports automatic checkpoint and resume functionality. If the crawler is interrupted (Ctrl+C, crash, network issue), you can restart it and it will continue from where it left off.

## How It Works

1. **Automatic Checkpointing**: After each successful page extraction, the crawler saves:
   - List of processed items (by hierarchy + page name)
   - Current index position
   - Timestamp

2. **Auto-Resume on Restart**: When you restart the crawler:
   - Loads previous checkpoint data
   - Loads existing Excel data
   - Skips already-processed items
   - Continues from last position

3. **Auto-Clear on Completion**: When all items are processed, the checkpoint is automatically cleared

## Files Created

- **`crawler_checkpoint.json`**: Stores checkpoint data (created automatically)
- **`uiMap_selenium_fullrun_auto.xlsx`**: Main output file (appended during resume)

## Usage

### Normal Run
```bash
python crawler.py
```
Just run normally - no changes needed!

### Resume After Interruption
1. If crawler stops (Ctrl+C, crash, etc.), **just run it again**:
   ```bash
   python crawler.py
   ```
2. The crawler will automatically:
   - Detect existing checkpoint
   - Load previous data
   - Show: "🔄 RESUMING from index X (Y items already processed)"
   - Skip already-processed items
   - Continue where it left off

### Manual Checkpoint Management

**Check checkpoint status:**
```powershell
Get-Content crawler_checkpoint.json | ConvertFrom-Json | Format-List
```

**Clear checkpoint manually (start fresh):**
```powershell
Remove-Item crawler_checkpoint.json
```

**See what's already processed:**
```powershell
(Get-Content crawler_checkpoint.json | ConvertFrom-Json).processed_items
```

## Important Notes

1. **Don't delete the Excel file** during a paused crawl - it contains your progress
2. **Checkpoint file is portable** - you can backup `crawler_checkpoint.json` + Excel file
3. **Duplicate prevention** - Uses hierarchy + page name to identify unique items
4. **Safe interruption** - Press Ctrl+C anytime, progress is saved after each item

## Example Output

**First Run:**
```
🎯 Found 4336 visible/clickable leaf nodes
[1/4336] 🖱️ Clicking: Customer
[2/4336] 🖱️ Clicking: Account
```
*Press Ctrl+C*

**Resume (Second Run):**
```
📂 Loaded 50 existing records from uiMap_selenium_fullrun_auto.xlsx
🔄 RESUMING from index 2 (2 items already processed)

🎯 Found 4336 visible/clickable leaf nodes
[1/4336] ⏭️ Already processed: Customer
[2/4336] ⏭️ Already processed: Account  
[3/4336] 🖱️ Clicking: Transaction
```

## Troubleshooting

**"Checkpoint exists but crawler starts from beginning"**
- Excel file may have been deleted - checkpoint needs the Excel data
- Delete `crawler_checkpoint.json` to start fresh

**"Same items being processed twice"**
- Menu structure may have changed between runs
- Checkpoint uses hierarchy path - if path changes, item seen as new
- Clear checkpoint and Excel to start fresh
