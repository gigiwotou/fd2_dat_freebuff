"""See what Python export tool actually reads for map 0"""
import struct
from pathlib import Path

fdfield_path = Path("game/FDFIELD.DAT")
data = fdfield_path.read_bytes()

# Python tool uses format 2: offsets from byte 6, no count
offsets_v2 = []
pos = 6
while pos < len(data) - 4:
    offset = struct.unpack_from("<I", data, pos)[0]
    if offset > pos and offset < len(data):
        offsets_v2.append(offset)
    else:
        break
    pos += 4

print(f"Python format 2 parsing: {len(offsets_v2)} offsets")
print(f"First 10 offsets: {offsets_v2[:10]}")

# Python tool for map 0:
layout_res_idx = 0  # map_id * 3 = 0 * 3 = 0
control_res_idx = 1  # map_id * 3 + 1 = 0 * 3 + 1 = 1

if len(offsets_v2) > control_res_idx + 1:
    layout_start = offsets_v2[layout_res_idx]
    layout_end = offsets_v2[layout_res_idx + 1]
    control_start = offsets_v2[control_res_idx]
    control_end = offsets_v2[control_res_idx + 1]
    
    layout_data = data[layout_start:layout_end]
    control_data = data[control_start:control_end]
    
    print(f"\nPython tool reads:")
    print(f"  Layout: resource {layout_res_idx}, offset {layout_start}-{layout_end}, size={len(layout_data)}")
    print(f"    First 20 bytes: {layout_data[:20].hex(' ')}")
    print(f"  Control: resource {control_res_idx}, offset {control_start}-{control_end}, size={len(control_data)}")
    print(f"    First 20 bytes: {control_data[:20].hex(' ')}")
    
    if len(layout_data) >= 4:
        w = struct.unpack_from("<H", layout_data, 0)[0]
        h = struct.unpack_from("<H", layout_data, 2)[0]
        print(f"    Parsed as layout: {w}x{h}")
    
    if len(control_data) >= 1:
        ts_id = control_data[0]
        print(f"    terrain_set_id = {ts_id} (0x{ts_id:02x})")
        
        # Check FDSHAP for this tileset
        fdshap_path = Path("game/FDSHAP.DAT")
        fdshap_data = fdshap_path.read_bytes()
        
        # Python uses format 2 for FDSHAP too
        shap_offsets_v2 = []
        pos = 6
        while pos < len(fdshap_data) - 4:
            offset = struct.unpack_from("<I", fdshap_data, pos)[0]
            if offset > pos and offset < len(fdshap_data):
                shap_offsets_v2.append(offset)
            else:
                break
            pos += 4
        
        print(f"\nFDSHAP.DAT (Python format 2): {len(shap_offsets_v2)} offsets")
        
        tile_set_res_idx = ts_id * 2  # terrain_set_id * 2
        if tile_set_res_idx < len(shap_offsets_v2) - 1:
            tile_start = shap_offsets_v2[tile_set_res_idx]
            tile_end = shap_offsets_v2[tile_set_res_idx + 1]
            tile_set_data = fdshap_data[tile_start:tile_end]
            print(f"  Tileset {ts_id} (resource {tile_set_res_idx}): offset {tile_start}-{tile_end}, size={len(tile_set_data)}")
            
            # Parse tileset header
            if len(tile_set_data) >= 6:
                tile_w = struct.unpack_from("<H", tile_set_data, 0)[0]
                tile_h = struct.unpack_from("<H", tile_set_data, 2)[0]
                tile_count = struct.unpack_from("<H", tile_set_data, 4)[0]
                print(f"    Tileset header: {tile_w}x{tile_h}, {tile_count} tiles")
