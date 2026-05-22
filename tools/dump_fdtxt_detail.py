#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FDTXT.DAT 详细转储工具
解析资源集0，子文本0，打印所有int16值及控制码参数
"""

import struct
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 控制码描述
CONTROL_CODES = {
    -1: 'TEXT_END - 文本结束',
    -2: 'TEXT_NEWLINE - 换行',
    -3: 'TEXT_NEWLINE_MODE - 换行+模式开启',
    -4: 'TEXT_RECURSE_1 - 递归显示文本[dword_53AD9]',
    -5: 'TEXT_RECURSE_2 - 递归显示文本[dword_53ADD]',
    -6: 'TEXT_SHOW_NUMBER - 显示数字变量n999_1',
    -7: 'TEXT_CMD_7 - 未知控制码',
    -8: 'TEXT_CMD_8 - 未知控制码',
    -9: 'TEXT_CMD_9 - 未知控制码',
    -10: 'TEXT_CMD_10 - 未知控制码',
    -11: 'TEXT_CMD_11 - 未知控制码',
    -12: 'TEXT_CMD_12 - 未知控制码',
    -13: 'TEXT_CMD_13 - 未知控制码',
    -14: 'TEXT_CMD_14 - 未知控制码',
    -15: 'TEXT_CMD_15 - 未知控制码',
    -16: 'TEXT_CMD_16 - 未知控制码',
    -17: 'TEXT_DATO_LOAD_1832 - 加载DATO对话框(类型1832)，参数=资源索引',
    -18: 'TEXT_DATO_LOAD_36887 - 加载DATO对话框(类型36887)，参数=资源索引',
    -19: 'TEXT_CHAR_F - 从图标加载头像(类型1832)，参数=图标索引',
    -20: 'TEXT_CHAR_S - 从图标加载头像(类型36887)，参数=图标索引',
}

# 需要跟随参数的控制码
PARAM_CODES = {-17, -18, -19, -20}

def main():
    dat_path = 'game/FDTXT.DAT'
    
    with open(dat_path, 'rb') as f:
        data = f.read()
    
    file_size = len(data)
    print('=' * 80)
    print('FDTXT.DAT 详细转储 - 资源集0/子文本0')
    print('=' * 80)
    print('文件大小: %d 字节' % file_size)
    print()
    
    # 解析头部
    magic = data[:6]
    print('魔数: %s' % magic)
    
    count = struct.unpack_from('<I', data, 6)[0]
    print('资源集数量: %d' % count)
    print()
    
    # 读取偏移表
    offsets = []
    for i in range(count):
        off = struct.unpack_from('<I', data, 10 + i * 4)[0]
        offsets.append(off)
    
    # 检查资源集0
    if len(offsets) < 2:
        print('错误: 资源集数量不足')
        return
    
    res0_start = offsets[0]
    res0_end = offsets[1] if len(offsets) > 1 else file_size
    
    print('=== 资源集0 ===')
    print('偏移: 0x%08X - 0x%08X' % (res0_start, res0_end))
    print('大小: %d 字节' % (res0_end - res0_start))
    print()
    
    # 资源集0数据结构:
    # 前2字节: 子项数量(16-bit signed)
    # 接下来: 子项偏移表(每个是16-bit signed，相对资源集起始)
    # 然后: 实际子项数据
    
    res0_data = data[res0_start:res0_end]
    
    if len(res0_data) < 2:
        print('错误: 资源集0数据不足')
        return
    
    sub_count = struct.unpack_from('<h', res0_data, 0)[0]
    print('子项数量: %d' % sub_count)
    print()
    
    if sub_count < 1:
        print('错误: 资源集0没有子项')
        return
    
    # 读取子项偏移表
    sub_offsets = []
    for i in range(sub_count):
        off = struct.unpack_from('<h', res0_data, 2 + i * 2)[0]
        sub_offsets.append(off)
    
    # 获取子文本0的起始和结束
    sub0_start = sub_offsets[0]
    sub0_end = sub_offsets[1] if len(sub_offsets) > 1 else len(res0_data)
    
    print('=== 子文本0 ===')
    print('偏移: %d - %d (相对资源集0)' % (sub0_start, sub0_end))
    print('大小: %d 字节' % (sub0_end - sub0_start))
    print()
    
    # 读取子文本0数据
    sub0_data = res0_data[sub0_start:sub0_end]
    
    # 解析所有WORD值
    print('=' * 80)
    print('所有int16值转储')
    print('=' * 80)
    print()
    
    index = 0
    pos = 0
    while pos + 2 <= len(sub0_data):
        value = struct.unpack_from('<h', sub0_data, pos)[0]
        pos += 2
        
        hex_val = '0x%04X' % (value & 0xFFFF)
        
        if value == -1:
            print('[%04d] %6d (%s) - %s' % (index, value, hex_val, 'TEXT_END - 文本结束'))
            break
        elif value < 0:
            desc = CONTROL_CODES.get(value, '未知控制码')
            print('[%04d] %6d (%s) - %s' % (index, value, hex_val, desc))
            
            # 如果是需要参数的控制码，显示下一个word
            if value in PARAM_CODES:
                if pos + 2 <= len(sub0_data):
                    param = struct.unpack_from('<h', sub0_data, pos)[0]
                    param_hex = '0x%04X' % (param & 0xFFFF)
                    print('       next word = %d (%s)' % (param, param_hex))
                    pos += 2
                    index += 1
                else:
                    print('       next word = (数据不足)')
        else:
            print('[%04d] %6d (%s) - 普通字符索引' % (index, value, hex_val))
        
        index += 1
    
    print()
    print('=' * 80)
    print('转储完成 - 共 %d 个word' % index)
    print('=' * 80)

if __name__ == '__main__':
    main()
