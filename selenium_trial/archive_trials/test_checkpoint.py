"""
Quick test to verify checkpoint file is being created and saved correctly.
"""
import json
import os

CHECKPOINT_FILE = 'crawler_checkpoint.json'

def check_checkpoint():
    """Check if checkpoint file exists and is valid."""
    if not os.path.exists(CHECKPOINT_FILE):
        print("❌ Checkpoint file does NOT exist")
        return False
    
    try:
        with open(CHECKPOINT_FILE, 'r') as f:
            data = json.load(f)
        
        print(f"✅ Checkpoint file is VALID")
        print(f"   - Last index: {data.get('last_index', 'MISSING')}")
        print(f"   - Processed items: {len(data.get('processed_items', []))}")
        print(f"   - Timestamp: {data.get('timestamp', 'MISSING')}")
        
        # Verify structure
        if 'last_index' not in data:
            print("   ⚠️ WARNING: 'last_index' field is missing!")
        if 'processed_items' not in data:
            print("   ⚠️ WARNING: 'processed_items' field is missing!")
        if 'timestamp' not in data:
            print("   ⚠️ WARNING: 'timestamp' field is missing!")
        
        return True
        
    except json.JSONDecodeError as e:
        print(f"❌ Checkpoint file is CORRUPTED: {e}")
        return False
    except Exception as e:
        print(f"❌ Error reading checkpoint: {e}")
        return False

if __name__ == "__main__":
    check_checkpoint()
