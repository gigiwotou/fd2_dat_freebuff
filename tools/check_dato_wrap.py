"""
验证DATO.DAT索引回绕逻辑
"""
import struct

def check_wrap_around():
    with open("game/DATO.DAT", "rb") as f:
        data = f.read()
    
    file_size = len(data)
    
    # 索引135是回绕点
    pos135 = 10 + 135 * 4
    start135, end135 = struct.unpack_from('<II', data, pos135)
    print(f"索引135 (回绕点): start={start135}, end={end135}")
    print(f"  end135={end135} 应该是第二轮资源的起始偏移")
    
    # 检查索引193
    # 如果索引136是第二轮的第一个资源，那么索引193是第二轮的第 193-136 = 57 个资源
    idx193_pos = 10 + 193 * 4
    start193, end193 = struct.unpack_from('<II', data, idx193_pos)
    print(f"\n索引193 (直接从偏移表): start={start193}, end={end193}")
    
    # 第二轮资源从字节16开始
    second_base = 16
    print(f"第二轮资源起始: 字节{second_base}")
    
    # 计算第二轮资源的偏移
    # 索引136对应第二轮资源0，偏移在16
    # 索引193对应第二轮资源57
    second_idx = 193 - 136  # = 57
    second_pos = second_base + second_idx * 4
    print(f"\n第二轮资源索引{second_idx}:")
    print(f"  位置: {second_pos}")
    
    if second_pos + 8 <= file_size:
        s, e = struct.unpack_from('<II', data, second_pos)
        print(f"  start={s}, end={e}")
        if s < file_size and e <= file_size:
            print(f"  状态: 有效")
        else:
            print(f"  状态: 无效")

if __name__ == "__main__":
    check_wrap_around()
