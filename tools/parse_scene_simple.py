"""
Simple scene data parser for FD2.
Outputs scene command data in C format for integration.
"""

import struct

# Scene table pointers extracted from IDA MCP at 0x627D8
SCENE_POINTERS = [
    0x62980, 0x6299B, 0x629A6, 0x629D1, 0x629F0, 0x62A01, 0x62A06,
    0x62A1B, 0x62A30, 0x62A3D, 0x62A6E, 0x62A87, 0x62AAA, 0x62AD1,
    0x62AFE, 0x62B03, 0x62B10, 0x62B29, 0x62B3E, 0x62B4D, 0x62B68,
    0x62B95, 0x62BB4, 0x62BBD, 0x62BD0, 0x62BDB, 0x62BE0, 0x62BE5,
    0x62BEA, 0x62CAB, 0x62CD2, 0x62D29, 0x62D40, 0x62D45, 0x62D5C,
    0x62D71, 0x62D76, 0x62D7B, 0x62D80, 0x62D91, 0x62D9A, 0x62DE1,
    0x62E6A, 0x62E85, 0x62E98, 0x62EAB, 0x62EB4, 0x62EE9, 0x62EEE,
    0x62F07, 0x62F0C, 0x62F15, 0x62F1E, 0x62F27, 0x62F4A, 0x62F6F,
    0x62F76, 0x62F83, 0x62F88, 0x62F8D, 0x62FE8, 0x62FED, 0x62FF2,
    0x62FF7
]

def parse_scene_from_bytes(data_bytes):
    """Parse scene data from raw bytes."""
    if not data_bytes:
        return None
    
    pos = 0
    cmd_count = data_bytes[pos]
    pos += 1
    
    commands = []
    for i in range(cmd_count):
        if pos >= len(data_bytes):
            break
        
        cmd_type = data_bytes[pos]
        pos += 1
        
        param_count = data_bytes[pos]
        pos += 1
        
        params = []
        for j in range(param_count):
            if pos + 1 >= len(data_bytes):
                break
            param_val = struct.unpack('<H', data_bytes[pos:pos+2])[0]
            params.append(param_val)
            pos += 2
        
        commands.append({
            'type': cmd_type,
            'param_count': param_count,
            'params': params
        })
    
    return {
        'cmd_count': cmd_count,
        'commands': commands,
        'size': pos
    }

def format_scene_c(idx, scene_data):
    """Format scene data as C struct."""
    lines = []
    lines.append(f"/* Scene {idx} */")
    lines.append(f"{{")
    lines.append(f"    .cmd_count = {scene_data['cmd_count']},")
    lines.append(f"    .commands = (scene_cmd_t[]){{")
    
    for i, cmd in enumerate(scene_data['commands']):
        params_str = ", ".join([f"0x{p:04X}" for p in cmd['params']])
        lines.append(f"        {{ .type = {cmd['type']}, .param_count = {cmd['param_count']}, .params = {{{params_str}}} }},")
    
    lines.append(f"    }},")
    lines.append(f"}},")
    return "\n".join(lines)

if __name__ == "__main__":
    print("FD2 Scene Data Parser - C Code Generator")
    print("This script generates C code for scene data integration.")
    print("Run it with extracted scene bytes from IDA MCP.")
    print()
    print("Example usage:")
    print("  1. Extract scene bytes using IDA MCP get_bytes")
    print("  2. Convert to Python bytes list")
    print("  3. Run this script to generate C struct")
