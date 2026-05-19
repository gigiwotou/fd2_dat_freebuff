#!/usr/bin/env python3
"""
检查FDOTHER.DAT主索引表中的资源201和205
"""

import struct
from pathlib import Path

GAME_DIR = Path("game")
DAT_MAGIC = b"LLLLLL"

def main():
    fdother_path = GAME_DIR / "FDOTHER.DAT"
    if not fdother_path.exists():
        print(f"错误: 找不到 {fdother_path}")
        return
    
    data = fdother_path.read_bytes()
    res_count = struct.unpack_from("<I", data, 6)[0]
    print(f"FDOTHER.DAT: 共 {res_count} 个资源\n")
    
    # 解析索引表
    offsets = []
    for i in range(res_count):
        offsets.append(struct.unpack_from("<I", data, 10 + i*4)[0])
    
    # 检查资源201和205
    for idx in [201, 205]:
        print(f"\n{'='*60}")
        print(f"检查主索引 {idx}:")
        print(f"{'='*60}")
        
        if idx >= len(offsets):
            print(f"  索引{idx}超出范围（最大索引{len(offsets)-1}）")
            continue
        
        s = offsets[idx]
        e = offsets[idx+1] if idx+1 < len(offsets) else len(data)
        sz = e - s
        
        print(f"  起始偏移: {s} (0x{s:X})")
        print(f"  结束偏移: {e} (0x{e:X})")
        print(f"  大小: {sz} 字节")
        
        if sz >= 4:
            w, h = struct.unpack_from("<HH", data, s)
            print(f"  可能的图像尺寸: {w}x{h}")
            
            # 显示hex头
            hex_header = data[s:s+32].hex()
            print(f"  前32字节: {hex_header}")
            
            # 判断类型
            if data[s:s+6] == DAT_MAGIC:
                nested_count = struct.unpack_from("<I", data, s+6)[0]
                print(f"  类型: 嵌套DAT ({nested_count}个子资源)")
            elif 0 < w <= 640 and 0 < h <= 480:
                print(f"  类型: RLE图像")
                
                # 计算压缩比
                if sz > 4:
                    uncompressed = w * h
                    compressed = sz - 4
                    ratio = uncompressed / compressed if compressed > 0 else 0
                    print(f"  未压缩: {uncompressed} 字节")
                    print(f"  压缩后: {compressed} 字节")
                    print(f"  压缩比: {ratio:.2f}:1")
            else:
                print(f"  类型: 数据块")

if __name__ == "__main__":
    main()
