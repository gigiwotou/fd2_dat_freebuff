#!/usr/bin/env python3
"""
FDTXT.DAT 原始字节数据分析工具

功能：
1. 读取FDTXT.DAT文件
2. 解析偏移表
3. 输出指定资源集(res_idx)和子项(sub_idx)的原始字节数据
4. 将字节数据解释为int16_t值并显示
5. 标记出控制码(-1,-2,-3等)和普通字符的位置

基于IDA Pro反汇编的sub_111BA函数逻辑：
- 偏移表从字节6开始，每4字节一个偏移量
- 资源集大小 = 下一个偏移 - 当前偏移
"""

import struct
from pathlib import Path

# 文件路径
FDTXT_PATH = "game/FDTXT.DAT"

# 控制码定义（基于IDA Pro反汇编）
CONTROL_CODES = {
    -1: "文本结束",
    -2: "换行",
    -3: "换行+清除状态",
    -4: "递归调用dword_53A7D",
    -5: "递归调用dword_53ADD",
    -6: "显示数值dword_53AE1",
    -17: "加载头像(正面)",
    -18: "加载头像(侧面)",
    -19: "从dword_53A45加载角色头像(正面)",
    -20: "从dword_53A45加载角色头像(侧面)",
}

# 带参数的控制码（后面跟着2字节参数）
CONTROL_CODES_WITH_PARAM = [-17, -18, -19, -20]


def analyze_fdtxt(res_idx=0, sub_idx=0):
    """分析FDTXT.DAT中指定资源集和子项的原始字节数据"""
    
    # 1. 读取FDTXT.DAT文件
    with open(FDTXT_PATH, 'rb') as f:
        data = f.read()
    
    print(f"文件大小: {len(data)} 字节")
    print()
    
    # 2. 解析偏移表（从字节6开始，每4字节一个偏移）
    print("=" * 80)
    print("解析偏移表（从字节6开始）")
    print("=" * 80)
    
    offsets = []
    pos = 6
    while pos + 4 <= len(data):
        offset = struct.unpack_from('<I', data, pos)[0]
        if offset > len(data):
            break
        offsets.append(offset)
        pos += 4
    
    print(f"共找到 {len(offsets)} 个资源集偏移")
    print()
    
    # 显示前几个偏移
    for i in range(min(10, len(offsets))):
        print(f"  资源集 {i}: 偏移 {offsets[i]} (0x{offsets[i]:06X})")
    if len(offsets) > 10:
        print(f"  ... (还有 {len(offsets) - 10} 个)")
    print()
    
    # 3. 获取指定资源集
    if res_idx < 0 or res_idx >= len(offsets):
        print(f"错误: 资源集索引 {res_idx} 超出范围 (0-{len(offsets)-1})")
        return
    
    res_start = offsets[res_idx]
    res_end = offsets[res_idx + 1] if res_idx + 1 < len(offsets) else len(data)
    res_data = data[res_start:res_end]
    
    print(f"资源集 {res_idx}:")
    print(f"  文件偏移: {res_start} - {res_end}")
    print(f"  大小: {len(res_data)} 字节")
    print()
    
    # 4. 解析资源集内部结构
    # 前2字节是子项数量（16位有符号整数）
    if len(res_data) < 2:
        print("错误: 资源集数据太小")
        return
    
    sub_count = struct.unpack_from('<h', res_data, 0)[0]
    print(f"  子项数量: {sub_count}")
    print()
    
    # 子项偏移表从字节2开始，每2字节一个偏移（相对资源集起始的偏移）
    if sub_idx < 0 or sub_idx >= sub_count:
        print(f"错误: 子项索引 {sub_idx} 超出范围 (0-{sub_count-1})")
        return
    
    sub_offset = struct.unpack_from('<h', res_data, 2 + sub_idx * 2)[0]
    if sub_idx + 1 < sub_count:
        next_sub_offset = struct.unpack_from('<h', res_data, 2 + (sub_idx + 1) * 2)[0]
    else:
        next_sub_offset = len(res_data)
    
    sub_data = res_data[sub_offset:next_sub_offset]
    
    print(f"子项 {sub_idx}:")
    print(f"  相对偏移: {sub_offset} - {next_sub_offset}")
    print(f"  绝对偏移: {res_start + sub_offset} - {res_start + next_sub_offset}")
    print(f"  大小: {len(sub_data)} 字节")
    print()
    
    # 5. 显示原始字节数据
    print("=" * 80)
    print("原始字节数据（十六进制）")
    print("=" * 80)
    
    for i in range(0, len(sub_data), 16):
        chunk = sub_data[i:i+16]
        hex_str = ' '.join(f'{b:02X}' for b in chunk)
        ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in chunk)
        print(f"  {i:04X}: {hex_str:<48s} {ascii_str}")
    print()
    
    # 6. 将字节数据解释为int16_t值并显示
    print("=" * 80)
    print("解析为int16_t值（小端序）")
    print("=" * 80)
    print(f"{'偏移':<8} {'字节':<12} {'int16值':<10} {'类型':<15} {'说明'}")
    print("-" * 80)
    
    i = 0
    while i + 2 <= len(sub_data):
        # 读取int16_t值
        value = struct.unpack_from('<h', sub_data, i)[0]
        byte_str = f"{sub_data[i]:02X} {sub_data[i+1]:02X}"
        offset_str = f"+{i:04d}"
        
        # 判断类型
        if value in CONTROL_CODES:
            value_type = "控制码"
            description = CONTROL_CODES[value]
        elif value < 0:
            value_type = "未知负值"
            description = "可能为特殊控制码"
        else:
            value_type = "普通字符"
            description = f"字体索引 {value}"
        
        print(f"  {offset_str:<8} {byte_str:<12} {value:<10} {value_type:<15} {description}")
        
        # 检查是否有参数
        if value in CONTROL_CODES_WITH_PARAM:
            if i + 4 <= len(sub_data):
                param = struct.unpack_from('<h', sub_data, i + 2)[0]
                param_bytes = f"{sub_data[i+2]:02X} {sub_data[i+3]:02X}"
                print(f"    {'参数:':<8} {param_bytes:<12} {param:<10} 参数值")
                i += 4
            else:
                print(f"    {'参数:':<8} {'N/A':<12} {'N/A':<10} 数据不足")
                i += 2
        else:
            i += 2
    
    print()
    
    # 7. 统计分析
    control_count = 0
    char_count = 0
    unknown_count = 0
    
    i = 0
    while i + 2 <= len(sub_data):
        value = struct.unpack_from('<h', sub_data, i)[0]
        if value in CONTROL_CODES:
            control_count += 1
            if value in CONTROL_CODES_WITH_PARAM:
                i += 4
                continue
        elif value < 0:
            unknown_count += 1
        else:
            char_count += 1
        i += 2
    
    print("=" * 80)
    print("统计分析")
    print("=" * 80)
    print(f"  控制码: {control_count} 个")
    print(f"  普通字符: {char_count} 个")
    print(f"  未知负值: {unknown_count} 个")
    print(f"  总计: {control_count + char_count + unknown_count} 个int16_t值")


if __name__ == "__main__":
    # 分析资源集0和子项0
    analyze_fdtxt(res_idx=0, sub_idx=0)
