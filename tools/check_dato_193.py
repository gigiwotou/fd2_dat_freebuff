"""
检查DATO.DAT索引193在文件中的真实偏移
"""
import struct

def check_index_193():
    with open("game/DATO.DAT", "rb") as f:
        data = f.read()
    
    file_size = len(data)
    
    # 游戏实际读取位置
    pos193 = 4 * 193 + 6
    print(f"索引193的游戏读取位置: {pos193}")
    print(f"文件总大小: {file_size}")
    
    if pos193 + 8 > file_size:
        print(f"*** 位置超出文件大小 ***")
    else:
        raw = data[pos193:pos193+8]
        start, end = struct.unpack_from('<II', data, pos193)
        print(f"原始字节: {raw.hex()}")
        print(f"start (LE): {start} (0x{start:X})")
        print(f"end (LE): {end} (0x{end:X})")
        
        # 尝试其他字节序
        start_be, end_be = struct.unpack_from('>II', data, pos193)
        print(f"start (BE): {start_be} (0x{start_be:X})")
        print(f"end (BE): {end_be} (0x{end_be:X})")
    
    # 检查字符数据库
    print("\n\n检查字符数据库(索引0):")
    print("-" * 80)
    
    # 索引0的位置
    pos0 = 4 * 0 + 6
    start0, end0 = struct.unpack_from('<II', data, pos0)
    print(f"索引0: start={start0}, end={end0}")
    print(f"数据库大小: {end0 - start0}")
    
    db_data = data[start0:end0]
    print(f"数据库字节数: {len(db_data)}")
    print(f"条目数(80字节/条): {len(db_data) // 80}")
    
    # 检查索引9和10的条目
    print("\n字符数据库索引9和10:")
    print("-" * 80)
    for idx in [9, 10]:
        entry_offset = idx * 80
        entry = db_data[entry_offset:entry_offset+80]
        print(f"\n  字符索引{idx}:")
        print(f"    原始数据(前16字节): {entry[:16].hex()}")
        print(f"    byte[7] (DATO索引): {entry[7]}")
        print(f"    byte[8] (角色ID): {entry[8]}")
        
        # 计算游戏加载DATO的位置
        dato_idx = entry[7]
        dato_pos = 4 * dato_idx + 6
        print(f"    游戏加载位置: {dato_pos}")
        
        if dato_pos + 8 <= file_size:
            d_start, d_end = struct.unpack_from('<II', data, dato_pos)
            print(f"    DATO资源: start={d_start}, end={d_end}, 大小={d_end-d_start}")
            if d_start < file_size and d_end <= file_size:
                print(f"    状态: 有效")
            else:
                print(f"    状态: *** 无效 ***")

if __name__ == "__main__":
    check_index_193()
