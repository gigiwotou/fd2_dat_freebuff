#!/usr/bin/env python3
"""
查找并验证地图调色板数据来源

基于IDA分析的关键发现:
1. FDSHAP.DAT: 资源成对出现 (palette 2*n, tileset 2*n+1)
2. FDOTHER.DAT: 根据地图ID加载不同资源作为调色板
3. 地图0 (n17=0) 不匹配sub_10652的任何case，可能使用默认调色板或硬编码
"""

import struct
from pathlib import Path

GAME_DIR = Path(__file__).parent.parent / "game"

def analyze_file(filename, target_sizes=None):
    """分析DAT文件的资源结构"""
    filepath = GAME_DIR / filename
    if not filepath.exists():
        print(f"[SKIP] {filename} 不存在")
        return
    
    with open(filepath, 'rb') as f:
        data = f.read()
    
    print(f"\n{'='*60}")
    print(f"分析 {filename}")
    print(f"{'='*60}")
    print(f"文件大小: {len(data)} 字节")
    print(f"魔数: {data[:6]}")
    
    # 尝试两种格式
    # 格式1: byte 6有资源计数
    count_fmt1 = struct.unpack_from("<I", data, 6)[0]
    
    # 格式2: 无计数，直接偏移表
    offsets_fmt2 = []
    pos = 6
    while pos < len(data) - 4:
        offset = struct.unpack_from("<I", data, pos)[0]
        if offset > pos and offset < len(data):
            offsets_fmt2.append(offset)
        else:
            break
        pos += 4
    
    print(f"\n格式1 (byte 6计数): {count_fmt1} 个资源")
    print(f"格式2 (无计数): {len(offsets_fmt2)} 个资源")
    
    # 使用格式1
    if count_fmt1 > 0 and count_fmt1 < 200:
        print(f"使用格式1解析")
        offsets = []
        for i in range(count_fmt1):
            offset = struct.unpack_from("<I", data, 10 + i * 4)[0]
            offsets.append(offset)
    else:
        print(f"使用格式2解析")
        offsets = offsets_fmt2
    
    # 分析所有资源
    print(f"\n资源列表:")
    for i, offset in enumerate(offsets):
        if i + 1 < len(offsets):
            size = offsets[i+1] - offset
        else:
            size = len(data) - offset
        
        # 检查是否匹配目标大小
        if target_sizes and size not in target_sizes:
            continue
        
        # 分析资源内容
        res_data = data[offset:min(offset+100, len(data))]
        
        # 检查是否是调色板
        is_palette = False
        if size == 768:
            is_palette = True
            max_val = max(data[offset:offset+size])
            unique_vals = len(set(data[offset:offset+size]))
            print(f"  资源#{i}: offset=0x{offset:06x}, size={size:5d} -> [调色板候选] 值范围0-{max_val}, 唯一值{unique_vals}")
            
            # 打印前几个颜色
            print(f"    颜色示例:")
            for c in range(min(5, 256)):
                r = data[offset + c*3]
                g = data[offset + c*3 + 1]
                b = data[offset + c*3 + 2]
                print(f"      [{c}] RGB({r}, {g}, {b})")
        elif size < 200:
            print(f"  资源#{i}: offset=0x{offset:06x}, size={size:5d} -> {res_data[:20].hex(' ')}")
        else:
            print(f"  资源#{i}: offset=0x{offset:06x}, size={size:5d}")

def main():
    print("查找地图调色板数据来源")
    print("="*60)
    
    # 分析FDSHAP.DAT - 瓦片和调色板
    analyze_file("FDSHAP.DAT", target_sizes=[768, 1200])
    
    # 分析FDOTHER.DAT - 可能包含调色板
    analyze_file("FDOTHER.DAT", target_sizes=[768])
    
    # 分析FDFIELD.DAT - 地图数据（不应该有调色板）
    analyze_file("FDFIELD.DAT", target_sizes=[768])
    
    print("\n" + "="*60)
    print("分析完成")
    print("="*60)

if __name__ == "__main__":
    main()
