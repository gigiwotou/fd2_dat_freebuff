#!/usr/bin/env python3
"""
分析 _FDOTHER.DAT__13 实际加载的资源索引

根据sub_2D80D:
  v36 = "?355[\\]^"  (ASCII: 63, 51, 53, 53, 91, 92, 93, 94)
  FDOTHER_DAT__13 = sub_111BA(v36[n28], ...)
  
所以实际加载的索引是:
  场景0: v36[0] = '?' = 63
  场景1: v36[1] = '3' = 51
  场景2: v36[2] = '5' = 53
  场景3: v36[3] = '5' = 53
  场景4: v36[4] = '[' = 91
  场景5: v36[5] = '\\' = 92
  场景6: v36[6] = ']' = 93
  场景7: v36[7] = '^' = 94
"""
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
    
    # v36 = "?355[\\]^"
    v36 = [63, 51, 53, 53, 91, 92, 93, 94]
    
    print(f"资源总数: {count}")
    print(f"\n_FDOTHER.DAT__13 实际加载的索引:")
    for scene, idx in enumerate(v36):
        if idx < len(offsets):
            res_start = offsets[idx]
            res_end = offsets[idx+1] if idx+1 < len(offsets) else len(data)
            res_size = res_end - res_start
            
            # 检查是否是嵌套DAT
            res_data = data[res_start:res_end]
            is_nested = res_data[:6] == b'LLLLLL'
            
            print(f"  场景{scene}: 索引{idx} (0x{idx:02X}), 大小={res_size}, 嵌套DAT={is_nested}")
            
            if is_nested:
                nested_count = struct.unpack_from('<I', res_data, 6)[0]
                print(f"    嵌套资源数: {nested_count}")
                
                # 检查tile头
                for tile_idx in range(min(3, nested_count)):
                    tile_offset = struct.unpack_from('<I', res_data, 10 + tile_idx*4)[0]
                    if tile_offset < len(res_data):
                        tile_data = res_data[tile_offset:tile_offset+12]
                        w = struct.unpack_from('<H', tile_data, 0)[0]
                        h = struct.unpack_from('<H', tile_data, 2)[0]
                        print(f"    Tile {tile_idx}: 偏移=0x{tile_offset:X}, w={w}, h={h}")
