"""
Test script to verify image paths and file locations.
Run this from your emergency-backend directory.
"""

import os
from pathlib import Path

def test_image_paths():
    """Test if images exist in the expected locations"""
    
    base_path = Path("shenal_uploads")
    print(f"📁 Checking directory: {base_path.absolute()}")
    print(f"Directory exists: {base_path.exists()}")
    
    if not base_path.exists():
        print("❌ shenal_uploads directory not found!")
        return
    
    # Look for the specific image
    target_filename = "CBH 6301_151010_96a5d19f.jpg"
    print(f"\n🔍 Searching for: {target_filename}")
    
    found_files = []
    for file_path in base_path.rglob("*"):
        if file_path.is_file() and target_filename.lower() in file_path.name.lower():
            found_files.append(file_path)
    
    if found_files:
        print(f"✅ Found {len(found_files)} matches:")
        for f in found_files:
            print(f"  - {f}")
    else:
        print("❌ No matches found")
    
    # List all jpg files
    print(f"\n📊 All .jpg files in {base_path}:")
    jpg_files = list(base_path.rglob("*.jpg"))
    for i, f in enumerate(jpg_files[:10]):
        print(f"  {i+1}. {f.relative_to(base_path)}")
    
    if len(jpg_files) > 10:
        print(f"  ... and {len(jpg_files) - 10} more")

if __name__ == "__main__":
    test_image_paths()