#!/usr/bin/env python3
"""分析FDTXT.DAT中具体子项的原始字节"""

import struct

FDTXT_PATH = "game/FDTXT.DAT"

def analyze_specific_sub(res_idx, sub_idx):
    with open(FDTXT_PATH, 'rb') as f:
        data = f.read()
    
    count = struct.unpack_from('<I', data, 6)[0]
    rs = struct.unpack_from('<I', data, 10 + res_idx * 4)[0]
    re = struct.unpack_from('<I', data, 10 + (res_idx + 1) * 4)[0] if res_idx + 1 < count else len(data)
    
    rd = data[rs:re]
    sub_count = struct.unpack_from('<h', rd, 0)[0]
    
    if sub_idx < 0 or sub_idx >= sub_count:
        print(f"子项 {sub_idx} 超出范围 (0-{sub_count-1})")
        return
    
    off = struct.unpack_from('<h', rd, 2 + sub_idx * 2)[0]
    next_off = struct.unpack_from('<h', rd, 2 + (sub_idx + 1) * 2)[0] if sub_idx + 1 < sub_count else len(rd)
    
    text_data = rd[off:next_off]
    print(f"资源集 {res_idx}, 子项 {sub_idx}:")
    print(f"  偏移: {off}-{next_off}, 长度: {len(text_data)} 字节")
    
    # 打印原始字节
    print("  原始字节 (hex):")
    for i in range(0, min(len(text_data), 200), 16):
        hex_str = ' '.join(f'{b:02x}' for b in text_data[i:i+16])
        ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in text_data[i:i+16])
        print(f"    {i:04x}: {hex_str:<48s}  {ascii_str}")
    
    # 解析为16位值
    print("\n  解析为16位值:")
    words = []
    i = 0
    while i < len(text_data):
        if i + 2 > len(text_data):
            break
        word = struct.unpack_from('<h', text_data, i)[0]
        words.append((i, word))
        i += 2
    
    for pos, word in words[:50]:
        if word == -1:
            desc = "TEXT_END"
        elif word == -2:
            desc = "TEXT_NEWLINE"
        elif word == -3:
            desc = "TEXT_NEWLINE2"
        elif word == -4:
            desc = "TEXT_RECURSE1"
        elif word == -5:
            desc = "TEXT_RECURSE2"
        elif word == -6:
            desc = "TEXT_SHOW_NUM"
        elif word == -17:
            desc = "TEXT_PORTRAIT_F"
        elif word == -18:
            desc = "TEXT_PORTRAIT_S"
        elif word == -19:
            desc = "TEXT_CHAR_F"
        elif word == -20:
            desc = "TEXT_CHAR_S"
        elif word >= 0 and word < 128:
            desc = f"ASCII '{chr(word)}' ({word})"
        elif word >= 128 and word < 1824:
            desc = f"字符索引 {word}"
        else:
            desc = f"未知值 {word} (0x{word & 0xffff:04x})"
        print(f"    [{pos:04x}] {word:5d} (0x{word & 0xffff:04x}): {desc}")

if __name__ == "__main__":
    # 根据截图，应该是资源集1的子项0或1
    analyze_specific_sub(1, 0)
    print("\n" + "="*60 + "\n")
    analyze_specific_sub(1, 1)
