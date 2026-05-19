import struct
import sys

def analyze_fdother_full(filename):
    with open(filename, 'rb') as f:
        data = f.read()
    
    print(f'文件总大小: {len(data)} bytes (0x{len(data):X})')
    print()
    
    # 查看文件头部
    print('=== 文件头部 (前0x200字节) ===')
    for i in range(0, 0x200, 16):
        print(f'0x{i:04X}: ', end='')
        hex_str = ''
        ascii_str = ''
        for j in range(16):
            if i + j < len(data):
                b = data[i+j]
                hex_str += f'{b:02X} '
                ascii_str += chr(b) if 32 <= b < 127 else '.'
        print(f'{hex_str:<48s}  {ascii_str}')
    
    print()
    
    # 尝试解析为不同的结构
    print('=== 尝试解析头部结构 ===')
    
    # 检查是否有魔数或文件头
    magic = data[:4]
    print(f'前4字节: {magic.hex()}')
    
    # 检查是否有嵌套DAT文件标记
    if data[:4] == b'FDAT' or data[:4] == b'DAT\x00':
        print('检测到FDAT/DAT标记')
    
    print()
    
    # 分析201和205资源
    print('=== 详细分析资源201和205 ===')
    
    for rid in [201, 205]:
        table_off = 0x46 + rid * 2
        res_off = struct.unpack('<H', data[table_off:table_off+2])[0]
        next_table_off = 0x46 + (rid + 1) * 2
        next_res_off = struct.unpack('<H', data[next_table_off:next_table_off+2])[0]
        res_size = next_res_off - res_off
        
        print(f'\n资源ID {rid}:')
        print(f'  表位置: 0x{table_off:04X}')
        print(f'  资源偏移: 0x{res_off:06X}')
        print(f'  下一资源偏移: 0x{next_res_off:06X}')
        print(f'  大小: {res_size} bytes')
        
        if res_off < len(data) and res_size > 0:
            print(f'  资源前32字节:')
            for i in range(0, min(32, res_size), 16):
                hex_str = ''
                for j in range(16):
                    if i + j < res_size:
                        hex_str += f'{data[res_off + i + j]:02X} '
                print(f'    {i:4d}: {hex_str}')
            
            # 按2字节解析
            print(f'  按2字节解析 (有符号):')
            for i in range(0, min(40, res_size), 2):
                val_signed = struct.unpack('<h', data[res_off + i:res_off + i + 2])[0]
                val_unsigned = struct.unpack('<H', data[res_off + i:res_off + i + 2])[0]
                print(f'    [{i//2:3d}] = {val_signed:6d} (0x{val_unsigned:04X})')
    
    # 查看资源1的内容 (可能是索引表)
    print('\n=== 分析资源1 (可能是嵌套结构) ===')
    table_off = 0x46 + 1 * 2
    res_off = struct.unpack('<H', data[table_off:table_off+2])[0]
    next_table_off = 0x46 + 2 * 2
    next_res_off = struct.unpack('<H', data[next_table_off:next_table_off+2])[0]
    res_size = next_res_off - res_off
    
    print(f'资源1: 偏移0x{res_off:06X}, 大小{res_size}')
    if res_off < len(data) and res_size > 0:
        print(f'  前64字节:')
        for i in range(0, min(64, res_size), 16):
            hex_str = ''
            for j in range(16):
                if i + j < res_size:
                    hex_str += f'{data[res_off + i + j]:02X} '
            print(f'    {i:4d}: {hex_str}')
        
        # 尝试按4字节解析
        print(f'  按4字节解析 (可能是一个偏移表):')
        for i in range(0, min(64, res_size), 4):
            val = struct.unpack('<I', data[res_off + i:res_off + i + 4])[0]
            print(f'    [{i//4:2d}] = 0x{val:06X} ({val})')

if __name__ == '__main__':
    if len(sys.argv) > 1:
        analyze_fdother_full(sys.argv[1])
    else:
        print('Usage: python analyze_fdother_full.py <path_to_FDOTHER.DAT>')
