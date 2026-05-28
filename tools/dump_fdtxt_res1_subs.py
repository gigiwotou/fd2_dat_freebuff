"""详细转储FDTXT.DAT资源1的子项0和子项1的完整内容"""

import struct

def dump_sub_text(data, rs, re, sub_idx):
    rd = data[rs:]
    sub_count = struct.unpack_from('<h', rd, 0)[0]
    
    if sub_idx < 0 or sub_idx >= sub_count:
        print(f"子项{sub_idx} 超出范围 (总数: {sub_count})")
        return
    
    offs = []
    for i in range(sub_count):
        off = struct.unpack_from('<h', rd, 2 + i * 2)[0]
        offs.append(off)
    
    sub_off = offs[sub_idx]
    if sub_off < 0 or sub_off >= (re - rs):
        print(f"子项{sub_idx} 偏移无效: {sub_off}")
        return
    
    print(f"\n=== 子项{sub_idx} 完整内容 ===")
    print(f"偏移: {sub_off} (0x{sub_off:X})")
    
    sub_data = rd[sub_off:]
    print(f"完整word序列:")
    
    j = 0
    while j < len(sub_data) // 2:
        val = struct.unpack_from('<h', sub_data, j * 2)[0]
        if val == -1:
            print(f"  [{j}] = {val} (TEXT_END)")
            break
        elif val == -2:
            print(f"  [{j}] = {val} (TEXT_NEWLINE)")
        elif val == -3:
            print(f"  [{j}] = {val} (TEXT_NEWLINE2)")
        elif val == -17:
            print(f"  [{j}] = {val} (TEXT_PORTRAIT_F)")
            j += 1
            if j < len(sub_data) // 2:
                pid = struct.unpack_from('<h', sub_data, j * 2)[0]
                print(f"  [{j}] = {pid} (portrait_id)")
        elif val == -18:
            print(f"  [{j}] = {val} (TEXT_PORTRAIT_S)")
            j += 1
            if j < len(sub_data) // 2:
                pid = struct.unpack_from('<h', sub_data, j * 2)[0]
                print(f"  [{j}] = {pid} (portrait_id)")
        elif val == -19:
            print(f"  [{j}] = {val} (TEXT_CHAR_F)")
            j += 1
            if j < len(sub_data) // 2:
                cid = struct.unpack_from('<h', sub_data, j * 2)[0]
                print(f"  [{j}] = {cid} (char_db_idx)")
        elif val == -20:
            print(f"  [{j}] = {val} (TEXT_CHAR_S)")
            j += 1
            if j < len(sub_data) // 2:
                cid = struct.unpack_from('<h', sub_data, j * 2)[0]
                print(f"  [{j}] = {cid} (char_db_idx)")
        elif val >= 0 and val < 0x8000:
            print(f"  [{j}] = {val} (char)")
        else:
            print(f"  [{j}] = {val} (0x{val:04X})")
        j += 1

def analyze_fdtxt_res1():
    with open('game/FDTXT.DAT', 'rb') as f:
        data = f.read()
    
    # 读取索引表
    count = struct.unpack_from('<I', data, 6)[0]
    print(f"资源总数: {count}")
    
    # 读取所有偏移
    offsets = []
    for i in range(count):
        off = struct.unpack_from('<I', data, 10 + i * 4)[0]
        offsets.append(off)
    
    # 分析资源1（第二关）
    res_idx = 1
    rs = offsets[res_idx]
    re = offsets[res_idx + 1] if res_idx + 1 < count else len(data)
    
    print(f"\n资源{res_idx}范围: 0x{rs:X} - 0x{re:X}")
    print(f"资源{res_idx}大小: {re - rs} 字节")
    
    rd = data[rs:]
    sub_count = struct.unpack_from('<h', rd, 0)[0]
    print(f"子项数量: {sub_count}")
    
    # 转储子项0和子项1
    dump_sub_text(data, rs, re, 0)
    dump_sub_text(data, rs, re, 1)
    dump_sub_text(data, rs, re, 2)

if __name__ == '__main__':
    analyze_fdtxt_res1()
