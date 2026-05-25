#!/usr/bin/env python3
"""
分析FDTXT.DAT资源1子项1的完整内容
输出所有控制码和字符的序列
"""

import struct
import os

# 控制码定义
TEXT_END = -1
TEXT_NEWLINE = -2
TEXT_NEWLINE2 = -3
TEXT_RECURSE1 = -4
TEXT_RECURSE2 = -5
TEXT_SHOW_NUM = -6
TEXT_PORTRAIT_F = -17
TEXT_PORTRAIT_S = -18
TEXT_CHAR_F = -19
TEXT_CHAR_S = -20

# 控制码名称映射
CONTROL_CODES = {
    TEXT_END: "TEXT_END (文本结束)",
    TEXT_NEWLINE: "TEXT_NEWLINE (换行)",
    TEXT_NEWLINE2: "TEXT_NEWLINE2 (换行+等待按键)",
    TEXT_RECURSE1: "TEXT_RECURSE1 (递归文本1)",
    TEXT_RECURSE2: "TEXT_RECURSE2 (递归文本2)",
    TEXT_SHOW_NUM: "TEXT_SHOW_NUM (显示数字)",
    TEXT_PORTRAIT_F: "TEXT_PORTRAIT_F (正面头像)",
    TEXT_PORTRAIT_S: "TEXT_PORTRAIT_S (侧面头像)",
    TEXT_CHAR_F: "TEXT_CHAR_F (正面角色)",
    TEXT_CHAR_S: "TEXT_CHAR_S (侧面角色)",
}

def parse_fdtxt(filepath):
    """解析FDTXT.DAT文件"""
    with open(filepath, 'rb') as f:
        # 读取文件头6字节 (LLLLLL魔数)
        magic = f.read(6)
        print(f"魔数: {magic}")
        
        # 读取资源数量 (4字节)
        resource_count = struct.unpack('<I', f.read(4))[0]
        print(f"资源数量: {resource_count}")
        
        # 读取资源偏移表 (每个资源4字节)
        offsets = []
        for i in range(resource_count):
            offset = struct.unpack('<I', f.read(4))[0]
            offsets.append(offset)
        
        print(f"\n资源偏移表:")
        for i, offset in enumerate(offsets[:5]):  # 只显示前5个
            size = offsets[i+1] - offset if i+1 < len(offsets) else 0
            print(f"  资源{i}: 偏移={offset}, 大小={size}")
        if resource_count > 5:
            print(f"  ... (共{resource_count}个资源)")
        
        return offsets, resource_count

def parse_resource(filepath, offsets, resource_idx):
    """解析指定资源"""
    with open(filepath, 'rb') as f:
        # 读取资源数据
        start = offsets[resource_idx]
        end = offsets[resource_idx + 1] if resource_idx + 1 < len(offsets) else os.path.getsize(filepath)
        
        f.seek(start)
        resource_data = f.read(end - start)
        
        # 读取子项数量 (2字节)
        sub_count = struct.unpack('<h', resource_data[0:2])[0]
        print(f"\n资源{resource_idx} - 子项数量: {sub_count}")
        
        # 读取子项偏移表 (每个子项2字节)
        sub_offsets = []
        for i in range(sub_count):
            sub_off = struct.unpack('<h', resource_data[2 + i*2 : 4 + i*2])[0]
            sub_offsets.append(sub_off)
        
        print(f"子项偏移:")
        for i, sub_off in enumerate(sub_offsets[:5]):
            if i+1 < len(sub_offsets):
                size = sub_offsets[i+1] - sub_off
            else:
                size = len(resource_data) - sub_off
            print(f"  子项{i}: 偏移={sub_off}, 大小={size}")
        if sub_count > 5:
            print(f"  ... (共{sub_count}个子项)")
        
        return resource_data, sub_count, sub_offsets

def parse_sub_text(resource_data, sub_offsets, sub_idx):
    """解析子项文本内容"""
    if sub_idx < 0 or sub_idx >= len(sub_offsets):
        print(f"错误: 子项{sub_idx}不存在")
        return []
    
    # 获取子项数据起始位置
    data_start = sub_offsets[sub_idx]
    
    # 获取下一个子项偏移或资源末尾
    if sub_idx + 1 < len(sub_offsets):
        data_end = sub_offsets[sub_idx + 1]
    else:
        data_end = len(resource_data)
    
    # 提取子项数据
    sub_data = resource_data[data_start:data_end]
    
    # 解析int16数组
    words = []
    pos = 0
    while pos + 2 <= len(sub_data):
        word = struct.unpack('<h', sub_data[pos:pos+2])[0]
        words.append(word)
        pos += 2
        
        # 遇到TEXT_END停止
        if word == TEXT_END:
            break
    
    return words

def format_output(words):
    """格式化输出所有控制码和字符"""
    print("\n" + "="*80)
    print("资源1 子项1 完整内容分析")
    print("="*80)
    
    sequence_num = 0
    i = 0
    while i < len(words):
        word = words[i]
        sequence_num += 1
        
        if word in CONTROL_CODES:
            ctrl_name = CONTROL_CODES[word]
            print(f"[{sequence_num:03d}] 控制码: {word:#06x} ({word}) - {ctrl_name}")
            
            # 某些控制码后面有参数
            if word in [TEXT_PORTRAIT_F, TEXT_PORTRAIT_S, TEXT_CHAR_F, TEXT_CHAR_S]:
                if i + 1 < len(words):
                    param = words[i + 1]
                    print(f"      参数: {param}")
                    i += 1
                    sequence_num += 1
                    print(f"[{sequence_num:03d}] └─ 参数值: {param:#06x} ({param})")
            
            elif word == TEXT_SHOW_NUM:
                if i + 1 < len(words):
                    param = words[i + 1]
                    print(f"      参数: {param}")
                    i += 1
                    sequence_num += 1
                    print(f"[{sequence_num:03d}] └─ 参数值: {param:#06x} ({param})")
        else:
            # 普通字符 (字体索引)
            print(f"[{sequence_num:03d}] 字符: {word:#06x} ({word}) - 字体索引#{word}")
        
        i += 1
    
    print("\n" + "="*80)
    print(f"总计: {len(words)} 个int16值")
    print(f"其中控制码: {sum(1 for w in words if w in CONTROL_CODES)} 个")
    print(f"普通字符: {sum(1 for w in words if w not in CONTROL_CODES)} 个")
    print("="*80)

def main():
    fdtxt_path = r"d:\testworkspace\fd2_dat_freebuff\game\FDTXT.DAT"
    
    if not os.path.exists(fdtxt_path):
        print(f"错误: 找不到文件 {fdtxt_path}")
        return
    
    print("正在解析FDTXT.DAT文件...")
    offsets, resource_count = parse_fdtxt(fdtxt_path)
    
    print(f"\n正在解析资源1...")
    resource_data, sub_count, sub_offsets = parse_resource(fdtxt_path, offsets, 1)
    
    print(f"\n正在解析子项1...")
    words = parse_sub_text(resource_data, sub_offsets, 1)
    
    if words:
        format_output(words)
    else:
        print("子项1为空或不存在")

if __name__ == "__main__":
    main()
