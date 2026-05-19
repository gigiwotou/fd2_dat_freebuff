import struct
import sys

def analyze_fdother_resources(filename):
    with open(filename, 'rb') as f:
        data = f.read()
    
    print(f'文件总大小: {len(data)} bytes (0x{len(data):X})')
    print()
    
    # FDOTHER.DAT有2个索引表
    # 索引表1: 4字节偏移 (前0x46字节)
    # 索引表2: 2字节偏移 (从0x46开始)
    
    print('=== 索引表2 (2字节偏移, 从0x46开始) ===')
    print('资源ID | 表位置  | 资源偏移 | 下一偏移 | 大小')
    print('-------|---------|----------|----------|----------')
    
    # 查看我们关心的资源ID
    target_ids = [1, 2, 3, 50, 100, 150, 200, 201, 202, 203, 204, 205, 206, 207, 208, 209, 210,
                  514, 515, 516, 549, 550, 551, 552, 76, 77, 78, 74, 19]
    
    for rid in sorted(set(target_ids)):
        table_off = 0x46 + rid * 2
        if table_off + 2 <= len(data):
            res_off = struct.unpack('<H', data[table_off:table_off+2])[0]
            
            next_table_off = 0x46 + (rid + 1) * 2
            if next_table_off + 2 <= len(data):
                next_res_off = struct.unpack('<H', data[next_table_off:next_table_off+2])[0]
                res_size = next_res_off - res_off
            else:
                res_size = len(data) - res_off
            
            print(f'{rid:6d} | 0x{table_off:05X} | 0x{res_off:06X} | 0x{next_res_off:06X} | {res_size} bytes')
            
            # 显示资源前16字节
            if res_off < len(data) and res_size > 0:
                print(f'       前16字节: ', end='')
                for i in range(min(16, res_size)):
                    print(f'{data[res_off + i]:02X} ', end='')
                print()
                
                # 如果是201或205,尝试解析为16位指令表
                if rid in [201, 205]:
                    print(f'       作为16位指令表:')
                    num_instructions = res_size // 2
                    for i in range(min(20, num_instructions)):
                        instr = struct.unpack('<h', data[res_off + i*2:res_off + i*2 + 2])[0]
                        print(f'         [{i:2d}] = {instr:6d} (0x{instr & 0xFFFF:04X})')
    
    print()
    print('=== 索引表1 (4字节偏移, 前0x46字节) ===')
    print('索引 | 偏移      | 大小')
    print('-----|-----------|----------')
    
    num_entries = 0x46 // 4
    for i in range(num_entries):
        off = i * 4
        if off + 4 <= len(data):
            val = struct.unpack('<I', data[off:off+4])[0]
            if val < len(data):
                if i + 1 < num_entries:
                    next_val = struct.unpack('<I', data[off+4:off+8])[0]
                    if next_val > val:
                        res_size = next_val - val
                    else:
                        res_size = 0
                else:
                    res_size = 0
                if res_size > 0 and res_size < 100000:
                    print(f'  {i:2d} | 0x{val:06X}  | {res_size} bytes')

if __name__ == '__main__':
    if len(sys.argv) > 1:
        analyze_fdother_resources(sys.argv[1])
    else:
        print('Usage: python analyze_fdother_resources.py <path_to_FDOTHER.DAT>')
