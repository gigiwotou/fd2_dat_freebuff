"""
Parse scene data from FD2.exe binary.
Scene data table at 0x627D8 contains pointers to scene data.
Each scene: byte0=command_count, then commands (type + param_count + params)
"""

import struct
import sys

# Scene data table addresses (extracted from IDA MCP)
SCENE_TABLE_BASE = 0x627D8
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

# Scene IDs from sub_3231B analysis
SCENE_IDS = {
    0: "Battlefield Scene 0",
    1: "Battlefield Scene 1", 
    2: "Battlefield Scene 2",
    5: "Battlefield Scene 5",
    90: "Scene 90",
    91: "Scene 91",
    92: "Scene 92",
    93: "Scene 93",
    94: "Scene 94",
    95: "Scene 95",
    96: "Scene 96",
    97: "Scene 97",
    98: "Scene 98",
    99: "Opening Animation",
    100: "Scene 100",
    101: "Scene 101",
    102: "Scene 102",
    103: "Scene 103",
    104: "Scene 104",
    105: "Scene 105",
}

def read_exe_bytes(exe_path, offset, size):
    """Read bytes from exe file at given offset."""
    with open(exe_path, 'rb') as f:
        f.seek(offset)
        return f.read(size)

def parse_scene_command(cmd_type, params):
    """Parse a single scene command."""
    # Special commands from sub_15F84 analysis
    if cmd_type == 0xFF:  # -1 as unsigned
        return "END - Scene end marker"
    elif cmd_type == 0xFE:  # -2
        return "LINE_BREAK - Switch to next line/layer"
    elif cmd_type == 0xEF:  # -17
        char_id = params[0] if params else 0
        return f"CHAR_SPRITE_LOAD - Load character sprite ID={char_id}"
    elif cmd_type == 0xEE:  # -18
        return f"CHAR_SPRITE_LOAD_ALT - Alternate character loading"
    elif cmd_type == 0xED:  # -19
        char_idx = params[0] if params else 0
        return f"CHAR_STATE_LOAD - Load sprite from character state index={char_idx}"
    else:
        # Regular command
        param_str = ", ".join([f"0x{p:04X}" for p in params])
        return f"CMD type={cmd_type}, params=[{param_str}]"

def parse_scene_data(exe_path, scene_idx):
    """Parse scene data from exe file."""
    if scene_idx >= len(SCENE_POINTERS):
        print(f"Scene index {scene_idx} out of range")
        return
    
    scene_addr = SCENE_POINTERS[scene_idx]
    print(f"\n{'='*60}")
    print(f"Scene {scene_idx} (ID: {SCENE_IDS.get(scene_idx, 'Unknown')})")
    print(f"Address: 0x{scene_addr:05X}")
    print(f"{'='*60}")
    
    # Read command count
    data = read_exe_bytes(exe_path, scene_addr, 1)
    cmd_count = data[0]
    print(f"Command count: {cmd_count}")
    
    # Read commands
    offset = scene_addr + 1
    for i in range(cmd_count):
        # Read command type and param count
        cmd_header = read_exe_bytes(exe_path, offset, 2)
        cmd_type = cmd_header[0]
        param_count = cmd_header[1]
        offset += 2
        
        # Read parameters (2 bytes each, little-endian)
        params = []
        for j in range(param_count):
            param_data = read_exe_bytes(exe_path, offset, 2)
            param_val = struct.unpack('<H', param_data)[0]
            params.append(param_val)
            offset += 2
        
        # Parse and display
        cmd_desc = parse_scene_command(cmd_type, params)
        print(f"  [{i:3d}] {cmd_desc}")

def dump_all_scenes(exe_path):
    """Dump all scene data to analyze structure."""
    print(f"FD2 Scene Data Parser")
    print(f"Scene table base: 0x{SCENE_TABLE_BASE:05X}")
    print(f"Total scenes: {len(SCENE_POINTERS)}")
    
    for idx in range(len(SCENE_POINTERS)):
        scene_addr = SCENE_POINTERS[idx]
        data = read_exe_bytes(exe_path, scene_addr, 1)
        cmd_count = data[0]
        scene_name = SCENE_IDS.get(idx, "Unknown")
        print(f"  Scene {idx:3d}: addr=0x{scene_addr:05X}, cmds={cmd_count:3d}, name={scene_name}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python parse_scenes.py <FD2.EXE> [scene_idx]")
        print("  scene_idx: specific scene to parse (omit to list all)")
        sys.exit(1)
    
    exe_path = sys.argv[1]
    
    if len(sys.argv) >= 3:
        scene_idx = int(sys.argv[2])
        parse_scene_data(exe_path, scene_idx)
    else:
        dump_all_scenes(exe_path)
