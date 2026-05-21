#!/usr/bin/env python3
"""
FDTXT.DAT 原始字节分析工具
输出原始int16值，帮助调试
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

def analyze_raw_bytes(resource_data, resource_idx, sub_idx):
    """分析特定资源集的特定子项的原始字节"""
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
    
    print(f"偏移表: {offsets}")
    
    # 分析当前子项
    sub_start = offsets[sub_idx]
    if sub_idx + 1 < sub_count:
        sub_end = offsets[sub_idx + 1]
    else:
        sub_end = len(resource_data)
    
    print(f"\n子项 {sub_idx}: 起始偏移={sub_start}, 结束偏移={sub_end}, 大小={sub_end - sub_start} 字节")
    print(f"对应的子项数量: {sub_count}")
    
    # 读取当前子项的所有int16值
    print(f"\n原始int16值序列 (从偏移 {sub_start} 到 {sub_end}):")
    print("=" * 80)
    
    word_count = (sub_end - sub_start) // 2
    print(f"子项 {sub_idx} 总词数: {word_count}")
    print(f"\n序号 | 偏移 | int16值 | 十六进制 | 类型 | 内容")
    print("-" * 80)
    
    for i in range(word_count):
        offset = sub_start + i * 2
        if offset + 1 >= len(resource_data):
            break
        word = struct.unpack_from('<h', resource_data, offset)[0]
        
        if word in CONTROL_CODES:
            ctrl_name = CONTROL_CODES[word]
            if word == -1:
                print(f"{i:4d} | {offset:4d} | {word:6d} | 0x{word & 0xFFFF:04X} | {ctrl_name:15s} | [文本结束]")
                break  # TEXT_END后应该停止
            elif word in [-17, -18, -19, -20]:
                # 控制码后面跟参数
                if i + 1 < word_count:
                    next_offset = sub_start + (i + 1) * 2
                    next_word = struct.unpack_from('<h', resource_data, next_offset)[0]
                    print(f"{i:4d} | {offset:4d} | {word:6d} | 0x{word & 0xFFFF:04X} | {ctrl_name:15s} | 参数={next_word}")
                    i += 1  # 跳过参数
                else:
                    print(f"{i:4d} | {offset:4d} | {word:6d} | 0x{word & 0xFFFF:04X} | {ctrl_name:15s} | [无参数!]")
            elif word in [-2, -3]:
                print(f"{i:4d} | {offset:4d} | {word:6d} | 0x{word & 0xFFFF:04X} | {ctrl_name:15s} | [换行]")
            else:
                print(f"{i:4d} | {offset:4d} | {word:6d} | 0x{word & 0xFFFF:04X} | {ctrl_name:15s} |")
        else:
            # 尝试解码为大五码
            try:
                char = word.to_bytes(2, 'little', signed=True).decode('big5')
                print(f"{i:4d} | {offset:4d} | {word:6d} | 0x{word & 0xFFFF:04X} | {'':15s} | {char}")
            except:
                print(f"{i:4d} | {offset:4d} | {word:6d} | 0x{word & 0xFFFF:04X} | {'':15s} | [无效:{word}]")
    
    print("=" * 80)
    
    # 输出完整文本
    print(f"\n子项 {sub_idx} 的完整文本:")
    text = []
    for i in range(word_count):
        offset = sub_start + i * 2
        if offset + 1 >= len(resource_data):
            break
        word = struct.unpack_from('<h', resource_data, offset)[0]
        if word == -1:
            break
        elif word in [-17, -18, -19, -20]:
            if i + 1 < word_count:
                next_word = struct.unpack_from('<h', resource_data, sub_start + (i + 1) * 2)[0]
                text.append(f"[头像:{next_word}]")
                i += 1
            else:
                text.append("[头像:无参数]")
        elif word == -2 or word == -3:
            text.append("[换行]")
        elif word >= 0:
            try:
                char = word.to_bytes(2, 'little', signed=True).decode('big5')
                text.append(char)
            except:
                text.append(f"[{word}]")
    
    print(''.join(text))

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
    
    if len(sys.argv) >= 3:
        res_idx = int(sys.argv[1])
        sub_idx = int(sys.argv[2])
        
        resource_data = load_dat_resource(fdtxt_data, res_idx)
        if resource_data:
            analyze_raw_bytes(resource_data, res_idx, sub_idx)
    else:
        print("用法: python analyze_fdtxt_raw.py <资源集索引> <子项索引>")
        print("示例: python analyze_fdtxt_raw.py 5 2")

if __name__ == "__main__":
    main()
