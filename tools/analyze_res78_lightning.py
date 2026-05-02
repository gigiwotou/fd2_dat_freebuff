#!/usr/bin/env python3
"""
分析 res78 闪电音效的数据结构。
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
    start = offsets[res_idx]
    end = offsets[res_idx + 1] if res_idx + 1 < len(offsets) else len(data)
    raw = data[start:end]
    
    print(f"Resource [{res_idx}] - {len(raw)} bytes")
    print(f"\nFirst 128 bytes (hex):")
    for i in range(0, min(128, len(raw)), 16):
        hex_str = raw[i:i+16].hex(' ')
        ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in raw[i:i+16])
        print(f"  {i:04x}: {hex_str:<47s}  {ascii_str}")
    
    print(f"\n--- 尝试解析头部结构 ---")
    
    print(f"\n前4字节: {raw[:4].hex()}")
    val1 = struct.unpack_from('<H', raw, 0)[0]
    val2 = struct.unpack_from('<H', raw, 2)[0]
    print(f"  前2字节 (uint16): {val1} (0x{val1:x})")
    print(f"  2-4字节 (uint16): {val2} (0x{val2:x})")
    
    if val1 < 50 and val2 < 50 and val1 > 0:
        print(f"\n  假设: val1={val1} 是偏移表项数, val2={val2} 是样本数")
        offset_table_start = 4
        print(f"  偏移表起始位置: {offset_table_start}")
        
        offsets_table = []
        for i in range(val2):
            off_pos = offset_table_start + i * 4
            if off_pos + 4 > len(raw):
                break
            off_val = struct.unpack_from('<I', raw, off_pos)[0]
            offsets_table.append(off_val)
            print(f"    偏移[{i}]: 0x{off_val:x} ({off_val})")
        
        print(f"\n  --- 样本内容分析 ---")
        for i in range(len(offsets_table) - 1):
            sample_start = offsets_table[i]
            sample_end = offsets_table[i + 1]
            sample_data = raw[sample_start:sample_end]
            print(f"  样本[{i}]: 偏移 0x{sample_start:x} - 0x{sample_end:x}, 大小 {len(sample_data)} bytes")
            if len(sample_data) > 0:
                print(f"    前32字节: {sample_data[:32].hex()}")
    
    print(f"\n--- 检查是否有 LLLLLL 格式 ---")
    if raw[:2] == b'LL':
        print("  找到 LL 标记")
        ll_count = struct.unpack_from('<H', raw, 2)[0]
        print(f"  LL count: {ll_count}")
    
    print(f"\n--- 检查是否有固定模式 ---")
    for pos in range(0, min(64, len(raw))):
        if raw[pos:pos+2] == b'\x00\x00':
            print(f"  位置 {pos}: 找到 0x0000")
    
    print(f"\n--- 统计分析 ---")
    nonzero_count = sum(1 for b in raw[4:] if b != 0)
    zero_count = sum(1 for b in raw[4:] if b == 0)
    print(f"  从偏移4开始: 非零字节={nonzero_count}, 零字节={zero_count}")
    print(f"  非零比例: {nonzero_count/(nonzero_count+zero_count)*100:.1f}%")

if __name__ == "__main__":
    main()
