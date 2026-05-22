import struct

def analyze_fdtxt_items_batch(dat_path, res_idx, max_subs=10):
    with open(dat_path, 'rb') as f:
        data = f.read()
    
    # Parse header
    file_size = len(data)
    count = struct.unpack_from('<I', data, 6)[0]
    
    print(f"文件大小: {file_size}")
    print(f"资源集数量: {count}")
    print()
    
    # Parse offsets
    offsets = []
    for i in range(count):
        off = struct.unpack_from('<I', data, 10 + i * 4)[0]
        offsets.append(off)
    
    if res_idx < 0 or res_idx >= count:
        print(f"资源集索引超出范围: {res_idx}")
        return
    
    rs = offsets[res_idx]
    re = offsets[res_idx + 1] if res_idx + 1 < count else file_size
    
    print(f"资源集 {res_idx}:")
    print(f"  偏移: {rs} - {re}")
    print(f"  大小: {re - rs} 字节")
    
    # Parse sub count
    sub_count = struct.unpack_from('<h', data, rs)[0]
    print(f"  子项数量: {sub_count}")
    print()
    
    # Parse sub offsets
    sub_offs = []
    for i in range(sub_count):
        off = struct.unpack_from('<h', data, rs + 2 + i * 2)[0]
        sub_offs.append(off)
    
    # Analyze each sub item
    print("=" * 80)
    print("子项分析:")
    print("=" * 80)
    
    items_to_analyze = min(max_subs, sub_count)
    results = []
    
    for sub_idx in range(items_to_analyze):
        ss = rs + sub_offs[sub_idx]
        se = rs + sub_offs[sub_idx + 1] if sub_idx + 1 < sub_count else re
        
        raw = data[ss:se]
        words = []
        for i in range(0, len(raw), 2):
            if i + 1 < len(raw):
                val = struct.unpack_from('<h', raw, i)[0]
                words.append(val)
        
        # Analyze content type
        text_chars = [v for v in words if v >= 0]
        special_cmds = [v for v in words if v < 0 and v != -1]
        has_end = -1 in words
        
        # Determine type
        if len(text_chars) > len(special_cmds):
            item_type = "对话内容"
        else:
            item_type = "控制指令"
        
        # Find special commands
        cmd_names = []
        for v in words:
            if v == -1:
                cmd_names.append("TEXT_END")
            elif v == -2:
                cmd_names.append("TEXT_NEWLINE")
            elif v == -3:
                cmd_names.append("TEXT_NEWLINE2")
            elif v == -4:
                cmd_names.append("TEXT_RECURSE1")
            elif v == -5:
                cmd_names.append("TEXT_RECURSE2")
            elif v == -6:
                cmd_names.append("TEXT_SHOW_NUM")
            elif v == -17:
                cmd_names.append("TEXT_PORTRAIT_F")
            elif v == -18:
                cmd_names.append("TEXT_PORTRAIT_S")
            elif v == -19:
                cmd_names.append("TEXT_CHAR_F")
            elif v == -20:
                cmd_names.append("TEXT_CHAR_S")
        
        result = {
            'sub_idx': sub_idx,
            'size': se - ss,
            'type': item_type,
            'text_count': len(text_chars),
            'cmd_count': len(special_cmds),
            'has_end': has_end,
            'commands': cmd_names,
            'first_char': text_chars[0] if text_chars else None,
        }
        results.append(result)
        
        print(f"\n子项 {sub_idx}:")
        print(f"  大小: {se - ss} 字节")
        print(f"  类型: {item_type}")
        print(f"  文字数量: {len(text_chars)}")
        print(f"  控制指令: {len(special_cmds)}")
        print(f"  包含结束标记: {has_end}")
        if cmd_names:
            print(f"  控制指令列表: {', '.join(cmd_names)}")
        if text_chars:
            print(f"  前几个文字索引: {text_chars[:5]}")
    
    # Summary
    print("\n" + "=" * 80)
    print("总结:")
    print("=" * 80)
    print(f"{'子项':<6} {'类型':<12} {'文字数':<8} {'指令数':<8} {'结束标记':<8}")
    print("-" * 80)
    for r in results:
        print(f"{r['sub_idx']:<6} {r['type']:<12} {r['text_count']:<8} {r['cmd_count']:<8} {'是' if r['has_end'] else '否':<8}")
    
    # Find first dialog
    first_dialog = None
    for r in results:
        if r['type'] == "对话内容" and r['has_end']:
            first_dialog = r
            break
    
    if first_dialog:
        print(f"\n第一关第一个对话分段: 子项 {first_dialog['sub_idx']}")
    else:
        print("\n未找到对话分段")

if __name__ == '__main__':
    analyze_fdtxt_items_batch('game/FDTXT.DAT', 0, 10)
