#!/usr/bin/env python3
"""分析FDTXT.DAT中文本项的控制码分布"""

import struct

FDTXT_PATH = "game/FDTXT.DAT"

def analyze_control_codes():
    with open(FDTXT_PATH, 'rb') as f:
        data = f.read()
    
    count = struct.unpack_from('<I', data, 6)[0]
    print(f"资源集数量: {count}")
    
    for res_idx in range(min(3, count)):
        rs = struct.unpack_from('<I', data, 10 + res_idx * 4)[0]
        re = struct.unpack_from('<I', data, 10 + (res_idx + 1) * 4)[0] if res_idx + 1 < count else len(data)
        
        rd = data[rs:re]
        sub_count = struct.unpack_from('<h', rd, 0)[0]
        print(f"\n资源集 {res_idx}: {sub_count} 个子项")
        
        for sub_idx in range(sub_count):
            off = struct.unpack_from('<h', rd, 2 + sub_idx * 2)[0]
            next_off = struct.unpack_from('<h', rd, 2 + (sub_idx + 1) * 2)[0] if sub_idx + 1 < sub_count else len(rd)
            
            text_data = rd[off:next_off]
            print(f"  子项 {sub_idx}: 偏移={off}-{next_off}, 长度={next_off-off} 字节")
            
            # 解析文本
            i = 0
            words = []
            while i < len(text_data):
                if i + 2 > len(text_data):
                    break
                word = struct.unpack_from('<h', text_data, i)[0]
                words.append(word)
                i += 2
                
                # 如果是带参数的控制码，跳过参数
                if word in (-17, -18, -19, -20):  # TEXT_PORTRAIT_F/S, TEXT_CHAR_F/S
                    if i + 2 <= len(text_data):
                        words.append(('param', struct.unpack_from('<h', text_data, i)[0]))
                        i += 2
                elif word in (-4, -5):  # TEXT_RECURSE1/2
                    if i + 2 <= len(text_data):
                        words.append(('param', struct.unpack_from('<h', text_data, i)[0]))
                        i += 2
            
            # 打印控制码和字符
            text_preview = ""
            for w in words:
                if isinstance(w, tuple):
                    continue  # 跳过参数
                if w == -1:
                    text_preview += "[END]"
                elif w == -2:
                    text_preview += "[NL]"
                elif w == -3:
                    text_preview += "[NL2]"
                elif w == -4:
                    text_preview += "[REC1]"
                elif w == -5:
                    text_preview += "[REC2]"
                elif w == -6:
                    text_preview += "[NUM]"
                elif w == -17:
                    text_preview += "[PF"
                elif w == -18:
                    text_preview += "[PS"
                elif w == -19:
                    text_preview += "[CF"
                elif w == -20:
                    text_preview += "[CS"
                elif w >= 0 and w < 1824:
                    text_preview += chr(w) if w < 128 else f"[{w}]"
                else:
                    text_preview += f"[{w}]"
            
            print(f"    内容: {text_preview[:100]}...")

if __name__ == "__main__":
    analyze_control_codes()
