#!/usr/bin/env python3
"""
重新解析res78的完整结构。
尝试找出正确的音频数据起始位置和大小。
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
    
    print(f"Res78: {len(raw)} bytes")
    print(f"\n前64字节hex:")
    for i in range(0, 64, 16):
        hex_str = raw[i:i+16].hex(' ')
        print(f"  {i:04x}: {hex_str}")
    
    print(f"\n--- 解析尝试 ---")
    
    # 方式1: 假设结构是 [4字节头][offset表][数据]
    # count1=2 可能是某种标志, count2=2 是偏移表项数
    c1, c2 = struct.unpack_from('<HH', raw, 0)
    print(f"count1={c1}, count2={c2}")
    
    # 读取偏移表 (从字节4开始, 每项4字节)
    for i in range(c2):
        pos = 4 + i * 4
        val = struct.unpack_from('<I', raw, pos)[0]
        print(f"  offset[{i}] at byte {pos}: 0x{val:x} ({val})")
    
    # 方式2: 假设从字节12开始还有更多信息
    val12 = struct.unpack_from('<I', raw, 12)[0]
    print(f"  bytes 12-15 as uint32: 0x{val12:x} ({val12})")
    
    # 方式3: 检查是否有样本大小信息
    # 如果 count1=2 表示2个样本, 那么应该有4个偏移值
    # 但只找到2个, 所以可能结构不同
    
    # 方式4: 尝试将字节12-15解释为样本大小
    sample_size = val12  # 6359
    print(f"\n假设样本大小 = {sample_size}")
    print(f"  如果从偏移16开始: 16 + {sample_size} = {16 + sample_size}")
    print(f"  资源总大小: {len(raw)}")
    print(f"  剩余: {len(raw) - 16 - sample_size} bytes")
    
    # 方式5: 检查从不同偏移开始的音频数据统计
    print(f"\n--- 不同偏移的数据统计 ---")
    for start in [0, 4, 8, 12, 16, 20, 24, 32]:
        if start + 100 > len(raw):
            break
        sample = raw[start:start+100]
        print(f"  从偏移{start:2d}: {sample[:16].hex(' ')}")
    
    # 方式6: 尝试找出数据中的模式
    # 如果样本大小是6359, 检查偏移16+6359=6375处的数据
    if 6375 < len(raw):
        print(f"\n在偏移6375处: {raw[6375:min(6375+32, len(raw))].hex(' ')}")
    
    # 方式7: 检查res9的头部结构进行对比
    print(f"\n--- 对比res9结构 ---")
    res9_start = offsets[9]
    res9_end = offsets[10] if 10 < len(offsets) else len(data)
    res9 = data[res9_start:res9_end]
    print(f"res9: {len(res9)} bytes")
    print(f"前32字节: {res9[:32].hex(' ')}")
    c1_9 = struct.unpack_from('<H', res9, 0)[0]
    c2_9 = struct.unpack_from('<H', res9, 2)[0]
    print(f"res9 count1={c1_9}, count2={c2_9}")


if __name__ == "__main__":
    main()
