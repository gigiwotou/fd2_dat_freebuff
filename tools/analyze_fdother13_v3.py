#!/usr/bin/env python3
"""分析 _FDOTHER.DAT__13 实际使用的索引"""
import struct

dat_path = r'D:\workspace\fd2_dat_freebuff\bin\FDOTHER.DAT'

with open(dat_path, 'rb') as f:
    data = f.read()

if data[:6] != b'LLLLLL':
    print("不是有效的 FDOTHER.DAT 文件")
else:
    count = struct.unpack_from('<I', data, 6)[0]
    offsets = []
    for i in range(count):
        offset = struct.unpack_from('<I', data, 10 + i * 4)[0]
        offsets.append(offset)
    
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
                print(f"    嵌套资源数: {nested_count}")
                
                # 检查tile头
                for tile_idx in range(min(5, nested_count)):
                    tile_offset = struct.unpack_from('<I', res_data, 10 + tile_idx*4)[0]
                    if tile_offset < len(res_data):
                        tile_data = res_data[tile_offset:tile_offset+16]
                        w = struct.unpack_from('<H', tile_data, 0)[0]
                        h = struct.unpack_from('<H', tile_data, 2)[0]
                        print(f"    Tile {tile_idx}: 偏移=0x{tile_offset:X}, w={w}, h={h}")
            else:
                # 打印前16字节
                print(f"    前16字节: {res_data[:16].hex()}")
    
    # 也检查所有嵌套DAT
    print(f"\n\n所有嵌套DAT资源:")
    nested_count = 0
    for i in range(count):
        res_start = offsets[i]
        res_end = offsets[i+1] if i+1 < len(offsets) else len(data)
        res_data = data[res_start:res_end]
        
        if res_data[:6] == b'LLLLLL':
            nc = struct.unpack_from('<I', res_data, 6)[0]
            print(f"  索引{i}: 大小={len(res_data)}, 嵌套={nc}")
            nested_count += 1
    
    print(f"\n总共 {nested_count} 个嵌套DAT资源")
