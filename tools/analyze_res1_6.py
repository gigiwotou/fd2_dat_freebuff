#!/usr/bin/env python3
"""
FD2 资源1-6详细分析
检查资源1-6的实际格式和内容
"""

import struct
from pathlib import Path

GAME_DIR = Path("game")
OUTPUT_DIR = Path("output/menu_verify")

def main():
    fdother_path = GAME_DIR / "FDOTHER.DAT"
    data = fdother_path.read_bytes()
    
    # 读取偏移表
    res_count = struct.unpack_from("<I", data, 6)[0]
    offsets = []
    for i in range(res_count):
        offsets.append(struct.unpack_from("<I", data, 10 + i*4)[0])
    
    print("资源1-6详细分析:")
    print("=" * 60)
    
    for i in range(1, 7):
        start = offsets[i]
        end = offsets[i+1] if i+1 < len(offsets) else len(data)
        res_data = data[start:end]
        
        print(f"\n资源{i}: {len(res_data)} 字节")
        print(f"  前16字节(hex): {res_data[:16].hex()}")
        print(f"  前16字节(ascii): {res_data[:16]}")
        
        # 检查是否有LLLLLL头
        if res_data[:6] == b"LLLLLL":
            inner_count = struct.unpack_from("<I", res_data, 6)[0]
            print(f"  是DAT嵌套! 子资源数: {inner_count}")
            inner_offsets = []
            for j in range(inner_count):
                inner_offsets.append(struct.unpack_from("<I", res_data, 10 + j*4)[0])
            for j in range(inner_count):
                s = inner_offsets[j]
                e = inner_offsets[j+1] if j+1 < len(inner_offsets) else len(res_data)
                print(f"    [{j}] 偏移={s}, 大小={e-s}, 头={res_data[s:s+4].hex()}")
        
        # 检查是否有LMI1头
        if res_data[:4] == b"LMI1":
            print(f"  格式: LMI1")
            if len(res_data) > 8:
                val1, val2 = struct.unpack_from("<HH", res_data, 4)
                print(f"  头后4字节: {val1}, {val2}")
        
        # 检查是否像RLE图像头
        if len(res_data) >= 4:
            w, h = struct.unpack_from("<HH", res_data, 0)
            if 0 < w <= 640 and 0 < h <= 480:
                compressed_size = len(res_data) - 4
                expected_pixels = w * h
                print(f"  可能是RLE图像: {w}x{h}, 压缩数据: {compressed_size}, 预期像素: {expected_pixels}")
        
        # 统计字节分布
        byte_counts = {}
        for b in res_data[:min(100, len(res_data))]:
            byte_counts[b] = byte_counts.get(b, 0) + 1
        top_bytes = sorted(byte_counts.items(), key=lambda x: -x[1])[:5]
        print(f"  前100字节最常见: {[f'0x{b:02x}({c})' for b,c in top_bytes]}")

if __name__ == "__main__":
    main()
