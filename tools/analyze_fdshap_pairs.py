#!/usr/bin/env python3
"""重新分析FDSHAP.DAT的资源结构"""
import struct

with open('game/FDSHAP.DAT', 'rb') as f:
    data = f.read()

print(f"FDSHAP.DAT 文件大小: {len(data)} 字节")
print(f"魔数: {data[:6]}")

# 格式1: byte 6-9 有资源计数
count_fmt1 = struct.unpack_from("<I", data, 6)[0]
print(f"\n格式1 (byte 6计数): {count_fmt1} 个资源")

if count_fmt1 > 0 and count_fmt1 < 500:
    print("使用格式1解析...")
    offsets = []
    for i in range(count_fmt1):
        offset = struct.unpack_from("<I", data, 10 + i * 4)[0]
        offsets.append(offset)
    
    print(f"成功解析 {len(offsets)} 个资源\n")
    
    # 分析资源对
    for pair_idx in range(0, min(20, len(offsets)), 2):
        res0_offset = offsets[pair_idx]
        res1_offset = offsets[pair_idx + 1] if pair_idx + 1 < len(offsets) else len(data)
        res0_size = res1_offset - res0_offset
        
        if pair_idx + 2 < len(offsets):
            res2_size = offsets[pair_idx + 2] - res1_offset
        else:
            res2_size = len(data) - res1_offset
        
        terrain_set_id = pair_idx // 2
        print(f"terrain_set_id={terrain_set_id}:")
        print(f"  资源{pair_idx}: offset=0x{res0_offset:06x}, size={res0_size:6d} 字节")
        print(f"  资源{pair_idx+1}: offset=0x{res1_offset:06x}, size={res2_size:6d} 字节")
        
        # 分析资源0的前4字节（可能是瓦片头）
        res0_data = data[res0_offset:res0_offset+6]
        print(f"    资源0头部: {res0_data.hex(' ')}")
