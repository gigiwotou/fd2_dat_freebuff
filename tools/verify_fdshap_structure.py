#!/usr/bin/env python3
"""详细验证FDSHAP.DAT的结构"""
import struct

with open('game/FDSHAP.DAT', 'rb') as f:
    data = f.read()

print(f"FDSHAP.DAT 文件大小: {len(data)} 字节")
print(f"魔数: {data[:6]}")

# 格式1: byte 6-9 有资源计数
count1 = struct.unpack_from("<I", data, 6)[0]
print(f"\n格式1 (byte 6计数): {count1} 个资源")

# 验证格式1是否合理
if count1 > 0 and count1 < 500:
    offsets1 = []
    for i in range(count1):
        offset = struct.unpack_from("<I", data, 10 + i * 4)[0]
        offsets1.append(offset)
    
    # 检查第一个资源的大小
    res0_size = offsets1[1] - offsets1[0]
    res1_size = offsets1[2] - offsets1[1]
    
    print(f"  资源0: {res0_size} 字节")
    print(f"  资源1: {res1_size} 字节")
    
    # 资源0应该是调色板（1200字节）
    # 资源1应该是瓦片集（大资源）
    if res0_size <= 2000:
        print(f"  -> 资源0小 ({res0_size}字节)，可能是调色板")
        print(f"  -> 资源1大 ({res1_size}字节)，可能是瓦片集")
        print(f"\n资源成对出现:")
        for pair_idx in range(0, min(10, len(offsets1)), 2):
            if pair_idx + 1 < len(offsets1):
                size0 = offsets1[pair_idx+1] - offsets1[pair_idx]
            else:
                size0 = len(data) - offsets1[pair_idx]
            
            if pair_idx + 2 < len(offsets1):
                size1 = offsets1[pair_idx+2] - offsets1[pair_idx+1]
            else:
                size1 = len(data) - offsets1[pair_idx+1]
            
            terrain_set_id = pair_idx // 2
            print(f"  terrain_set_id={terrain_set_id}:")
            print(f"    资源{pair_idx} (调色板): {size0} 字节")
            print(f"    资源{pair_idx+1} (瓦片集): {size1} 字节")
            
            # 分析调色板前6字节
            res0_data = data[offsets1[pair_idx]:offsets1[pair_idx]+min(768, size0)]
            if len(res0_data) >= 6:
                print(f"    调色板前3个颜色:")
                for c in range(min(3, len(res0_data)//3)):
                    r, g, b = res0_data[c*3], res0_data[c*3+1], res0_data[c*3+2]
                    print(f"      [{c}] RGB({r}, {g}, {b})")