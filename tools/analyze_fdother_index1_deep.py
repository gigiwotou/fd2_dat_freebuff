#!/usr/bin/env python3
"""
深度分析FDOTHER.DAT索引1的数据结构
找出正确的资源偏移表格式
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

def analyze_index1_deep():
    filepath = 'd:/workspace/fd2_dat_freebuff/game/FDOTHER.DAT'
    if not os.path.exists(filepath):
        print(f"错误: 找不到文件 {filepath}")
        return
    
    with open(filepath, 'rb') as f:
        data = f.read()
    
    print("=" * 80)
    print("FDOTHER.DAT 索引1 深度分析")
    print("=" * 80)
    
    # 解析主文件头
    res_count = struct.unpack('<H', data[6:8])[0]
    print(f"资源数量: {res_count}")
    
    # 找到索引1的偏移
    offset_table_start = 10
    idx1_offset = struct.unpack('<I', data[offset_table_start + 1*4:offset_table_start + 1*4 + 4])[0]
    idx1_next_offset = struct.unpack('<I', data[offset_table_start + 2*4:offset_table_start + 2*4 + 4])[0]
    idx1_size = idx1_next_offset - idx1_offset
    
    print(f"索引1偏移: 0x{idx1_offset:06X}, 大小: {idx1_size}")
    
    # 读取索引1的数据
    idx1_data = data[idx1_offset:idx1_next_offset]
    
    print(f"\n索引1前100字节完整分析:")
    hex_dump(idx1_data, 0, 100)
    
    # 分析结构
    # 前0x46字节 (70字节): 可能是某种4字节的偏移表
    # 0x00-0x44: 18个4字节条目 = 72字节? 不对
    # 让我们仔细分析
    
    print(f"\n前70字节按4字节分组:")
    for i in range(0, 70, 4):
        if i + 4 <= len(idx1_data):
            val = struct.unpack('<I', idx1_data[i:i+4])[0]
            print(f"  偏移0x{i:02X}: 0x{val:08X} ({val})")
    
    # 计算一下：如果前0x46字节是某种表
    # 0x46 = 70字节
    # 70 / 4 = 17.5 -> 不是4字节的整数倍
    # 70 / 2 = 35 -> 可能是2字节的整数倍
    
    print(f"\n从0x46开始的2字节值 (前60项):")
    for i in range(60):
        table_offset = 0x46 + i * 2
        if table_offset + 2 <= len(idx1_data):
            val = struct.unpack('<H', idx1_data[table_offset:table_offset+2])[0]
            if i % 10 == 0:
                print()
            print(f"[{i:3d}]0x{val:04X} ", end='')
    print()
    
    # 寻找有规律的模式
    print(f"\n寻找非零偏移的模式:")
    for i in range(0, 300):
        table_offset = 0x46 + i * 2
        if table_offset + 2 <= len(idx1_data):
            val = struct.unpack('<H', idx1_data[table_offset:table_offset+2])[0]
            if val != 0:
                print(f"  [{i:3d}] 0x{table_offset:04X} = 0x{val:04X} ({val})")
    
    # 检查资源201, 205, 514, 549, 550
    print(f"\n\n目标资源ID分析:")
    for rid in [201, 205, 514, 549, 550]:
        print(f"\n--- 资源ID {rid} ---")
        
        table_offset = 0x46 + rid * 2
        if table_offset + 2 > len(idx1_data):
            print(f"  超出范围! (需要偏移{table_offset}, 总大小{len(idx1_data)})")
            continue
        
        res_offset = struct.unpack('<H', idx1_data[table_offset:table_offset+2])[0]
        print(f"  表中位置: 0x{table_offset:04X}")
        print(f"  资源偏移: 0x{res_offset:04X} ({res_offset})")
        
        # 获取下一个非零偏移
        next_res_offset = None
        for j in range(rid + 1, rid + 100):
            next_table_offset = 0x46 + j * 2
            if next_table_offset + 2 <= len(idx1_data):
                next_val = struct.unpack('<H', idx1_data[next_table_offset:next_table_offset+2])[0]
                if next_val != 0 and next_val > res_offset:
                    next_res_offset = next_val
                    break
        
        if next_res_offset:
            res_size = next_res_offset - res_offset
            print(f"  下一个非零偏移: 0x{next_res_offset:04X}")
            print(f"  资源大小: {res_size} 字节")
            
            # 检查资源数据
            if res_offset < len(idx1_data) and res_size > 0:
                actual_size = min(res_size, len(idx1_data) - res_offset)
                res_data = idx1_data[res_offset:res_offset + actual_size]
                
                print(f"\n  资源数据前96字节:")
                hex_dump(res_data, res_offset, min(96, actual_size))
        else:
            print(f"  未找到下一个非零偏移")

if __name__ == '__main__':
    analyze_index1_deep()
