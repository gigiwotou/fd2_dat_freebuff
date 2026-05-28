"""详细分析子项0之前的对话数据（真正的第一个对话）"""

import struct

def analyze_first_dialog():
    with open('game/FDTXT.DAT', 'rb') as f:
        data = f.read()
    
    count = struct.unpack_from('<I', data, 6)[0]
    offsets = []
    for i in range(count):
        off = struct.unpack_from('<I', data, 10 + i * 4)[0]
        offsets.append(off)
    
    rs = offsets[1]
    rd = data[rs:]
    sub0_off = 158
    
    print("=== 子项0之前的对话数据 (word[0] 到 word[78]) ===")
    
    for i in range(sub0_off // 2):
        val = struct.unpack_from('<h', rd, i * 2)[0]
        
        if val == -1:
            print(f"  [{i}] = {val} (TEXT_END) - 对话结束")
        elif val == -2:
            print(f"  [{i}] = {val} (NEWLINE)")
        elif val == -3:
            print(f"  [{i}] = {val} (NEWLINE2) - 等待按键")
        elif val == -17:
            print(f"  [{i}] = {val} (PORTRAIT_F)")
            i += 1
            param = struct.unpack_from('<h', rd, i * 2)[0]
            print(f"  [{i}] = {param} (portrait_id)")
        elif val == -18:
            print(f"  [{i}] = {val} (PORTRAIT_S)")
            i += 1
            param = struct.unpack_from('<h', rd, i * 2)[0]
            print(f"  [{i}] = {param} (portrait_id)")
        elif val == -19:
            print(f"  [{i}] = {val} (CHAR_F)")
            i += 1
            param = struct.unpack_from('<h', rd, i * 2)[0]
            print(f"  [{i}] = {param} (char_db_idx)")
        elif val == -20:
            print(f"  [{i}] = {val} (CHAR_S)")
            i += 1
            param = struct.unpack_from('<h', rd, i * 2)[0]
            print(f"  [{i}] = {param} (char_db_idx)")
        elif val >= 0 and val < 0x8000:
            print(f"  [{i}] = {val} (字符)")
        else:
            print(f"  [{i}] = {val} (0x{val:04X})")
    
    print("\n=== 对比：子项0的内容 ===")
    sub_data = rd[sub0_off:]
    for i in range(min(30, len(sub_data) // 2)):
        val = struct.unpack_from('<h', sub_data, i * 2)[0]
        
        if val == -1:
            print(f"  [{i}] = {val} (TEXT_END)")
            break
        elif val == -2:
            print(f"  [{i}] = {val} (NEWLINE)")
        elif val == -3:
            print(f"  [{i}] = {val} (NEWLINE2)")
        elif val == -17:
            print(f"  [{i}] = {val} (PORTRAIT_F)")
            i += 1
            param = struct.unpack_from('<h', sub_data, i * 2)[0]
            print(f"  [{i}] = {param} (portrait_id)")
        elif val == -18:
            print(f"  [{i}] = {val} (PORTRAIT_S)")
            i += 1
            param = struct.unpack_from('<h', sub_data, i * 2)[0]
            print(f"  [{i}] = {param} (portrait_id)")
        elif val == -19:
            print(f"  [{i}] = {val} (CHAR_F)")
            i += 1
            param = struct.unpack_from('<h', sub_data, i * 2)[0]
            print(f"  [{i}] = {param} (char_db_idx)")
        elif val == -20:
            print(f"  [{i}] = {val} (CHAR_S)")
            i += 1
            param = struct.unpack_from('<h', sub_data, i * 2)[0]
            print(f"  [{i}] = {param} (char_db_idx)")
        elif val >= 0 and val < 0x8000:
            print(f"  [{i}] = {val} (字符)")
        else:
            print(f"  [{i}] = {val} (0x{val:04X})")
    
    print("\n=== 结论 ===")
    print("资源1的结构：")
    print("  - 前79个word (0-157字节): 第一个对话事件，包含头像切换和对话内容")
    print("  - 子项数量: 34")
    print("  - 子项0: 第二个对话事件 (偏移158)")
    print("  - 子项1: 第三个对话事件 (偏移336)")
    print("  ...")
    print("\n这意味着：")
    print("  - 游戏实际使用时，sub 0 应该从word[0]开始渲染，包括前面的对话")
    print("  - 或者资源开头的数据是某种前置内容，需要特殊处理")

if __name__ == '__main__':
    analyze_first_dialog()
