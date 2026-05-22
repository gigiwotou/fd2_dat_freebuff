"""
检查DATO.DAT文件完整结构
"""
import struct

def check_dato_structure():
    with open("game/DATO.DAT", "rb") as f:
        data = f.read()
    
    file_size = len(data)
    print(f"文件大小: {file_size} 字节")
    
    # 文件头6字节
    print(f"文件头: {data[:6]}")
    
    # 资源数量
    count = struct.unpack_from('<I', data, 6)[0]
    print(f"资源数量: {count}")
    
    # 偏移表大小
    table_size = (count + 1) * 4
    print(f"偏移表大小: {table_size} 字节")
    print(f"偏移表范围: 10 - {10 + table_size - 1}")
    
    # 检查索引135和136
    print("\n检查索引135和136:")
    for idx in [135, 136]:
        pos = 10 + idx * 4
        if pos + 8 <= file_size:
            start, end = struct.unpack_from('<II', data, pos)
            print(f"  索引{idx}: start={start}, end={end}")
    
    # 检查文件末尾的字节
    print("\n文件末尾16字节:")
    print(f"  {data[-16:].hex()}")
    
    # 检查偏移表是否完整
    last_offset_pos = 10 + count * 4
    print(f"\n最后一个偏移表位置: {last_offset_pos}")
    if last_offset_pos <= file_size:
        print(f"  在文件范围内: 是")
    else:
        print(f"  在文件范围内: 否")

if __name__ == "__main__":
    check_dato_structure()
