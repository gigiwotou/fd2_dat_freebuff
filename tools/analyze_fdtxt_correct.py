#!/usr/bin/env python3
"""正确分析FDTXT.DAT的文本数据"""

import struct

FDTXT_PATH = "game/FDTXT.DAT"

def analyze_fdtxt():
    with open(FDTXT_PATH, 'rb') as f:
        data = f.read()
    
    # 读取资源集数量 (32-bit at offset 6)
    count = struct.unpack_from('<I', data, 6)[0]
    print(f"资源集数量: {count}")
    print(f"文件大小: {len(data)} 字节")
    print()
    
    # 读取资源集偏移表 (32-bit values starting at offset 10)
    offsets = []
    for i in range(count):
        off = struct.unpack_from('<I', data, 10 + i * 4)[0]
        offsets.append(off)
        print(f"资源集 {i}: 文件偏移 {off} (0x{off:06x})")
    
    print()
    
    # 分析前3个资源集
    for res_idx in range(min(3, count)):
        rs = offsets[res_idx]
        re = offsets[res_idx + 1] if res_idx + 1 < count else len(data)
        
        # 资源数据
        rd = data[rs:re]
        
        # 子项数量 (16-bit signed at resource start)
        sub_count = struct.unpack_from('<h', rd, 0)[0]
        print(f"\n资源集 {res_idx} (文件偏移 {rs}-{re}):")
        print(f"  子项数量: {sub_count}")
        
        # 子项偏移表 (16-bit signed values, relative to resource start)
        for sub_idx in range(min(sub_count, 5)):  # 只分析前5个子项
            off = struct.unpack_from('<h', rd, 2 + sub_idx * 2)[0]
            next_off = struct.unpack_from('<h', rd, 2 + (sub_idx + 1) * 2)[0] if sub_idx + 1 < sub_count else len(rd)
            
            # 这些是相对偏移
            abs_start = rs + off
            abs_end = rs + next_off
            
            print(f"  子项 {sub_idx}: 相对偏移 {off}-{next_off}, 绝对偏移 {abs_start}-{abs_end}")
            
            # 获取文本数据
            text_data = rd[off:next_off]
            
            # 解析文本
            words = []
            i = 0
            while i < len(text_data):
                if i + 2 > len(text_data):
                    break
                word = struct.unpack_from('<h', text_data, i)[0]
                words.append(word)
                i += 2
                
                # 如果是带参数的控制码，跳过参数
                if word in (-17, -18, -19, -20):  # TEXT_PORTRAIT_F/S, TEXT_CHAR_F/S
                    if i + 2 <= len(text_data):
                        param = struct.unpack_from('<h', text_data, i)[0]
                        words.append(('param', param))
                        i += 2
            
            # 打印文本内容
            text_preview = ""
            for w in words[:30]:
                if isinstance(w, tuple):
                    continue
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
                    text_preview += f"[{w}]"
                else:
                    text_preview += f"[{w}]"
            
            print(f"    内容: {text_preview}")

if __name__ == "__main__":
    analyze_fdtxt()
