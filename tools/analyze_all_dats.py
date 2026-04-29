#!/usr/bin/env python3
"""完整分析所有DAT文件的资源结构"""
import struct
from pathlib import Path

GAME_DIR = Path(__file__).parent.parent / "game"

def analyze_dat(filename):
    filepath = GAME_DIR / filename
    if not filepath.exists():
        print(f"[SKIP] {filename} 不存在")
        return
    
    with open(filepath, 'rb') as f:
        data = f.read()
    
    print(f"\n{'='*70}")
    print(f"分析 {filename} ({len(data)} 字节)")
    print(f"{'='*70}")
    print(f"魔数: {data[:6]}")
    
    # 解析资源偏移表（格式2：无计数）
    offsets = []
    pos = 6
    while pos < len(data) - 4:
        offset = struct.unpack_from("<I", data, pos)[0]
        if offset > pos and offset < len(data):
            offsets.append(offset)
        else:
            break
        pos += 4
    
    print(f"资源数量: {len(offsets)}")
    
    # 分析前20个资源
    for i, offset in enumerate(offsets[:20]):
        if i + 1 < len(offsets):
            size = offsets[i+1] - offset
        else:
            size = len(data) - offset
        
        res_data = data[offset:min(offset+32, len(data))]
        
        # 特殊标记
        marker = ""
        if i == 0 and filename == "FDSHAP.DAT":
            marker = " <- [地图0调色板]"
        elif i == 1 and filename == "FDSHAP.DAT":
            marker = " <- [地图0瓦片集]"
        elif i % 2 == 0 and filename == "FDSHAP.DAT":
            marker = f" <- [调色板#{i//2}]"
        elif i % 2 == 1 and filename == "FDSHAP.DAT":
            marker = f" <- [瓦片集#{(i-1)//2}]"
        
        if size <= 1024:
            print(f"  资源#{i:2d}: offset=0x{offset:06x}, size={size:5d}{marker}")
            print(f"    数据: {res_data.hex(' ')}")
        else:
            print(f"  资源#{i:2d}: offset=0x{offset:06x}, size={size:5d}{marker}")
    
    # 重点分析资源0和1
    if len(offsets) >= 2:
        res0_size = offsets[1] - offsets[0]
        res1_size = offsets[2] - offsets[1] if len(offsets) > 2 else len(data) - offsets[1]
        
        print(f"\n重点分析:")
        print(f"  资源0: {res0_size} 字节")
        print(f"  资源1: {res1_size} 字节")
        
        if filename == "FDSHAP.DAT":
            # 分析资源0是否是调色板
            res0_data = data[offsets[0]:offsets[0]+res0_size]
            unique_bytes = len(set(res0_data))
            max_byte = max(res0_data)
            
            if res0_size == 768:
                print(f"  -> 资源0是标准调色板 (768字节)")
                print(f"  -> 颜色示例:")
                for c in range(5):
                    r, g, b = res0_data[c*3], res0_data[c*3+1], res0_data[c*3+2]
                    print(f"     [{c}] RGB({r}, {g}, {b})")
            elif res0_size == 1200:
                print(f"  -> 资源0大小1200字节（不是标准调色板）")
                print(f"     唯一字节: {unique_bytes}, 最大值: {max_byte}")
                print(f"     前64字节: {res0_data[:64].hex(' ')}")
            else:
                print(f"  -> 资源0大小: {res0_size} 字节")

if __name__ == "__main__":
    for f in ["FDSHAP.DAT", "FDFIELD.DAT", "FDOTHER.DAT"]:
        analyze_dat(f)
