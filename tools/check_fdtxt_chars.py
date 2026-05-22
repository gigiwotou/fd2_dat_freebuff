"""
检查FDTXT资源0/子项0的TEXT_CHAR_F/S控制码
"""
import struct

def check_fdtxt_chars():
    with open("game/FDTXT.DAT", "rb") as f:
        fdtxt = f.read()
    
    # 资源数量
    count = struct.unpack_from('<I', fdtxt, 6)[0]
    print(f"FDTXT资源数量: {count}")
    
    # 读取偏移表
    offsets = []
    for i in range(count):
        off = struct.unpack_from('<I', fdtxt, 10 + i*4)[0]
        offsets.append(off)
    
    # 读取资源0
    res_start = offsets[0]
    res_end = offsets[1] if 1 < count else len(fdtxt)
    res_data = fdtxt[res_start:res_end]
    
    # 子项数量
    sub_count = struct.unpack_from('<h', res_data, 0)[0]
    print(f"资源0的子项数量: {sub_count}")
    
    # 子项偏移表
    sub_offsets = []
    for i in range(sub_count):
        off = struct.unpack_from('<h', res_data, 2 + i*2)[0]
        sub_offsets.append(off)
    
    # 解析子项0
    text_start = sub_offsets[0]
    text_end = sub_offsets[1] if 1 < sub_count else len(res_data)
    
    print(f"\n子项0: 文本偏移{text_start}-{text_end}")
    print("-" * 80)
    
    # 解析文本中的控制码
    pos = text_start
    char_idx = 0
    while pos < text_end:
        word = struct.unpack_from('<h', res_data, pos)[0]
        pos += 2
        
        if word == -1:  # TEXT_END
            print(f"  TEXT_END")
            break
        elif word == -2:  # TEXT_NEWLINE
            print(f"  TEXT_NEWLINE")
        elif word == -3:  # TEXT_NEWLINE2
            print(f"  TEXT_NEWLINE2")
        elif word == -17:  # TEXT_PORTRAIT_F
            pid = struct.unpack_from('<h', res_data, pos)[0]
            pos += 2
            print(f"  TEXT_PORTRAIT_F: portrait_id={pid}")
        elif word == -18:  # TEXT_PORTRAIT_S
            pid = struct.unpack_from('<h', res_data, pos)[0]
            pos += 2
            print(f"  TEXT_PORTRAIT_S: portrait_id={pid}")
        elif word == -19:  # TEXT_CHAR_F
            cid = struct.unpack_from('<h', res_data, pos)[0]
            pos += 2
            print(f"  TEXT_CHAR_F: char_db_index={cid}")
            char_idx += 1
            if char_idx > 5:  # 只显示前5个
                print("  ... (更多字符省略)")
                break
        elif word == -20:  # TEXT_CHAR_S
            cid = struct.unpack_from('<h', res_data, pos)[0]
            pos += 2
            print(f"  TEXT_CHAR_S: char_db_index={cid}")
        elif word >= 0:
            pass  # 普通字符
        else:
            print(f"  未知控制码: {word}")

if __name__ == "__main__":
    check_fdtxt_chars()
