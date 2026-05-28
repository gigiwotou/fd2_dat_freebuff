"""检查资源1开头的数据结构"""

import struct

def check_res1_header():
    with open('game/FDTXT.DAT', 'rb') as f:
        data = f.read()
    
    # 读取资源1
    count = struct.unpack_from('<I', data, 6)[0]
    offsets = []
    for i in range(count):
        off = struct.unpack_from('<I', data, 10 + i * 4)[0]
        offsets.append(off)
    
    rs = offsets[1]
    re = offsets[2] if 2 < count else len(data)
    
    print(f"资源1范围: 0x{rs:X} - 0x{re:X}")
    print(f"资源1大小: {re - rs} 字节")
    
    rd = data[rs:]
    
    # 打印前200字节的原始hex
    print("\n=== 资源1前200字节 (hex) ===")
    for i in range(0, min(200, len(rd)), 16):
        hex_str = ' '.join(f'{b:02x}' for b in rd[i:i+16])
        ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in rd[i:i+16])
        print(f"  {i:04x}: {hex_str:<48s} {ascii_str}")
    
    # 解析子项数量
    sub_count = struct.unpack_from('<h', rd, 0)[0]
    print(f"\n子项数量 (word at 0): {sub_count}")
    
    # 解析子项偏移表
    print("\n=== 子项偏移表 (前10个) ===")
    for i in range(min(10, sub_count)):
        off = struct.unpack_from('<h', rd, 2 + i * 2)[0]
        print(f"  子项{i} 偏移: {off} (0x{off:X})")
    
    # 检查偏移158之前的数据
    sub0_off = struct.unpack_from('<h', rd, 2)[0]
    print(f"\n=== 子项0之前数据 (偏移0到{sub0_off}) ===")
    print(f"大小: {sub0_off} 字节 = {sub0_off // 2} words")
    
    # 解析为words
    for i in range(sub0_off // 2):
        val = struct.unpack_from('<h', rd, i * 2)[0]
        if i < 2:
            continue  # 跳过子项数量和子项0偏移
        if val == -1:
            print(f"  word[{i}] = {val} (TEXT_END)")
        elif val == -2:
            print(f"  word[{i}] = {val} (NEWLINE)")
        elif val == -3:
            print(f"  word[{i}] = {val} (NEWLINE2)")
        elif val in [-17, -18, -19, -20]:
            cmd_name = {-17: "PORTRAIT_F", -18: "PORTRAIT_S", -19: "CHAR_F", -20: "CHAR_S"}[val]
            if i + 1 < sub0_off // 2:
                param = struct.unpack_from('<h', rd, (i + 1) * 2)[0]
                print(f"  word[{i}] = {val} ({cmd_name}), word[{i+1}] = {param}")
        elif val >= 0 and val < 0x8000:
            pass  # 跳过普通字符
        else:
            print(f"  word[{i}] = {val} (0x{val:04X})")
    
    # 检查子项0之前的内容是否包含对话
    print(f"\n=== 子项0之前的内容分析 ===")
    has_portrait = False
    has_text = False
    for i in range(2, sub0_off // 2):
        val = struct.unpack_from('<h', rd, i * 2)[0]
        if val in [-17, -18, -19, -20]:
            has_portrait = True
            cmd_name = {-17: "PORTRAIT_F", -18: "PORTRAIT_S", -19: "CHAR_F", -20: "CHAR_S"}[val]
            param = struct.unpack_from('<h', rd, (i + 1) * 2)[0] if i + 1 < sub0_off // 2 else 0
            print(f"  发现头像命令: {cmd_name}({param}) at word[{i}]")
        if val >= 0 and val < 0x8000:
            has_text = True
    
    if has_portrait or has_text:
        print("  -> 子项0之前确实包含对话数据！")
    else:
        print("  -> 子项0之前可能只是填充数据或索引表")

if __name__ == '__main__':
    check_res1_header()
