"""
检查DATO.DAT偏移表完整结构
"""
import struct

def full_analysis():
    with open("game/DATO.DAT", "rb") as f:
        data = f.read()
    
    file_size = len(data)
    
    # 文件头6字节：LLLLLL
    print(f"文件头: {data[:6]}")
    
    # 资源数量（4字节，偏移6）
    count = struct.unpack_from('<I', data, 6)[0]
    print(f"资源数量: {count}")
    print(f"文件大小: {file_size}")
    print()
    
    # 偏移表从字节10开始
    # 但是游戏使用 fseek(v3, 4*a3 + 6, 0) 读取8字节
    # 所以对于索引a3，读取位置是 4*a3 + 6
    
    print("检查游戏实际读取位置:")
    print("-" * 80)
    
    for idx in [0, 1, 134, 135, 136, 193, 196]:
        pos = 4 * idx + 6
        if pos + 8 <= file_size:
            start, end = struct.unpack_from('<II', data, pos)
            size = end - start
            valid = "有效" if start < file_size and end <= file_size else "无效"
            print(f"  索引{idx}: 游戏读取位置={pos}, start={start}, end={end}, size={size}, 状态={valid}")
    
    print()
    print("检查索引135（回绕点）:")
    print("-" * 80)
    # 索引135
    pos135 = 4 * 135 + 6
    start135, end135 = struct.unpack_from('<II', data, pos135)
    print(f"  索引135: start={start135}, end={end135}")
    print(f"  start135 = {start135} (应该是最后一个资源的结束)")
    print(f"  end135 = {end135} (应该是下一个资源的开始)")
    
    # 检查索引0-134的资源是否连续
    print()
    print("检查索引0-134的偏移连续性:")
    print("-" * 80)
    prev_end = None
    for idx in range(135):
        pos = 4 * idx + 6
        start, end = struct.unpack_from('<II', data, pos)
        if prev_end is not None and start != prev_end:
            print(f"  *** 索引{idx}: start={start} != 前一个end={prev_end} ***")
        prev_end = end
    
    print("  索引0-134的偏移是连续的" if prev_end == 1979029 else "  索引0-134的偏移不连续")
    
    print()
    print("检查索引135-269（第二轮资源）:")
    print("-" * 80)
    for idx in range(135, min(145, count)):
        pos = 4 * idx + 6
        if pos + 8 <= file_size:
            start, end = struct.unpack_from('<II', data, pos)
            valid = "有效" if start < file_size and end <= file_size else "无效"
            print(f"  索引{idx}: start={start}, end={end}, 状态={valid}")

if __name__ == "__main__":
    full_analysis()
