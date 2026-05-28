"""验证IDA中的索引逻辑：v11 = (__int16 *)(*(__int16 *)(a2 + 2 * a3) + a2)

这意味着：
- a2 = 资源起始地址
- a3 = 子项索引
- *(int16*)(a2 + 2*a3) = 偏移值（从偏移表读取）
- 最终指针 = a2 + 偏移值

关键：资源开头没有"子项数量"字段！
字节0-1 就是子项0的偏移
字节2-3 就是子项1的偏移
...
"""

import struct

def verify_correct_indexing():
    with open('game/FDTXT.DAT', 'rb') as f:
        data = f.read()
    
    count = struct.unpack_from('<I', data, 6)[0]
    offsets = []
    for i in range(count):
        off = struct.unpack_from('<I', data, 10 + i * 4)[0]
        offsets.append(off)
    
    # 资源1
    rs = offsets[1]
    rd = data[rs:]
    
    print("=== 根据IDA代码的正确索引方式 ===")
    print("资源开头就是偏移表，没有子项数量字段")
    print()
    
    # 按照IDA的逻辑读取
    for sub_idx in range(5):
        # IDA: *(int16*)(a2 + 2*sub_idx)
        offset = struct.unpack_from('<h', rd, sub_idx * 2)[0]
        print(f"sub {sub_idx}: 偏移 = *(int16*)(资源+{sub_idx*2}) = {offset}")
        
        if offset < 0 or offset >= (offsets[2] - offsets[1]):
            print(f"  -> 偏移无效")
            continue
        
        # 读取该偏移处的内容
        sub_data = rd[offset:]
        print(f"  -> 前5个word:")
        for i in range(min(5, len(sub_data) // 2)):
            val = struct.unpack_from('<h', sub_data, i * 2)[0]
            if val == -1:
                print(f"     [{i}] = {val} (TEXT_END)")
                break
            elif val == -2:
                print(f"     [{i}] = {val} (NEWLINE)")
            elif val == -3:
                print(f"     [{i}] = {val} (NEWLINE2)")
            elif val in [-17, -18, -19, -20]:
                cmd = {-17: "PORTRAIT_F", -18: "PORTRAIT_S", -19: "CHAR_F", -20: "CHAR_S"}[val]
                next_val = struct.unpack_from('<h', sub_data, (i + 1) * 2)[0]
                print(f"     [{i}] = {val} ({cmd})")
                print(f"     [{i+1}] = {next_val} (参数)")
            elif val >= 0 and val < 0x8000:
                print(f"     [{i}] = {val} (字符)")
            else:
                print(f"     [{i}] = {val} (0x{val:04X})")
    
    print("\n=== 验证：原来代码中错误的索引方式 ===")
    print("原代码认为：")
    print("  字节0-1 = 子项数量 (34)")
    print("  字节2-N = 偏移表")
    print("  sub 0 读取偏移表第一个值 = 158")
    print()
    print("但IDA显示：")
    print("  字节0-1 = sub 0 的偏移 (34)")
    print("  字节2-3 = sub 1 的偏移 (158)")
    print("  所以原代码的 sub 0 实际是 IDA 的 sub 1!")")
    print()
    print("这就是为什么 --sub 0 渲染的是第二句话！")

if __name__ == '__main__':
    verify_correct_indexing()
