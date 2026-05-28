"""验证FDTXT资源结构：子项0之前的数据是第一个对话还是其他"""

import struct

def verify_structure():
    with open('game/FDTXT.DAT', 'rb') as f:
        data = f.read()
    
    count = struct.unpack_from('<I', data, 6)[0]
    offsets = []
    for i in range(count):
        off = struct.unpack_from('<I', data, 10 + i * 4)[0]
        offsets.append(off)
    
    # 检查资源1
    rs = offsets[1]
    rd = data[rs:]
    
    sub_count = struct.unpack_from('<h', rd, 0)[0]
    print(f"子项数量: {sub_count}")
    print(f"偏移表大小: {sub_count * 2} 字节 (从偏移2到偏移{2 + sub_count * 2})")
    
    # 偏移表结束位置
    table_end = 2 + sub_count * 2
    print(f"偏移表结束于: {table_end}")
    print(f"子项0偏移: {struct.unpack_from('<h', rd, 2)[0]}")
    
    # 子项0之前有什么？
    print(f"\n=== 检查偏移表区域 (2 到 {table_end}) ===")
    for i in range(sub_count):
        off = struct.unpack_from('<h', rd, 2 + i * 2)[0]
        print(f"  子项{i}: 偏移 {off}")
        if off < 0:
            print(f"    -> 负数偏移，可能是无效/占位")
    
    # 子项0偏移是158，偏移表结束于70 (2 + 34*2)
    # 70到158之间是什么？
    print(f"\n=== 偏移表结束(70)到子项0(158)之间的数据 ===")
    print(f"大小: {158 - 70} 字节 = {(158 - 70) // 2} words")
    
    for i in range(70, 158, 2):
        val = struct.unpack_from('<h', rd, i)[0]
        word_idx = i // 2
        if val == -1:
            print(f"  word[{word_idx}] (字节{i}) = {val} (TEXT_END)")
        elif val == -2:
            print(f"  word[{word_idx}] (字节{i}) = {val} (NEWLINE)")
        elif val == -3:
            print(f"  word[{word_idx}] (字节{i}) = {val} (NEWLINE2)")
        elif val in [-17, -18, -19, -20]:
            cmd = {-17: "PORTRAIT_F", -18: "PORTRAIT_S", -19: "CHAR_F", -20: "CHAR_S"}[val]
            next_val = struct.unpack_from('<h', rd, i + 2)[0]
            print(f"  word[{word_idx}] (字节{i}) = {val} ({cmd}), next={next_val}")
        elif val >= 0 and val < 0x8000:
            pass  # 普通字符，不显示
        else:
            print(f"  word[{word_idx}] (字节{i}) = {val} (0x{val:04X})")
    
    print(f"\n=== 分析 ===")
    print(f"偏移表: 字节 2-69 (34个偏移)")
    print(f"空白/填充: 字节 70-157 (88字节 = 44words)")
    print(f"子项0: 字节 158+")
    
    # 检查偏移70-157之间是否有头像命令
    has_portrait = False
    for i in range(70, 158, 2):
        val = struct.unpack_from('<h', rd, i)[0]
        if val in [-17, -18, -19, -20]:
            has_portrait = True
            cmd = {-17: "PORTRAIT_F", -18: "PORTRAIT_S", -19: "CHAR_F", -20: "CHAR_S"}[val]
            next_val = struct.unpack_from('<h', rd, i + 2)[0]
            print(f"  发现: {cmd}({next_val}) at 字节{i}")
    
    if not has_portrait:
        print(f"  -> 这段区域没有头像命令，可能是填充数据")

if __name__ == '__main__':
    verify_structure()
