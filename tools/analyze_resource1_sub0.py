#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FDTXT.DAT 资源1子项0 完整分析工具
输出所有控制码和字符的序列
"""

import struct
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

FDTXT_PATH = 'game/FDTXT.DAT'

# 控制码定义（用户提供）
CONTROL_CODES = {
    -1: 'TEXT_END - 文本结束',
    -2: 'TEXT_NEWLINE - 换行',
    -3: 'TEXT_NEWLINE2 - 换行2',
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
    -17: 'TEXT_PORTRAIT_F - 从图标加载头像(正面)',
    -18: 'TEXT_PORTRAIT_S - 从图标加载头像(侧面)',
    -19: 'TEXT_CHAR_F - 从图标加载角色头像(正面)',
    -20: 'TEXT_CHAR_S - 从图标加载角色头像(侧面)',
}

# 带参数的控制码（后面跟着2字节参数）
PARAM_CODES = {-17, -18, -19, -20}


def load_resource(fdtxt_data, res_index):
    """加载指定资源"""
    count = struct.unpack_from('<I', fdtxt_data, 6)[0]
    if res_index >= count:
        return None, None

    offsets = []
    for i in range(count):
        off = struct.unpack_from('<I', fdtxt_data, 10 + i * 4)[0]
        offsets.append(off)

    res_start = offsets[res_index]
    res_end = offsets[res_index + 1] if res_index + 1 < count else len(fdtxt_data)
    return fdtxt_data[res_start:res_end], res_start


def main():
    with open(FDTXT_PATH, 'rb') as f:
        fdtxt = f.read()

    print('=' * 80)
    print('FDTXT.DAT 资源1/子项0 完整分析')
    print('=' * 80)
    print(f'文件大小: {len(fdtxt)} 字节')
    print()

    # 加载资源1
    res_data, res_offset = load_resource(fdtxt, 1)
    if res_data is None:
        print('错误: 无法加载资源1')
        return

    print(f'资源1偏移: 0x{res_offset:08X}')
    print(f'资源1大小: {len(res_data)} 字节')
    print()

    # 解析子项
    sub_count = struct.unpack_from('<h', res_data, 0)[0]
    print(f'子项数量: {sub_count}')
    print()

    if sub_count < 1:
        print('错误: 没有子项')
        return

    # 读取子项偏移表
    sub_offsets = []
    for i in range(sub_count):
        off = struct.unpack_from('<h', res_data, 2 + i * 2)[0]
        sub_offsets.append(off)

    sub0_start = sub_offsets[0]
    sub0_end = sub_offsets[1] if len(sub_offsets) > 1 else len(res_data)

    print(f'=== 子项0 ===')
    print(f'偏移: {sub0_start} - {sub0_end} (相对资源1)')
    print(f'大小: {sub0_end - sub0_start} 字节')
    print()

    # 读取子项0数据
    sub0_data = res_data[sub0_start:sub0_end]

    # 解析所有值
    print('=' * 80)
    print('完整控制码和字符序列')
    print('=' * 80)
    print()

    all_values = []
    pos = 0
    index = 0

    # 统计
    char_count = 0
    control_count = 0
    control_details = {}

    while pos + 2 <= len(sub0_data):
        value = struct.unpack_from('<h', sub0_data, pos)[0]
        pos += 2

        hex_val = f'0x{value & 0xFFFF:04X}'
        all_values.append(value)

        if value == -1:
            print(f'[{index:04d}] {value:6d} ({hex_val}) - TEXT_END (文本结束)')
            control_count += 1
            control_details[-1] = control_details.get(-1, 0) + 1
            index += 1
            break
        elif value < 0:
            desc = CONTROL_CODES.get(value, '未知控制码')
            print(f'[{index:04d}] {value:6d} ({hex_val}) - {desc}')
            control_count += 1
            control_details[value] = control_details.get(value, 0) + 1

            # 带参数的控制码，显示参数
            if value in PARAM_CODES:
                if pos + 2 <= len(sub0_data):
                    param = struct.unpack_from('<h', sub0_data, pos)[0]
                    param_hex = f'0x{param & 0xFFFF:04X}'
                    print(f'       └─ 参数: {param} ({param_hex})')
                    all_values.append(param)
                    pos += 2
                    index += 1
                else:
                    print(f'       └─ 参数: (数据不足)')
        else:
            print(f'[{index:04d}] {value:6d} ({hex_val}) - 普通字符索引')
            char_count += 1

        index += 1

    print()
    print('=' * 80)
    print('统计信息')
    print('=' * 80)
    print()
    print(f'总值数量: {index}')
    print(f'普通字符数量: {char_count}')
    print(f'控制码数量: {control_count}')
    print()
    print('控制码统计:')
    for code in sorted(control_details.keys()):
        desc = CONTROL_CODES.get(code, '未知控制码')
        print(f'  {code:6d} ({code & 0xFFFF:04X}): {control_details[code]}次 - {desc}')
    print()
    print('=' * 80)
    print('完整序列（逗号分隔，包含参数）')
    print('=' * 80)
    print(', '.join(str(v) for v in all_values))
    print()
    print('=' * 80)
    print('分析完成')
    print('=' * 80)


if __name__ == '__main__':
    main()
