#!/usr/bin/env python3
"""提取FDOTHER.DAT索引1的资源ID 1-18的图形数据"""
import struct
import os

def extract_resources():
    fdother_path = os.path.join(os.path.dirname(__file__), '..', 'game', 'FDOTHER.DAT')
    output_dir = os.path.join(os.path.dirname(__file__), '..', 'output')
    os.makedirs(output_dir, exist_ok=True)

    with open(fdother_path, 'rb') as f:
        data = f.read()

    # 读取索引1的位置
    idx1_offset = struct.unpack('<I', data[10 + 1*4:10 + 1*4 + 4])[0]
    idx1_next_offset = struct.unpack('<I', data[10 + 2*4:10 + 2*4 + 4])[0]
    idx1_size = idx1_next_offset - idx1_offset

    print(f"索引1信息:")
    print(f"  文件偏移: 0x{idx1_offset:06X}")
    print(f"  数据大小: {idx1_size} 字节")

    # 读取索引1的完整数据
    idx1_data = data[idx1_offset:idx1_next_offset]

    # 解析前0x46字节的4字节偏移表
    print(f"\n4字节偏移表 (前0x46字节):")
    print("-" * 60)

    offset_table = []
    for i in range(19):  # 读取0-18共19个条目
        pos = i * 4
        if pos + 4 > len(idx1_data):
            break

        offset_val = struct.unpack('<I', idx1_data[pos:pos+4])[0]
        offset_table.append(offset_val)

        if i > 0:
            prev_offset = offset_table[i-1]
            size = offset_val - prev_offset
            print(f"  ID [{i:2d}]: 偏移=0x{offset_val:06X} ({offset_val:6d}), 大小={size} 字节")
        else:
            print(f"  ID [{i:2d}]: 偏移=0x{offset_val:06X} ({offset_val:6d})")

    # 提取资源ID 1-18的数据
    print(f"\n提取资源ID 1-18:")
    print("=" * 60)

    for res_id in range(1, 19):
        if res_id >= len(offset_table):
            break

        res_start = offset_table[res_id]

        # 计算资源大小
        if res_id + 1 < len(offset_table):
            res_end = offset_table[res_id + 1]
        else:
            res_end = len(idx1_data)

        res_size = res_end - res_start

        if res_size <= 0:
            print(f"  ID {res_id:2d}: 大小异常 ({res_size}), 跳过")
            continue

        # 提取数据
        res_data = idx1_data[res_start:res_end]

        # 解析图形数据头部
        width = 0
        height = 0
        if res_size >= 4:
            width = struct.unpack('<H', res_data[0:2])[0]
            height = struct.unpack('<H', res_data[2:4])[0]

        # 保存为二进制文件
        output_file = os.path.join(output_dir, f'idx1_resource_{res_id:02d}.bin')
        with open(output_file, 'wb') as out:
            out.write(res_data)

        print(f"  ID {res_id:2d}: 偏移=0x{res_start:04X}, 大小={res_size:4d} 字节, "
              f"可能尺寸: {width:3d}x{height:3d} -> {output_file}")

    print(f"\n完成! 资源已保存到: {output_dir}")

if __name__ == '__main__':
    extract_resources()
