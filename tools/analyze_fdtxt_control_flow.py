"""
分析FDTXT.DAT资源0/子项0的完整控制码序列
找出对话是如何分段和连续播放的
"""
import struct

def analyze_fdtxt_control_flow():
    with open("game/FDTXT.DAT", "rb") as f:
        fdtxt = f.read()
    
    # 资源数量
    count = struct.unpack_from('<I', fdtxt, 6)[0]
    
    # 读取偏移表
    offsets = []
    for i in range(count):
        off = struct.unpack_from('<I', fdtxt, 10 + i*4)[0]
        offsets.append(off)
    
    # 读取资源0
    res_start = offsets[0]
    res_end = offsets[1] if 1 < count else len(fdtxt)
    res_data = fdtxt[res_start:res_end]
    
    # 子项数量
    sub_count = struct.unpack_from('<h', res_data, 0)[0]
    
    # 子项偏移表
    sub_offsets = []
    for i in range(sub_count):
        off = struct.unpack_from('<h', res_data, 2 + i*2)[0]
        sub_offsets.append(off)
    
    # 分析子项0
    text_start = sub_offsets[0]
    text_end = sub_offsets[1] if 1 < sub_count else len(res_data)
    
    print(f"=== FDTXT资源0/子项0 完整分析 ===")
    print(f"文本范围: {text_start} - {text_end} ({text_end - text_start} 字节)")
    print(f"控制码统计:\n")
    
    # 控制码定义
    control_codes = {
        -1: "TEXT_END",
        -2: "TEXT_NEWLINE",
        -3: "TEXT_NEWLINE2",
        -4: "TEXT_RECURSE1",
        -5: "TEXT_RECURSE2",
        -6: "TEXT_SHOW_NUM",
        -17: "TEXT_PORTRAIT_F",
        -18: "TEXT_PORTRAIT_S",
        -19: "TEXT_CHAR_F",
        -20: "TEXT_CHAR_S",
        -2: "TEXT_DELAY"  # alias
    }
    
    # 解析所有控制码及其位置
    pos = text_start
    code_sequence = []
    code_counts = {}
    char_count = 0
    line_count = 0
    
    while pos < text_end:
        word = struct.unpack_from('<h', res_data, pos)[0]
        pos += 2
        
        if word == -1:
            code_sequence.append(("TEXT_END", pos-2))
            code_counts[word] = code_counts.get(word, 0) + 1
            break
        elif word == -2:
            code_sequence.append(("TEXT_NEWLINE", pos-2))
            code_counts[word] = code_counts.get(word, 0) + 1
            line_count += 1
        elif word == -3:
            code_sequence.append(("TEXT_NEWLINE2", pos-2))
            code_counts[word] = code_counts.get(word, 0) + 1
            line_count += 1
        elif word == -4:
            code_sequence.append(("TEXT_RECURSE1", pos-2))
            code_counts[word] = code_counts.get(word, 0) + 1
        elif word == -5:
            code_sequence.append(("TEXT_RECURSE2", pos-2))
            code_counts[word] = code_counts.get(word, 0) + 1
        elif word == -6:
            code_sequence.append(("TEXT_SHOW_NUM", pos-2))
            code_counts[word] = code_counts.get(word, 0) + 1
            pos += 2  # skip parameter
        elif word == -17:
            pid = struct.unpack_from('<h', res_data, pos)[0]
            pos += 2
            code_sequence.append((f"TEXT_PORTRAIT_F(pid={pid})", pos-4))
            code_counts[word] = code_counts.get(word, 0) + 1
        elif word == -18:
            pid = struct.unpack_from('<h', res_data, pos)[0]
            pos += 2
            code_sequence.append((f"TEXT_PORTRAIT_S(pid={pid})", pos-4))
            code_counts[word] = code_counts.get(word, 0) + 1
        elif word == -19:
            cid = struct.unpack_from('<h', res_data, pos)[0]
            pos += 2
            code_sequence.append((f"TEXT_CHAR_F(cid={cid})", pos-4))
            code_counts[word] = code_counts.get(word, 0) + 1
        elif word == -20:
            cid = struct.unpack_from('<h', res_data, pos)[0]
            pos += 2
            code_sequence.append((f"TEXT_CHAR_S(cid={cid})", pos-4))
            code_counts[word] = code_counts.get(word, 0) + 1
        elif word >= 0:
            char_count += 1
        else:
            code_sequence.append((f"UNKNOWN({word})", pos-2))
    
    # 打印统计
    print("控制码出现次数:")
    print("-" * 50)
    for code, name in control_codes.items():
        count = code_counts.get(code, 0)
        if count > 0:
            print(f"  {name.ljust(18)}: {count}次")
    
    print(f"\n普通字符数: {char_count}")
    print(f"换行符总数: {line_count}")
    
    # 打印完整序列（前100个条目）
    print(f"\n完整控制码序列 (前100项):")
    print("-" * 80)
    for i, (name, offset) in enumerate(code_sequence[:100]):
        print(f"  {i:3d}. [{offset:5d}] {name}")
    
    if len(code_sequence) > 100:
        print(f"  ... 还有 {len(code_sequence) - 100} 项")
    
    # 分析对话分段
    print(f"\n对话分段分析:")
    print("-" * 80)
    
    segment_num = 0
    current_segment = []
    for name, offset in code_sequence:
        if "TEXT_CHAR" in name or "TEXT_PORTRAIT" in name or name == "TEXT_NEWLINE":
            current_segment.append(name)
        elif name == "TEXT_NEWLINE2":
            current_segment.append(name)
            print(f"  段{segment_num}: {' -> '.join(current_segment)}")
            segment_num += 1
            current_segment = []
        elif name == "TEXT_END":
            if current_segment:
                print(f"  段{segment_num}: {' -> '.join(current_segment)}")
            break

if __name__ == "__main__":
    analyze_fdtxt_control_flow()
