"""分析资源1子项0的完整结构，找出所有对话分隔点"""

import struct

def analyze_sub0():
    with open('game/FDTXT.DAT', 'rb') as f:
        data = f.read()
    
    # 读取资源1
    count = struct.unpack_from('<I', data, 6)[0]
    offsets = []
    for i in range(count):
        off = struct.unpack_from('<I', data, 10 + i * 4)[0]
        offsets.append(off)
    
    rs = offsets[1]
    rd = data[rs:]
    
    # 子项0的偏移
    sub_off = struct.unpack_from('<h', rd, 2)[0]
    print(f"子项0偏移: {sub_off} (0x{sub_off:X})")
    
    # 读取子项0的完整数据
    sub_data = rd[sub_off:]
    
    print("\n=== 子项0完整分析（按对话块分组） ===")
    print("对话块由 PORTRAIT/CHAR 命令分隔")
    
    block_num = 0
    j = 0
    in_block = False
    block_start = 0
    
    while j < len(sub_data) // 2:
        val = struct.unpack_from('<h', sub_data, j * 2)[0]
        
        if val == -1:  # TEXT_END
            print(f"  [{j}] = {val} (TEXT_END) - 对话块{block_num}结束")
            break
        elif val in [-17, -18, -19, -20]:  # 头像命令
            cmd_name = {
                -17: "TEXT_PORTRAIT_F",
                -18: "TEXT_PORTRAIT_S", 
                -19: "TEXT_CHAR_F",
                -20: "TEXT_CHAR_S"
            }[val]
            
            j += 1
            param = struct.unpack_from('<h', sub_data, j * 2)[0]
            
            block_num += 1
            print(f"\n--- 对话块 {block_num} ---")
            print(f"  [{j-1}] = {val} ({cmd_name})")
            print(f"  [{j}] = {param} (参数)")
            in_block = True
            block_start = j + 1
            
        elif val == -2:
            print(f"  [{j}] = {val} (NEWLINE)")
        elif val == -3:
            print(f"  [{j}] = {val} (NEWLINE2)")
        elif val >= 0 and val < 0x8000:
            # 普通字符，显示第一个和最后一个
            if j == block_start or (j > 0 and struct.unpack_from('<h', sub_data, (j-1)*2)[0] < 0 and struct.unpack_from('<h', sub_data, (j-1)*2)[0] >= -20):
                print(f"  [{j}] = {val} (char) ...")
        else:
            print(f"  [{j}] = {val} (0x{val:04X})")
        
        j += 1
    
    print(f"\n总共发现 {block_num} 个对话块")
    
    # 现在详细分析每个对话块的起始位置
    print("\n=== 对话块详细位置 ===")
    j = 0
    block_num = 0
    while j < len(sub_data) // 2:
        val = struct.unpack_from('<h', sub_data, j * 2)[0]
        if val in [-17, -18, -19, -20]:
            block_num += 1
            cmd_name = {-17: "PORTRAIT_F", -18: "PORTRAIT_S", -19: "CHAR_F", -20: "CHAR_S"}[val]
            param = struct.unpack_from('<h', sub_data, (j+1) * 2)[0]
            print(f"对话块{block_num}: 位置 {j}, 命令 {cmd_name}, 参数 {param}")
        j += 1

if __name__ == '__main__':
    analyze_sub0()
