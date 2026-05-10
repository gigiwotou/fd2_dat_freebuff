"""
Extract scene data from FD2.EXE binary file.
Scene pointer table is at offset 0x627D8.
Each pointer is 4 bytes (little-endian).
"""

import struct

EXE_PATH = r"D:\workspace\fd2ida\FD2\FD2.EXE"
SCENE_POINTER_TABLE = 0x627D8
MAX_SCENE_INDEX = 106  # 0-105

def extract_scenes():
    with open(EXE_PATH, 'rb') as f:
        # Read pointer table
        f.seek(SCENE_POINTER_TABLE)
        pointers = []
        for i in range(MAX_SCENE_INDEX):
            ptr_bytes = f.read(4)
            if len(ptr_bytes) < 4:
                break
            ptr = struct.unpack('<I', ptr_bytes)[0]
            pointers.append(ptr)
        
        print(f"Extracted {len(pointers)} scene pointers from 0x{SCENE_POINTER_TABLE:X}")
        
        # Read each scene data
        for i, ptr in enumerate(pointers):
            if ptr == 0:
                print(f"Scene {i}: NULL pointer")
                continue
            
            f.seek(ptr)
            # Read scene: first byte is entry count
            entry_count_byte = f.read(1)
            if len(entry_count_byte) < 1:
                print(f"Scene {i}: Invalid data at 0x{ptr:X}")
                continue
            
            entry_count = entry_count_byte[0]
            
            # Parse all entries to determine total size
            f.seek(ptr)
            scene_data = bytearray()
            
            # Read entry count
            scene_data.append(entry_count)
            
            pos = ptr + 1
            for e in range(entry_count):
                # Read cmd_type and param_count
                f.seek(pos)
                header = f.read(2)
                if len(header) < 2:
                    break
                
                cmd_type = header[0]
                param_count = header[1]
                scene_data.extend(header)
                pos += 2
                
                # Read params (2 bytes each)
                for p in range(param_count):
                    param_bytes = f.read(2)
                    if len(param_bytes) < 2:
                        break
                    scene_data.extend(param_bytes)
                    pos += 2
            
            # Output as Python bytes literal
            if len(scene_data) > 0:
                # Format as hex string for readability
                hex_str = scene_data.hex(' ')
                print(f"\nScene {i}: {len(scene_data)} bytes at 0x{ptr:X}, entries={entry_count}")
                print(f"  Raw: {hex_str[:200]}{'...' if len(hex_str) > 200 else ''}")
                
                # Also output as Python bytes
                bytes_literal = "b'"
                for b in scene_data:
                    bytes_literal += f"\\x{b:02x}"
                bytes_literal += "'"
                
                if len(bytes_literal) > 500:
                    print(f"  Python: {bytes_literal[:500]}...")
                else:
                    print(f"  Python: {bytes_literal}")

if __name__ == "__main__":
    extract_scenes()
