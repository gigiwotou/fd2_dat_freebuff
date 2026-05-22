"""
检查DATO.DAT索引193附近的偏移表数据
"""
import struct

def check_dato_table():
    with open("game/DATO.DAT", "rb") as f:
        data = f.read()
    
    # 索引193的偏移表位置
    base = 10 + 193 * 4
    print(f"索引193的偏移表位置: 字节{base}")
    
    # 检查索引193附近的偏移（前后各5个）
    print("\n检查索引188-198的偏移表:")
    print("-" * 80)
    for idx in range(188, 200):
        offset = 10 + idx * 4
        off_start = struct.unpack_from('<I', data, offset)[0]
        off_end = struct.unpack_from('<I', data, offset + 4)[0]
        
        # 打印原始字节
        raw = data[offset:offset+8]
        
        print(f"  索引{idx}:")
        print(f"    位置: {offset}, 原始字节: {raw.hex()}")
        print(f"    start: {off_start} (0x{off_start:X})")
        print(f"    end: {off_end} (0x{off_end:X})")
        print(f"    在文件内: {'是' if off_start < len(data) and off_end <= len(data) else '否'}")
        print()

if __name__ == "__main__":
    check_dato_table()
