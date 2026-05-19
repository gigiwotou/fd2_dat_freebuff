import struct
import sys

def analyze_fdother_structure(filename):
    with open(filename, 'rb') as f:
        data = f.read()
    
    print(f'文件总大小: {len(data)} bytes (0x{len(data):X})')
    print()
    
    # 查看文件头部结构
    print('=== 文件头部 (前0x100字节) ===')
    for i in range(0, 0x100, 16):
        print(f'0x{i:04X}: ', end='')
        for j in range(16):
            if i + j < len(data):
                print(f'{data[i+j]:02X} ', end='')
            else:
                print('   ', end='')
        print('  ', end='')
        for j in range(16):
            if i + j < len(data):
                c = data[i+j]
                print(chr(c) if 32 <= c < 127 else '.', end='')
        print()
    
    print()
    
    # 分析索引表2的结构
    print('=== 分析索引表2 (2字节偏移表) ===')
    print('索引表起始位置: 0x0046')
    
    # 查看前100个资源ID
    print('资源ID | 偏移值   | 计算大小  | 实际内容前4字节')
    print('-------|----------|-----------|----------------')
    
    prev_off = None
    for rid in range(100):
        table_off = 0x46 + rid * 2
        if table_off + 2 > len(data):
            break
            
        res_off = struct.unpack('<H', data[table_off:table_off+2])[0]
        
        if prev_off is not None:
            calc_size = res_off - prev_off
        else:
            calc_size = 0
        
        # 查看资源内容
        content_preview = ''
        if res_off < len(data):
            content_preview = ' '.join(f'{data[res_off+i]:02X}' for i in range(min(4, len(data)-res_off)))
        
        print(f'{rid:6d} | 0x{res_off:06X} | {calc_size:8d}  | {content_preview}')
        
        prev_off = res_off

if __name__ == '__main__':
    if len(sys.argv) > 1:
        analyze_fdother_structure(sys.argv[1])
    else:
        print('Usage: python analyze_fdother_structure.py <path_to_FDOTHER.DAT>')
