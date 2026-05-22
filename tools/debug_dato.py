"""
直接检查DATO.DAT的二进制结构
"""
import struct

def analyze_dato():
    with open("game/DATO.DAT", "rb") as f:
        data = f.read()
    
    print(f"DATO.DAT 文件大小: {len(data)} 字节 ({len(data)/1024:.2f} KB)")
    print(f"文件头(前6字节): {data[:6].hex()} ({data[:6]})")
    
    # 读取资源数量
    count = struct.unpack_from('<I', data, 6)[0]
    print(f"资源总数: {count}")
    
    # 检查前几个资源的偏移
    print("\n前10个资源的偏移:")
    print("-" * 50)
    for i in range(min(10, count)):
        offset = 10 + i * 4
        off_val = struct.unpack_from('<I', data, offset)[0]
        print(f"  索引{i}: 偏移在{offset}, 值={off_val} (0x{off_val:X})")
    
    # 检查索引193和196
    print("\n检查索引193和196:")
    print("-" * 50)
    for idx in [193, 196]:
        offset = 10 + idx * 4
        off_start = struct.unpack_from('<I', data, offset)[0]
        off_end = struct.unpack_from('<I', data, offset + 4)[0]
        size = off_end - off_start
        
        print(f"\n  索引{idx}:")
        print(f"    偏移表位置: {offset}")
        print(f"    start: {off_start} (0x{off_start:X})")
        print(f"    end: {off_end} (0x{off_end:X})")
        print(f"    大小: {size}")
        
        if off_start < len(data) and off_end <= len(data):
            # 读取资源头
            if size >= 20:
                res_data = data[off_start:off_start+20]
                w, h = struct.unpack_from('<hh', res_data, 16)
                print(f"    资源头: w={w}, h={h}")
                print(f"    帧偏移: {struct.unpack_from('<III', res_data, 4)}")
        else:
            print(f"    *** 偏移超出文件大小 ***")
    
    # 检查索引表范围
    print("\n检查索引表的范围:")
    print("-" * 50)
    last_offset = 10 + count * 4
    print(f"  偏移表起始: 字节10")
    print(f"  偏移表结束: 字节{last_offset}")
    print(f"  偏移表大小: {last_offset - 10} 字节")
    
    # 检查第一个和最后一个偏移
    first_off = struct.unpack_from('<I', data, 10)[0]
    last_off = struct.unpack_from('<I', data, last_offset - 4)[0]
    print(f"  第一个资源偏移: {first_off}")
    print(f"  最后一个资源结束偏移: {last_off}")
    print(f"  数据区大小: {last_off - first_off} 字节")

if __name__ == "__main__":
    analyze_dato()
