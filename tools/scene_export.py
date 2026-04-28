#!/usr/bin/env python3
"""
Export FD2 scene data from IDA MCP and generate C code.
Run this after extracting scene data from IDA.
"""

# Scene 99 data from IDA MCP (at address 0x62D91)
# First 100 bytes extracted
SCENE_99_RAW = bytes([
    0x2, 0x88, 0x1, 0x8, 0x2, 0x80, 0x1, 0x8, 0x2, 0x8, 0x4, 0x1, 0xe, 0x0, 0x86, 0x1, 
    0xe, 0x1, 0x86, 0x1, 0xe, 0x3, 0x84, 0x1, 0xe, 0x2, 0x80, 0x1, 0xe, 0x2, 0x2, 0xa, 
    0xf, 0x0, 0x10, 0x0, 0x11, 0x0, 0x12, 0x0, 0x13, 0x0, 0x14, 0x0, 0x15, 0x0, 0x16, 
    0x0, 0x17, 0x0, 0x18, 0x0, 0x1, 0xb, 0xe, 0x0, 0xf, 0x0, 0x10, 0x0, 0x11, 0x0, 0x12, 
    0x0, 0x13, 0x0, 0x14, 0x0, 0x15, 0x0, 0x16, 0x0, 0x17, 0x0, 0x18, 0x0, 0x8a, 0x1, 
    0xe, 0x0, 0x9, 0x1, 0x2, 0xd, 0x2, 0x0, 0x2, 0x1, 0x6, 0xd, 0x2, 0xc, 0x2, 0xb, 
    0x2, 0xa, 0x2, 0x9, 0x2, 0x0
])

# Scene 0 data from IDA MCP (at address 0x62980)
SCENE_0_RAW = bytes([
    0x5, 0x6, 0x4, 0x0, 0x2, 0x1, 0x2, 0x2, 0x2, 0x3, 0x2, 0x88, 0x1, 0x0, 0x1, 0x88, 
    0x1, 0x0, 0x3, 0x88, 0x1, 0x0, 0x1, 0x84, 0x1, 0x0, 0x0
])

def parse_scene(scene_name, raw_data):
    """Parse scene data and print commands."""
    print(f"\n=== {scene_name} (size={len(raw_data)} bytes) ===")
    print("Raw bytes:")
    for i in range(0, len(raw_data), 16):
        chunk = raw_data[i:i+16]
        hex_str = ' '.join(f'{b:02x}' for b in chunk)
        print(f"  {i:3d}: {hex_str}")
    
    # Parse commands
    offset = 0
    cmd_count = raw_data[offset]
    offset += 1
    print(f"\nCommand count: {cmd_count}")
    
    for i in range(cmd_count):
        if offset >= len(raw_data):
            break
        
        cmd_type = raw_data[offset]
        param_count = raw_data[offset + 1]
        offset += 2
        
        params = []
        for j in range(param_count):
            if offset + 1 < len(raw_data):
                param = int.from_bytes(raw_data[offset:offset+2], 'little')
                params.append(param)
                offset += 2
        
        is_special = (cmd_type & 0x80) != 0
        print(f"  [{i:2d}] cmd=0x{cmd_type:02X}{' (special)' if is_special else ''}, "
              f"params={param_count}, values={params}")
    
    print(f"\nParsed {offset} bytes, remaining {len(raw_data) - offset} bytes")
    
    # Generate C code
    print("\nC code:")
    print(f"static const u8 {scene_name.lower().replace(' ', '_')}_raw[] = {{")
    for i in range(0, len(raw_data), 12):
        chunk = raw_data[i:i+12]
        hex_vals = ', '.join(f'0x{b:02x}' for b in chunk)
        print(f"    {hex_vals},")
    print("};\n")

def main():
    parse_scene("Scene 0", SCENE_0_RAW)
    parse_scene("Scene 99", SCENE_99_RAW)

if __name__ == "__main__":
    main()
