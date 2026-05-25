#!/usr/bin/env python3
"""分析 _FDOTHER.DAT__13 资源类型"""
import struct

dat_path = r'D:\workspace\fd2_dat_freebuff\bin\FDOTHER.DAT'

with open(dat_path, 'rb') as f:
    data = f.read()

count = struct.unpack_from('<I', data, 6)[0]
offsets = []
for i in range(count):
    offset = struct.unpack_from('<I', data, 10 + i * 4)[0]
    offsets.append(offset)

# 检查 v36 数组对应的索引
# v36 = "?355[\\]^" (ASCII: 63, 51, 53, 53, 91, 92, 93, 94)
v36 = [63, 51, 53, 53, 91, 92, 93, 94]

print(f"资源总数: {count}")

# 检查 v36 数组对应的索引
print(f"\n_FDOTHER.DAT__13 实际加载的索引 (v36[n28]):")
for scene, idx in enumerate(v36):
    if idx < len(offsets):
        res_start = offsets[idx]
        res_end = offsets[idx+1] if idx+1 < len(offsets) else len(data)
        res_data = data[res_start:res_end]
        
        is_llllll = res_data[:6] == b'LLLLLL'
        
        print(f"  场景{scene}: 索引{idx} (0x{idx:02X}), 大小={len(res_data)}, 嵌套DAT={is_llllll}")
        
        if is_llllll:
            nested_count = struct.unpack_from('<I', res_data, 6)[0]
            print(f"    嵌套资源数/未知值: {nested_count}")
            
            # 检查前几个偏移
            for tile_idx in range(min(5, nested_count)):
                tile_offset = struct.unpack_from('<I', res_data, 10 + tile_idx*4)[0]
                if tile_offset < len(res_data):
                    tile_size = 0
                    # 查找下一个有效偏移
                    for next_idx in range(tile_idx + 1, min(nested_count, 20)):
                        next_offset = struct.unpack_from('<I', res_data, 10 + next_idx*4)[0]
                        if next_offset >= len(res_data):
                            break
                        tile_size = next_offset - tile_offset
                        break
                    
                    if tile_size == 0:
                        tile_size = len(res_data) - tile_offset
                    
                    tile_data = res_data[tile_offset:tile_offset+min(tile_size, 32)]
                    print(f"    Tile {tile_idx}: 偏移=0x{tile_offset:X}, 大小={tile_size}, 前32字节={tile_data.hex()}")
                    
                    # 检查是否是音频数据 (WAV头?)
                    if tile_data[:4] == b'RIFF' or tile_data[:4] == b'fmt ':
                        print(f"      -> 可能是音频数据")
                    elif tile_data[0:1] == b'\x00' and tile_data[1:2] == b'\x00':
                        print(f"      -> 可能是零开头的数据")
        else:
            # 打印前32字节
            print(f"    前32字节: {res_data[:32].hex()}")
            
            # 检查是否是音频数据
            if res_data[:4] == b'RIFF' or res_data[:4] == b'fmt ':
                print(f"    -> 可能是音频数据 (WAV)")
