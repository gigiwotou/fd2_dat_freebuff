"""
Extract all scene data from IDA MCP and output as C arrays.
This helps verify scene data is correct before implementing scene playback.
"""

import struct

# Scene pointer table from IDA at 0x627D8 (106 entries, 4 bytes each, little-endian)
SCENE_POINTERS = [
    0x62980, 0x6299B, 0x629A6, 0x629D1, 0x629F0, 0x62A01, 0x62A06, 0x62A1B, 0x62A30, 0x62A3D,
    0x62A6E, 0x62A87, 0x62AAA, 0x62AD1, 0x62AFE, 0x62B03, 0x62B10, 0x62B29, 0x62B3E, 0x62B4D,
    0x62B68, 0x62B95, 0x62BB4, 0x62BBD, 0x62BD0, 0x62BDB, 0x62BE0, 0x62BE5, 0x62BEA, 0x62CAB,
    0x62CD2, 0x62D29, 0x62D40, 0x62D45, 0x62D5C, 0x62D71, 0x62D76, 0x62D7B, 0x62D80, 0x62D91,
    0x62D9A, 0x62DE1, 0x62E6A, 0x62E85, 0x62E98, 0x62EAB, 0x62EB4, 0x62EE9, 0x62EEE, 0x62F07,
    0x62F0C, 0x62F15, 0x62F1E, 0x62F27, 0x62F4A, 0x62F6F, 0x62F76, 0x62F83, 0x62F88, 0x62F8D,
    0x62FE8, 0x62FED, 0x62FF2, 0x62FF7
]

# Scene data from IDA MCP (concatenated bytes from all scenes)
# This needs to be filled with actual data from IDA
# For now, I'll show the structure

def analyze_scene_format():
    """Analyze the raw scene data format from IDA."""
    
    # Scene 0 data from IDA (first 50 bytes)
    scene_0_data = bytes([
        0x5, 0x6, 0x4, 0x0, 0x2, 0x1, 0x2, 0x2, 0x2, 0x3, 0x2, 0x88, 0x1, 0x0, 0x1, 0x88, 0x1,
        0x0, 0x3, 0x88, 0x1, 0x0, 0x1, 0x84, 0x1, 0x0, 0x0, 0x1, 0x1, 0x4, 0x4, 0x0, 0x5, 0x0,
        0x6, 0x0, 0x7, 0x0, 0x4, 0x1, 0x4, 0x8, 0x2, 0x9, 0x2, 0xa, 0x1, 0xb, 0x3, 0x2
    ])
    
    # Scene 99 data from IDA (first 50 bytes)  
    scene_99_data = bytes([
        0x1, 0x1, 0x4, 0x4, 0x0, 0x5, 0x0, 0x6, 0x0, 0x7, 0x0, 0x4, 0x1, 0x4, 0x8, 0x2, 0x9,
        0x2, 0xa, 0x1, 0xb, 0x3, 0x2, 0x4, 0x8, 0x3, 0x9, 0x2, 0xa, 0x2, 0xb, 0x2, 0x2, 0x4,
        0x8, 0x2, 0x9, 0x3, 0xa, 0x2, 0xb, 0x2, 0x84, 0x5, 0x9, 0x2, 0x0, 0x0, 0x1, 0x0
    ])
    
    print("=== Scene 0 Format Analysis ===")
    print(f"Raw data: {scene_0_data.hex(' ')}")
    
    # Parse according to sub_1366A logic
    offset = 0
    cmd_count = scene_0_data[offset]
    offset += 1
    print(f"Command count: {cmd_count}")
    
    for i in range(cmd_count):
        if offset >= len(scene_0_data):
            break
        
        cmd_type = scene_0_data[offset]
        param_count = scene_0_data[offset + 1]
        offset += 2
        
        params = []
        for j in range(param_count):
            if offset + 1 < len(scene_0_data):
                param = struct.unpack('<H', scene_0_data[offset:offset+2])[0]
                params.append(param)
                offset += 2
        
        is_special = (cmd_type & 0x80) != 0
        print(f"  [{i}] type=0x{cmd_type:02X}{' (special)' if is_special else ''}, params={param_count}, values={params}")
    
    print(f"\nTotal parsed: {offset} bytes")
    print(f"Data length: {len(scene_0_data)} bytes")
    
    print("\n=== Scene 99 Format Analysis ===")
    print(f"Raw data: {scene_99_data.hex(' ')}")
    
    offset = 0
    cmd_count = scene_99_data[offset]
    offset += 1
    print(f"Command count: {cmd_count}")
    
    for i in range(cmd_count):
        if offset >= len(scene_99_data):
            break
        
        cmd_type = scene_99_data[offset]
        param_count = scene_99_data[offset + 1]
        offset += 2
        
        params = []
        for j in range(param_count):
            if offset + 1 < len(scene_99_data):
                param = struct.unpack('<H', scene_99_data[offset:offset+2])[0]
                params.append(param)
                offset += 2
        
        is_special = (cmd_type & 0x80) != 0
        print(f"  [{i}] type=0x{cmd_type:02X}{' (special)' if is_special else ''}, params={param_count}, values={params}")
    
    print(f"\nTotal parsed: {offset} bytes")

if __name__ == "__main__":
    analyze_scene_format()