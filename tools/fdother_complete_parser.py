"""
FDOTHER.DAT 完整解析脚本 - 严格按MCP汇编代码实现
根据sub_111BA函数逻辑，解析所有子资源
"""

import struct
import os

def dump_hex(data, offset=0, length=64):
    """输出十六进制数据"""
    end = min(offset + length, len(data))
    result = []
    for i in range(offset, end, 16):
        hex_str = ' '.join(f'{b:02X}' for b in data[i:min(i+16, end)])
        result.append(f'  {i:04X}: {hex_str}')
    return '\n'.join(result)

def analyze_fdother():
    """解析FDOTHER.DAT所有资源"""
    
    filepath = 'game/FDOTHER.DAT'
    output_dir = 'output/fdother_complete_parse'
    os.makedirs(output_dir, exist_ok=True)
    
    with open(filepath, 'rb') as f:
        data = f.read()
    
    file_size = len(data)
    print(f'FDOTHER.DAT 文件大小: {file_size} 字节 ({file_size/1024:.1f} KB)')
    print(f'文件头部6字节: {dump_hex(data, 0, 6)}')
    
    # 检查文件魔数
    magic = data[0:6]
    print(f'魔数: {magic}')
    
    # 根据sub_111BA分析：
    # fseek(fp, 4 * resource_index + 6, SEEK_SET)
    # 索引表从偏移6开始，每项4字节（仅包含起始偏移）
    # 资源大小 = 下一个偏移 - 当前偏移
    
    # 查找索引表结束位置
    # 索引表起始位置：6
    # 需要找到资源数据开始的位置
    
    # 读取可能的索引数量
    # 先尝试读取头部可能的计数信息
    
    print('\n=== 分析索引表结构 ===')
    
    # 方法1：假设前4字节（偏移6-9）是资源数量
    potential_count = struct.unpack('<I', data[6:10])[0]
    print(f'假设偏移6处是资源数量: {potential_count}')
    
    # 方法2：扫描索引表，找到第一个偏移指向文件末尾之后的位置
    print('\n扫描索引表，查找有效资源...')
    
    offsets = []
    max_index = 0
    
    # 尝试不同的索引表起始位置
    for table_start in [6, 10]:
        print(f'\n--- 尝试索引表起始位置: {table_start} ---')
        
        # 读取前100个可能的索引
        for i in range(150):
            offset_addr = table_start + i * 4
            if offset_addr + 4 > file_size:
                break
            
            offset_val = struct.unpack('<I', data[offset_addr:offset_addr+4])[0]
            
            if offset_val > file_size:
                print(f'索引 {i}: 偏移 {offset_val} (0x{offset_val:08X}) - 超出文件大小，停止')
                break
            
            if offset_val == 0:
                print(f'索引 {i}: 偏移 0 - 空')
                continue
            
            offsets.append((i, offset_val))
            max_index = max(max_index, i)
        
        if offsets:
            print(f'找到 {len(offsets)} 个有效索引')
            # 打印前30个
            for idx, off in offsets[:30]:
                # 读取该位置的前几个字节
                if off + 20 <= file_size:
                    preview = dump_hex(data, off, 20)
                    print(f'索引 {idx:3d}: 偏移 {off:7d} (0x{off:06X})\n{preview}')
                else:
                    print(f'索引 {idx:3d}: 偏移 {off:7d} (0x{off:06X}) - 数据不足')
            
            # 计算资源大小
            print('\n=== 资源大小分析 ===')
            for i in range(len(offsets) - 1):
                idx1, off1 = offsets[i]
                idx2, off2 = offsets[i + 1]
                size = off2 - off1
                print(f'资源 {idx1}: 偏移 {off1} - {off2}, 大小 {size} 字节')
            
            # 最后一个资源
            if offsets:
                last_idx, last_off = offsets[-1]
                last_size = file_size - last_off
                print(f'资源 {last_idx}: 偏移 {last_off} - {file_size}, 大小 {last_size} 字节')
            
            break

if __name__ == '__main__':
    analyze_fdother()
