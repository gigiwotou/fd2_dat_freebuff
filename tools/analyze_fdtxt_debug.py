#!/usr/bin/env python3
"""
FDTXT.DAT 对话文本调试工具
显示指定资源集和子项的原始数据
"""

import struct
import sys
import os

CONTROL_CODES = {
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
}

def load_dat_resource(dat_data, index):
    count = struct.unpack_from('<I', dat_data, 6)[0]
    if index < 0 or index >= count - 1:
        return None
    
    offset_start = struct.unpack_from('<I', dat_data, 10 + index * 4)[0]
    offset_end = struct.unpack_from('<I', dat_data, 10 + (index + 1) * 4)[0]
    
    return dat_data[offset_start:offset_end]

def analyze_sub_texts(resource_data, resource_idx, sub_idx):
    """分析特定资源集的特定子项"""
    if len(resource_data) < 2:
        print(f"资源集 {resource_idx} 数据太小")
        return
    
    sub_count = struct.unpack_from('<h', resource_data, 0)[0]
    print(f"资源集 {resource_idx} 包含 {sub_count} 个子项")
    
    if sub_idx < 0 or sub_idx >= sub_count:
        print(f"子项索引 {sub_idx} 超出范围")
        return
    
    # 读取偏移表
    offsets = []
    for i in range(sub_count):
        offset = struct.unpack_from('<h', resource_data, 2 + i * 2)[0]
        offsets.append(offset)
    
    # 计算当前子项的结束位置
    if sub_idx + 1 < sub_count:
        sub_end = offsets[sub_idx + 1]
    else:
        sub_end = len(resource_data)
    
    sub_data = resource_data[offsets[sub_idx]:sub_end]
    
    print(f"\n子项 {sub_idx} (偏移: {offsets[sub_idx]}, 大小: {len(sub_data)} 字节):")
    print("=" * 80)
    
    # 解析文本
    words = []
    for i in range(0, len(sub_data), 2):
        if i + 1 >= len(sub_data):
            break
        word = struct.unpack_from('<h', sub_data, i)[0]
        words.append((i, word))
    
    print(f"总词数: {len(words)}")
    print(f"\n文本内容:")
    print("-" * 80)
    
    current_pos = 0
    text_chars = []
    
    for offset, word in words:
        if word in CONTROL_CODES:
            if word == -1:
                print(f"  [{offset:4d}] {CONTROL_CODES[word]}")
                break
            elif word == -2 or word == -3:
                print(f"  [{offset:4d}] {CONTROL_CODES[word]} [换行]")
            elif word == -6:
                next_word = words[offset // 2 + 1][1] if offset // 2 + 1 < len(words) else 0
                print(f"  [{offset:4d}] {CONTROL_CODES[word]} {next_word}")
            elif word in [-17, -18, -19, -20]:
                next_word = words[offset // 2 + 1][1] if offset // 2 + 1 < len(words) else 0
                print(f"  [{offset:4d}] {CONTROL_CODES[word]} 参数={next_word}")
            else:
                print(f"  [{offset:4d}] {CONTROL_CODES[word]}")
        else:
            # 尝试解码为大五码
            try:
                char = word.to_bytes(2, 'little', signed=True).decode('big5')
                text_chars.append(char)
                if offset % 32 == 0:
                    print(f"  [{offset:4d}] {char}")
            except:
                text_chars.append(f"[{word}]")
    
    print(f"\n完整文本: {''.join(text_chars)}")
    print("=" * 80)

def main():
    fdtxt_path = os.path.join("game", "FDTXT.DAT")
    
    if not os.path.exists(fdtxt_path):
        print(f"错误: 找不到 {fdtxt_path}")
        return
    
    with open(fdtxt_path, 'rb') as f:
        fdtxt_data = f.read()
    
    count = struct.unpack_from('<I', fdtxt_data, 6)[0]
    print(f"FDTXT.DAT 包含 {count} 个资源集")
    print()
    
    # 解析命令行参数
    if len(sys.argv) >= 3:
        res_idx = int(sys.argv[1])
        sub_idx = int(sys.argv[2])
        
        resource_data = load_dat_resource(fdtxt_data, res_idx)
        if resource_data:
            analyze_sub_texts(resource_data, res_idx, sub_idx)
    else:
        print("用法: python analyze_fdtxt_debug.py <资源集索引> <子项索引>")
        print("示例: python analyze_fdtxt_debug.py 5 2")

if __name__ == "__main__":
    main()
