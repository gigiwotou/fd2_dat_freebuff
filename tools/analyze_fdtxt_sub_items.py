"""分析FDTXT.DAT资源1（第二关）的子项结构"""

import struct

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
        print(f"资源{i} 偏移: 0x{off:X} ({off})")
    
    # 分析资源1（第二关）
    print("\n=== 分析资源1（第二关） ===")
    res_idx = 1
    rs = offsets[res_idx]
    re = offsets[res_idx + 1] if res_idx + 1 < count else len(data)
    
    print(f"资源1范围: 0x{rs:X} - 0x{re:X}")
    print(f"资源1大小: {re - rs} 字节")
    
    # 读取子项数量
    rd = data[rs:]
    sub_count = struct.unpack_from('<h', rd, 0)[0]
    print(f"子项数量: {sub_count}")
    
    # 读取子项偏移表
    print("\n子项偏移表:")
    for i in range(sub_count):
        sub_off = struct.unpack_from('<h', rd, 2 + i * 2)[0]
        print(f"  子项{i} 偏移: {sub_off} (0x{sub_off:X})")
        if sub_off < 0:
            print(f"    -> 负数偏移，跳过")
            continue
        
        # 读取子项内容
        sub_data = rd[sub_off:]
        print(f"    -> 前20个word值:")
        for j in range(min(20, len(sub_data) // 2)):
            val = struct.unpack_from('<h', sub_data, j * 2)[0]
            if val == -1:
                print(f"      [{j}] = {val} (END)")
                break
            elif val == -2:
                print(f"      [{j}] = {val} (NEWLINE)")
            elif val == -3:
                print(f"      [{j}] = {val} (NEWLINE2)")
            elif val == -17:
                print(f"      [{j}] = {val} (PORTRAIT_F)")
                j += 1
                if j < len(sub_data) // 2:
                    pid = struct.unpack_from('<h', sub_data, j * 2)[0]
                    print(f"      [{j}] = {pid} (portrait_id)")
            elif val == -18:
                print(f"      [{j}] = {val} (PORTRAIT_S)")
                j += 1
                if j < len(sub_data) // 2:
                    pid = struct.unpack_from('<h', sub_data, j * 2)[0]
                    print(f"      [{j}] = {pid} (portrait_id)")
            elif val >= 0 and val < 0x8000:
                # 可能是字符
                print(f"      [{j}] = {val} (char)")
            else:
                print(f"      [{j}] = {val} (0x{val:04X})")

if __name__ == '__main__':
    analyze_fdtxt_res1()
