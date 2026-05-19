#!/usr/bin/env python3
"""
智能分析FDOTHER.DAT索引1的数据结构
识别不同的数据区域和模式
"""
import struct
import os

def hex_dump(data, offset=0, length=None):
    if length is None:
        length = len(data)
    for i in range(0, min(length, len(data)), 16):
        chunk = data[i:i+16]
        hex_str = ' '.join(f'{b:02X}' for b in chunk)
        ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in chunk)
        print(f'  {offset+i:06X}: {hex_str:<48s} {ascii_str}')

def analyze_index1_smart():
    filepath = 'd:/workspace/fd2_dat_freebuff/game/FDOTHER.DAT'
    if not os.path.exists(filepath):
        print(f"错误: 找不到文件 {filepath}")
        return
    
    with open(filepath, 'rb') as f:
        data = f.read()
    
    print("=" * 80)
    print("FDOTHER.DAT 索引1 智能分析")
    print("=" * 80)
    
    # 找到索引1的偏移
    idx1_offset = struct.unpack('<I', data[10 + 1*4:10 + 1*4 + 4])[0]
    idx1_next_offset = struct.unpack('<I', data[10 + 2*4:10 + 2*4 + 4])[0]
    idx1_size = idx1_next_offset - idx1_offset
    
    print(f"索引1偏移: 0x{idx1_offset:06X}, 大小: {idx1_size}")
    
    # 读取索引1的数据
    idx1_data = data[idx1_offset:idx1_next_offset]
    
    print(f"\n" + "=" * 80)
    print("数据结构分析")
    print("=" * 80)
    
    # 区域1: 前0x46字节 - 4字节偏移表
    print(f"\n区域1: 偏移0x00-0x44 (69字节)")
    print(f"  这是4字节小端偏移表，包含17个条目:")
    for i in range(18):
        offset_val = struct.unpack('<I', idx1_data[i*4:i*4+4])[0]
        if i > 0:
            prev_offset = struct.unpack('<I', idx1_data[(i-1)*4:(i-1)*4+4])[0]
            size = offset_val - prev_offset
            print(f"  [{i:2d}] 0x{offset_val:08X} (差值: {size})")
        else:
            print(f"  [{i:2d}] 0x{offset_val:08X}")
    
    # 区域2: 从0x46开始
    print(f"\n区域2: 偏移0x46之后")
    print(f"  分析模式变化...")
    
    # 查找模式变化的位置
    print(f"\n查找从规则模式到不规则模式的转变点:")
    for i in range(0, 300, 2):
        table_offset = 0x46 + i
        if table_offset + 2 <= len(idx1_data):
            val = struct.unpack('<H', idx1_data[table_offset:table_offset+2])[0]
            # 检查是否还是规则的0和非零交替模式
            if i > 0:
                prev_offset = 0x46 + (i-2)
                prev_val = struct.unpack('<H', idx1_data[prev_offset:prev_offset+2])[0]
                
                # 如果模式不再是0和非零交替
                if i % 4 == 0 and val != 0:  # 偶数位置应该是0
                    print(f"  模式变化在索引{i}: 0x{table_offset:04X} = 0x{val:04X}")
                    break
    
    # 分析资源ID 201, 205, 514, 549, 550
    print(f"\n" + "=" * 80)
    print("目标资源ID内容分析")
    print("=" * 80)
    
    target_ids = [201, 205, 514, 549, 550]
    
    for rid in target_ids:
        print(f"\n--- 资源ID {rid} ---")
        
        # 直接查找该ID在数据中的位置
        # 假设资源ID映射到某种数据结构
        table_offset = 0x46 + rid * 2
        
        if table_offset >= len(idx1_data):
            print(f"  超出数据范围!")
            continue
        
        val = struct.unpack('<H', idx1_data[table_offset:table_offset+2])[0]
        print(f"  位置0x{table_offset:04X}: 0x{val:04X} ({val})")
        
        # 检查这个值是否是偏移量
        if val < len(idx1_data):
            # 显示该位置的内容
            print(f"  数据内容 (从偏移0x{val:04X}开始):")
            hex_dump(idx1_data, val, 64)
            
            # 尝试识别数据类型
            chunk = idx1_data[val:val+64]
            if all(b == 0 for b in chunk[:64]):
                print(f"  -> 全零数据块")
            elif chunk[:6] == b'LLLLLL':
                print(f"  -> 嵌套DAT文件")
            elif val >= 0x46 and val < 0x100:
                print(f"  -> 可能是内部偏移表引用")
            else:
                print(f"  -> 未知数据类型")
    
    # 额外分析：查找所有非零值的位置
    print(f"\n" + "=" * 80)
    print("完整数据结构映射")
    print("=" * 80)
    
    print(f"\n所有非零2字节值的位置:")
    for i in range(0, min(1000, len(idx1_data) - 1), 2):
        val = struct.unpack('<H', idx1_data[i:i+2])[0]
        if val != 0 and val < len(idx1_data):
            if i < 0x46 or i > 0x200:  # 跳过中间的规则模式
                print(f"  偏移0x{i:04X}: 0x{val:04X}")

if __name__ == '__main__':
    analyze_index1_smart()
