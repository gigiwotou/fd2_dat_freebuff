"""
直接检查DATO.DAT偏移表中索引193指向的数据
"""
import struct

def check_dato_193_data():
    with open("game/DATO.DAT", "rb") as f:
        data = f.read()
    
    file_size = len(data)
    
    # 游戏读取位置
    pos = 4 * 193 + 6
    print(f"游戏读取索引193的位置: {pos}")
    
    if pos + 8 > file_size:
        print(f"超出文件大小")
        return
    
    # 读取8字节偏移
    raw = data[pos:pos+8]
    start, end = struct.unpack_from('<II', data, pos)
    print(f"原始字节: {raw.hex()}")
    print(f"start={start}, end={end}")
    
    # 这些值明显不对，让我检查它们是否是某种编码或映射
    # 检查这些值模文件大小
    start_mod = start % file_size
    end_mod = end % file_size
    print(f"start mod file_size = {start_mod}")
    print(f"end mod file_size = {end_mod}")
    
    # 检查这些位置的数据
    if start_mod < file_size - 20:
        print(f"\n在start_mod位置的数据:")
        chunk = data[start_mod:start_mod+20]
        print(f"  前20字节: {chunk.hex()}")
        w, h = struct.unpack_from('<hh', chunk, 16)
        print(f"  w={w}, h={h}")
    
    # 检查原始文件是否有多个段
    print(f"\n\n检查文件中的重复模式:")
    # 搜索文件头标记 "LLLLLL"
    header = b'LLLLLL'
    positions = []
    start_search = 0
    while True:
        pos = data.find(header, start_search)
        if pos == -1:
            break
        positions.append(pos)
        start_search = pos + 1
    
    print(f"找到文件头 'LLLLLL' 在位置: {positions}")

if __name__ == "__main__":
    check_dato_193_data()
