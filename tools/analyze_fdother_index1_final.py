#!/usr/bin/env python3
"""
分析FDOTHER.DAT索引1的完整数据结构
特别关注资源ID 201/205/514/549/550
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

def analyze_index1():
    filepath = 'd:/workspace/fd2_dat_freebuff/game/FDOTHER.DAT'
    if not os.path.exists(filepath):
        print(f"错误: 找不到文件 {filepath}")
        return
    
    with open(filepath, 'rb') as f:
        data = f.read()
    
    print("=" * 80)
    print("FDOTHER.DAT 索引1 数据结构分析")
    print("=" * 80)
    
    # 解析主文件头
    magic = data[0:6]
    res_count = struct.unpack('<H', data[6:8])[0]
    
    print(f"\n主文件:")
    print(f"  魔数: {magic}")
    print(f"  资源数量: {res_count}")
    
    # 找到索引1的偏移
    offset_table_start = 10
    idx1_offset = struct.unpack('<I', data[offset_table_start + 1*4:offset_table_start + 1*4 + 4])[0]
    idx1_next_offset = struct.unpack('<I', data[offset_table_start + 2*4:offset_table_start + 2*4 + 4])[0]
    idx1_size = idx1_next_offset - idx1_offset
    
    print(f"\n索引1:")
    print(f"  偏移: 0x{idx1_offset:06X} ({idx1_offset})")
    print(f"  下一个索引偏移: 0x{idx1_next_offset:06X} ({idx1_next_offset})")
    print(f"  大小: {idx1_size} 字节")
    
    # 读取索引1的数据
    idx1_data = data[idx1_offset:idx1_next_offset]
    
    print(f"\n" + "=" * 80)
    print("索引1 头部分析")
    print("=" * 80)
    
    print(f"\n前70字节 (可能是偏移表):")
    hex_dump(idx1_data, 0, 70)
    
    # 分析前0x46字节
    print(f"\n前0x46字节分析:")
    for i in range(0, 0x46, 4):
        val = struct.unpack('<I', idx1_data[i:i+4])[0]
        print(f"  偏移0x{i:02X}: 0x{val:08X} ({val})")
    
    # 从0x46开始可能是2字节的偏移表
    print(f"\n从0x46开始的2字节偏移表 (前30项):")
    for i in range(30):
        table_offset = 0x46 + i * 2
        if table_offset + 2 <= len(idx1_data):
            val = struct.unpack('<H', idx1_data[table_offset:table_offset+2])[0]
            print(f"  [{i:3d}] 0x{table_offset:04X} = 0x{val:04X} ({val})")
    
    print(f"\n" + "=" * 80)
    print("目标资源ID分析")
    print("=" * 80)
    
    for rid in [201, 205, 514, 549, 550]:
        print(f"\n--- 资源ID {rid} ---")
        
        table_offset = 0x46 + rid * 2
        if table_offset + 2 > len(idx1_data):
            print(f"  超出范围!")
            continue
        
        res_offset = struct.unpack('<H', idx1_data[table_offset:table_offset+2])[0]
        print(f"  表中位置: 0x{table_offset:04X}")
        print(f"  资源偏移: 0x{res_offset:04X} ({res_offset})")
        
        # 获取下一个偏移来计算大小
        next_table_offset = 0x46 + (rid + 1) * 2
        if next_table_offset + 2 <= len(idx1_data):
            next_res_offset = struct.unpack('<H', idx1_data[next_table_offset:next_table_offset+2])[0]
            res_size = next_res_offset - res_offset
            print(f"  下一个偏移: 0x{next_res_offset:04X}")
            print(f"  资源大小: {res_size} 字节")
        else:
            res_size = len(idx1_data) - res_offset
            print(f"  资源大小: {res_size} 字节 (到末尾)")
        
        # 检查资源数据
        if res_offset < len(idx1_data) and res_size > 0:
            actual_size = min(res_size, len(idx1_data) - res_offset)
            res_data = idx1_data[res_offset:res_offset + actual_size]
            
            print(f"\n  资源数据前128字节:")
            hex_dump(res_data, res_offset, min(128, actual_size))
            
            # 保存资源
            output_dir = 'd:/workspace/fd2_dat_freebuff/output'
            os.makedirs(output_dir, exist_ok=True)
            output_file = os.path.join(output_dir, f'idx1_resource_{rid}.bin')
            with open(output_file, 'wb') as f:
                f.write(res_data)
            print(f"\n  已保存到: {output_file}")
            
            # 尝试识别资源类型
            if actual_size == 768:
                print(f"  类型推测: 调色板 (768字节)")
            elif res_data[:6] == b'LLLLLL':
                nested_count = struct.unpack('<H', res_data[6:8])[0]
                print(f"  类型推测: 嵌套DAT ({nested_count}个子资源)")
            elif actual_size >= 4:
                width = struct.unpack('<H', res_data[0:2])[0]
                height = struct.unpack('<H', res_data[2:4])[0]
                if 0 < width <= 640 and 0 < height <= 480:
                    print(f"  类型推测: RLE图像 ({width}x{height})")
                else:
                    print(f"  类型推测: 未知二进制数据")
        else:
            print(f"  无有效数据!")

if __name__ == '__main__':
    analyze_index1()
