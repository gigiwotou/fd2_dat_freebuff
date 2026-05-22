"""
DATO.DAT 字符数据库检查工具
检查FDTXT中的字符索引(9和10)是否映射到有效的DATO资源
"""
import struct
import sys
import os

def main():
    # 定位DATO.DAT文件
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    dat_path = os.path.join(project_root, 'game', 'DATO.DAT')
    
    if not os.path.exists(dat_path):
        print(f'错误: 找不到 {dat_path}')
        sys.exit(1)
    
    with open(dat_path, 'rb') as f:
        data = f.read()
    
    file_size = len(data)
    print(f'DATO.DAT 文件大小: {file_size} 字节 ({file_size/1024:.2f} KB)')
    
    # 解析文件头
    header = data[0:6]
    print(f'文件头: {header.hex()} ({header.decode("ascii", errors="replace")})')
    
    # 读取资源总数 (偏移6, 4字节小端)
    total_resources = struct.unpack('<I', data[6:10])[0]
    print(f'\n资源总数: {total_resources}')
    
    # 解析偏移表
    offset_table_start = 10
    offsets = []
    for i in range(total_resources + 1):
        off = struct.unpack('<I', data[offset_table_start + i * 4 : offset_table_start + i * 4 + 4])[0]
        offsets.append(off)
    
    print(f'偏移表范围: {offsets[0]} - {offsets[-1]}')
    print(f'索引0数据块大小: {offsets[1] - offsets[0]} 字节')
    
    # 加载索引0 (字符数据库)
    db_start = offsets[0]
    db_end = offsets[1]
    db_size = db_end - db_start
    db_data = data[db_start:db_end]
    entry_count = db_size // 80
    
    print(f'\n=== 字符数据库 (索引0) ===')
    print(f'数据范围: {db_start} - {db_end}')
    print(f'数据块大小: {db_size} 字节')
    print(f'条目数 (80字节/条): {entry_count}')
    print(f'剩余字节: {db_size % 80}')
    
    # 检查索引9和10
    print(f'\n=== 检查字符索引 9 和 10 ===')
    
    for char_idx in [9, 10]:
        if char_idx >= entry_count:
            print(f'\n字符索引 {char_idx}: 超出范围 (最大 {entry_count - 1})')
            continue
        
        entry_start = char_idx * 80
        entry = db_data[entry_start : entry_start + 80]
        
        print(f'\n--- 字符索引 {char_idx} ---')
        print(f'  原始80字节 (前20字节HEX): {entry[0:20].hex(" ")}')
        print(f'  byte[7] (DATO资源索引): {entry[7]}')
        print(f'  byte[8] (角色图标ID): {entry[8]}')
        
        # 检查DATO资源索引是否有效
        dato_idx = entry[7]
        if dato_idx < total_resources:
            dato_start = struct.unpack('<I', data[10 + dato_idx * 4 : 14 + dato_idx * 4])[0]
            dato_end = struct.unpack('<I', data[10 + dato_idx * 4 + 4 : 14 + dato_idx * 4 + 4])[0]
            dato_size = dato_end - dato_start
            print(f'  DATO资源[{dato_idx}] 大小: {dato_size} 字节 [有效]')
        else:
            print(f'  DATO资源[{dato_idx}] [无效! 超出资源总数 {total_resources}]')
    
    # 额外: 列出所有字符的byte[7]和byte[8]
    print(f'\n=== 所有字符的 DATO资源索引(byte[7]) 和 图标ID(byte[8]) ===')
    print(f'{"索引":>4} | {"byte[7]":>7} | {"byte[8]":>7} | {"DATO资源有效":>12}')
    print('-' * 40)
    
    for i in range(entry_count):
        entry = db_data[i * 80 : i * 80 + 80]
        dato_idx = entry[7]
        icon_id = entry[8]
        valid = '是' if dato_idx < total_resources else '否'
        print(f'{i:>4} | {dato_idx:>7} | {icon_id:>7} | {valid:>12}')

if __name__ == '__main__':
    main()
