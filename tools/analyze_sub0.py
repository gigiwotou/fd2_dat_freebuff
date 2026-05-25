#!/usr/bin/env python3
"""分析FDTXT.DAT子项0的前50个控制码"""

import struct

FDTXT_PATH = "game/FDTXT.DAT"

def analyze_sub0():
    with open(FDTXT_PATH, "rb") as f:
        data = f.read()
    
    count = struct.unpack("<I", data[6:10])[0]
    print(f"资源总数: {count}")
    
    rs = struct.unpack("<I", data[10:14])[0]
    re = struct.unpack("<I", data[14:18])[0]
    
    print(f"资源集0: 偏移 {rs:#x} - {re:#x}")
    
    rd = data[rs:re]
    sc = struct.unpack("<h", rd[0:2])[0]
    print(f"子项数量: {sc}")
    
    for sub in range(min(3, sc)):
        offs = struct.unpack(f"<{sc}h", rd[2:2 + sc * 2])
        bo = offs[sub]
        
        if bo < 0 or bo >= len(rd):
            continue
        
        ts = rd[bo:]
        print(f"\n子项 {sub} 的前50个控制码:")
        for i in range(min(50, len(ts))):
            word = struct.unpack("<h", ts[i*2:i*2+2])[0]
            
            if word == -1:
                name = "TEXT_END (-1)"
            elif word == -2:
                name = "TEXT_NEWLINE (-2)"
            elif word == -3:
                name = "TEXT_NEWLINE2 (-3)"
            elif word == -17:
                name = "TEXT_PORTRAIT_F (-17)"
                i += 1
                pid = struct.unpack("<h", ts[i*2:i*2+2])[0]
                print(f"  [{i}] {name} pid={pid}")
                continue
            elif word == -18:
                name = "TEXT_PORTRAIT_S (-18)"
                i += 1
                pid = struct.unpack("<h", ts[i*2:i*2+2])[0]
                print(f"  [{i}] {name} pid={pid}")
                continue
            elif word == -19:
                name = "TEXT_CHAR_F (-19)"
                i += 1
                cid = struct.unpack("<h", ts[i*2:i*2+2])[0]
                print(f"  [{i}] {name} cid={cid}")
                continue
            elif word == -20:
                name = "TEXT_CHAR_S (-20)"
                i += 1
                cid = struct.unpack("<h", ts[i*2:i*2+2])[0]
                print(f"  [{i}] {name} cid={cid}")
                continue
            elif 0 <= word <= 0xFF:
                name = f"字符 ({word})"
            else:
                name = f"未知 ({word})"
            
            print(f"  [{i}] {name}")
            
            if word == -1:
                break

if __name__ == "__main__":
    analyze_sub0()
