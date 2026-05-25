#!/usr/bin/env python3
"""分析FDTXT.DAT子项1的第一个控制码"""

import struct

FDTXT_PATH = "game/FDTXT.DAT"

def analyze_sub(res_idx, sub_idx):
    with open(FDTXT_PATH, "rb") as f:
        data = f.read()
    
    # 读取资源数量
    count = struct.unpack("<I", data[6:10])[0]
    print(f"资源总数: {count}")
    
    if res_idx >= count:
        print(f"错误: 资源索引 {res_idx} 超出范围")
        return
    
    # 读取资源偏移
    rs = struct.unpack("<I", data[10 + res_idx * 4:10 + res_idx * 4 + 4])[0]
    re = struct.unpack("<I", data[10 + (res_idx + 1) * 4:10 + (res_idx + 1) * 4 + 4])[0] if res_idx + 1 < count else len(data)
    
    print(f"\n资源集 {res_idx}: 偏移 {rs:#x} - {re:#x}")
    
    # 读取子项数量
    rd = data[rs:re]
    sc = struct.unpack("<h", rd[0:2])[0]
    print(f"子项数量: {sc}")
    
    if sub_idx >= sc:
        print(f"错误: 子项索引 {sub_idx} 超出范围")
        return
    
    # 读取子项偏移
    offs = struct.unpack(f"<{sc}h", rd[2:2 + sc * 2])
    bo = offs[sub_idx]
    
    if bo < 0 or bo >= len(rd):
        print(f"错误: 子项偏移 {bo} 无效")
        return
    
    # 读取子项内容
    ts = rd[bo:]
    
    # 读取前20个控制码
    print(f"\n子项 {sub_idx} 的前20个控制码:")
    for i in range(min(20, len(ts))):
        word = struct.unpack("<h", ts[i*2:i*2+2])[0]
        
        if word == -1:
            name = "TEXT_END (-1)"
        elif word == -2:
            name = "TEXT_NEWLINE (-2)"
        elif word == -3:
            name = "TEXT_NEWLINE2 (-3)"
        elif word == -4:
            name = "TEXT_RECURSE1 (-4)"
        elif word == -5:
            name = "TEXT_RECURSE2 (-5)"
        elif word == -6:
            name = "TEXT_SHOW_NUM (-6)"
        elif word == -17:
            name = "TEXT_PORTRAIT_F (-17)"
        elif word == -18:
            name = "TEXT_PORTRAIT_S (-18)"
        elif word == -19:
            name = "TEXT_CHAR_F (-19)"
        elif word == -20:
            name = "TEXT_CHAR_S (-20)"
        else:
            name = f"字符 ({word})"
        
        print(f"  [{i}] {name}")
        
        if word == -1:  # TEXT_END
            break

if __name__ == "__main__":
    analyze_sub(1, 0)  # 资源集1，子项0
    print("\n" + "="*50 + "\n")
    analyze_sub(1, 1)  # 资源集1，子项1
