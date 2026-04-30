#!/usr/bin/env python3
"""
Verify C parsing logic matches IDA sub_1088D exactly.
"""
import struct

def main():
    # Load FDFIELD.DAT
    with open('data/FDFIELD.DAT', 'rb') as f:
        data = f.read()
    
    print("=" * 80)
    print("Verifying C code parsing logic against IDA sub_1088D")
    print("=" * 80)
    
    # Parse index table (99 entries)
    count = (len(data) - 6) // 4
    offsets = []
    for i in range(count):
        pos = 6 + i * 4
        offset = struct.unpack_from('<I', data, pos)[0]
        offsets.append(offset)
    
    print(f"\nFDFIELD.DAT: {len(data)} bytes, {count} index entries")
    
    # Verify each map
    all_ok = True
    
    for map_id in range(33):
        layout_idx = 3 * map_id
        control_idx = 3 * map_id + 1
        charpos_idx = 3 * map_id + 2
        
        # Get data ranges
        layout_start = offsets[layout_idx]
        layout_end = offsets[layout_idx + 1]
        layout_data = data[layout_start:layout_end]
        
        control_start = offsets[control_idx]
        control_end = offsets[control_idx + 1]
        control_data = data[control_start:control_end]
        
        charpos_start = offsets[charpos_idx]
        charpos_end = offsets[charpos_idx + 1]
        charpos_data = data[charpos_start:charpos_end]
        
        # Parse control data (IDA line 1098b-10995)
        terrain_set_id = control_data[0]
        max_friendly = control_data[1]  # ::n6
        total_units = control_data[2]   # dword_53BE3
        
        # Parse map dimensions
        map_width = struct.unpack_from('<H', layout_data, 0)[0]
        map_height = struct.unpack_from('<H', layout_data, 2)[0]
        
        # Parse character positions
        total_chars = struct.unpack_from('<H', charpos_data, 0)[0]
        
        # IDA v4 offset calculation
        v4_offset = 6 * total_units + 2
        
        # Read max_friendly characters
        friendly_chars = []
        for i in range(max_friendly):
            offset = v4_offset + i * 6
            if offset + 6 > len(charpos_data):
                break
            x = charpos_data[offset]
            y = charpos_data[offset + 2]
            portrait = charpos_data[offset + 3]
            friendly_chars.append((x, y, portrait))
        
        # Check if C code would parse correctly
        # C code at line 598-602:
        #   max_friendly = control_data[0]  # BUG! Should be [1]
        #   total_units = control_data[1]   # BUG! Should be [2]
        
        c_max_friendly = control_data[0]  # What C code uses
        c_total_units = control_data[1]   # What C code uses
        
        # Check if C code matches IDA
        ida_match = (c_max_friendly == max_friendly and c_total_units == total_units)
        
        if not ida_match:
            all_ok = False
            print(f"\n❌ Map {map_id}: C code BUG detected!")
            print(f"  IDA:     max_friendly={max_friendly}, total_units={total_units}")
            print(f"  C code:  max_friendly={c_max_friendly}, total_units={c_total_units}")
            print(f"  IDA terrain_set_id = {terrain_set_id}")
            print(f"  C code uses: terrain_set_id = control_data[0] = {c_max_friendly} (WRONG!)")
        else:
            print(f"\n✓ Map {map_id}: {map_width}x{map_height}, terrain={terrain_set_id}, "
                  f"{max_friendly} friendly, {total_units} enemies, {len(friendly_chars)} chars parsed")
            if friendly_chars:
                print(f"  Friendly chars: {friendly_chars[:3]}...")
    
    print("\n" + "=" * 80)
    if all_ok:
        print("✓ All maps: C code matches IDA logic")
    else:
        print("❌ CRITICAL: C code does NOT match IDA logic!")
        print("\nFix required in fd2_map_loader.c lines 598-602:")
        print("  Current (WRONG):")
        print("    max_friendly = control_data[0];")
        print("    total_units = control_data[1];")
        print("  Should be (IDA correct):")
        print("    terrain_set_id = control_data[0];")
        print("    max_friendly = control_data[1];")
        print("    total_units = control_data[2];")
    print("=" * 80)

if __name__ == '__main__':
    main()
