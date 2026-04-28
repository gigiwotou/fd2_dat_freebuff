import struct
from pathlib import Path

data = Path("game/FDFIELD.DAT").read_bytes()

resource_count = struct.unpack_from('<I', data, 6)[0]

print(f"Resource count: {resource_count}")
print(f"Total file size: {len(data)} bytes")

# 根据IDA sub_111BA，偏移表从偏移10开始，每个资源8字节
print("\n=== Analyzing resource structure ===")

# 检查资源1（可能是地图0的布局数据）
for map_id in range(3):
    print(f"\n--- Map {map_id} ---")
    
    # 每个地图3个资源
    for res_type, res_idx in [("3*N (layout?)", map_id*3), 
                              ("3*N+1 (control?)", map_id*3+1), 
                              ("3*N+2 (spawn?)", map_id*3+2)]:
        pos = 10 + res_idx * 8
        start, end = struct.unpack_from("<II", data, pos)
        size = end - start
        res_data = data[start:end]
        
        print(f"  Resource {res_idx} ({res_type}): size={size}")
        if size >= 4:
            w, h = struct.unpack_from("<HH", res_data, 0)
            print(f"    First 4 bytes as width/height: w={w}, h={h}")
            print(f"    First 20 bytes: {res_data[:20].hex()}")
