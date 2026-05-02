#!/usr/bin/env python3
"""
深入分析res78的前16字节元数据。
"""

import struct
from pathlib import Path

def main():
    with open("game/FDOTHER.DAT", "rb") as f:
        data = f.read()
    
    count = struct.unpack_from('<I', data, 6)[0]
    offsets = []
    for i in range(count):
        off = struct.unpack_from('<I', data, 10 + i * 4)[0]
        offsets.append(off)
    
    res_idx = 78
    res_start = offsets[res_idx]
    res_end = offsets[res_idx + 1] if res_idx + 1 < len(offsets) else len(data)
    raw = data[res_start:res_end]
    
    print(f"Res78 total size: {len(raw)} bytes")
    print(f"\nFirst 32 bytes (hex + ascii):")
    for i in range(0, min(32, len(raw)), 16):
        hex_str = raw[i:i+16].hex(' ')
        ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in raw[i:i+16])
        print(f"  {i:04x}: {hex_str:<47s}  {ascii_str}")
    
    print(f"\n--- 逐字节分析 ---")
    for i in range(min(16, len(raw))):
        b = raw[i]
        print(f"  byte[{i:2d}] = 0x{b:02x} ({b:3d}) '{chr(b) if 32 <= b < 127 else '.'}'")
    
    print(f"\n--- 尝试不同解析方式 ---")
    
    # 方式1: 4字节 count1, count2, offset_count, 保留
    c1 = struct.unpack_from('<H', raw, 0)[0]
    c2 = struct.unpack_from('<H', raw, 2)[0]
    print(f"  方式1: count1={c1}, count2={c2}")
    
    # 方式2: 全部当作int16
    vals16 = []
    for i in range(0, 16, 2):
        vals16.append(struct.unpack_from('<H', raw, i)[0])
    print(f"  方式2: int16数组: {vals16}")
    
    # 方式3: 全部当作int32
    vals32 = []
    for i in range(0, 16, 4):
        vals32.append(struct.unpack_from('<I', raw, i)[0])
    print(f"  方式3: int32数组: {vals32}")
    
    # 方式4: 检查是否有常见音频格式标记
    print(f"\n--- 检查标记 ---")
    if raw[:4] == b'RIFF': print("  RIFF标记")
    if raw[:2] == b'LL': print("  LL标记")
    if raw[:4] == b'LMI1': print("  LMI1标记 (Miles Sound System)")
    
    # 方式5: 检查样本数据的统计特征
    print(f"\n--- 从不同偏移开始的样本数据统计 ---")
    for start in [0, 4, 8, 12, 16, 20, 24, 32]:
        if start + 100 > len(raw):
            break
        sample = raw[start:]
        nonzero = sum(1 for b in sample if b != 0)
        zero = sum(1 for b in sample if b == 0)
        max_val = max(sample)
        min_val = min(sample)
        avg_val = sum(sample) / len(sample)
        print(f"  从偏移{start:2d}开始: {len(sample):5d}字节, 非零={nonzero:5d}({nonzero/len(sample)*100:.1f}%), "
              f"最大={max_val:3d}, 最小={min_val:3d}, 平均={avg_val:.1f}")
    
    # 方式6: 检查样本数据的字节分布
    print(f"\n--- 从偏移16开始的字节值分布 ---")
    sample_data = raw[16:]
    hist = [0] * 16
    for b in sample_data:
        hist[b >> 4] += 1
    for i in range(16):
        bar = '#' * (hist[i] // 100)
        print(f"  {i*16:3d}-{i*16+15:3d}: {hist[i]:5d} {bar}")


if __name__ == "__main__":
    main()
