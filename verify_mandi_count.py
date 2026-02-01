#!/usr/bin/env python3
"""
Quick verification script to check what's actually in the standalone_mandi_ear.py file
"""

import re

def check_mandi_count():
    """Check the current mandi count in the file"""
    try:
        with open('standalone_mandi_ear.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find all stat-number occurrences
        stat_numbers = re.findall(r'<span class="stat-number">([^<]+)</span>', content)
        
        print("🔍 Found stat-number values:")
        for i, stat in enumerate(stat_numbers):
            print(f"  {i+1}. {stat}")
        
        # Check specifically for mandis
        mandis_pattern = r'<span class="stat-number">([^<]+)</span>\s*<span class="stat-label"[^>]*>Mandis</span>'
        mandis_match = re.search(mandis_pattern, content)
        
        if mandis_match:
            mandis_count = mandis_match.group(1)
            print(f"\n✅ Current Mandis count: {mandis_count}")
        else:
            print("\n❌ Could not find Mandis stat")
        
        # Check for any 7000 references
        seven_thousand = re.findall(r'7[,\s]*000[+]*', content)
        if seven_thousand:
            print(f"\n⚠️  Found 7000 references: {seven_thousand}")
        else:
            print(f"\n✅ No 7000 references found")
            
    except FileNotFoundError:
        print("❌ standalone_mandi_ear.py not found in current directory")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("🔍 Verifying MANDI EAR™ mandi count...")
    check_mandi_count()