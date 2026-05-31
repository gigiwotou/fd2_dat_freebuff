#!/usr/bin/env python3
"""查找调用sub_4EBFF(0x4EBFF)的汇编代码位置"""
import struct

def main():
    # 读取FD2.EXE
    filepath = 'FD2.EXE'
    try:
        with open(filepath, 'rb') as f:
            exe_data = f.read()
    except FileNotFoundError:
        print(f"ERROR: {filepath} not found")
        return
    
    # 在EXE中搜索对0x4EBFF的call指令
    # call指令格式: E8 xx xx xx xx (相对偏移)
    # 4EBFF在EXE中的偏移需要计算
    
    print(f"EXE size: {len(exe_data)} bytes")
    
    # 搜索 E8 指令后面跟随的偏移
    # 由于是16位代码，需要特殊处理
    # 搜索 FF E8 (push 0x4EBFF? 不对)
    
    # 搜索 call near rel16/rel32
    # E8 xx xx xx xx 或 E8 xx xx
    target_addr = 0x4EBFF
    
    # 查找所有call指令
    calls_found = []
    pos = 0
    while pos < len(exe_data) - 5:
        if exe_data[pos] == 0xE8:  # call指令
            # 尝试解析为32位相对偏移
            if pos + 4 < len(exe_data):
                rel = struct.unpack_from('<i', exe_data, pos + 1)[0]
                call_target = pos + 5 + rel
                if call_target == target_addr:
                    calls_found.append(pos)
            # 尝试解析为16位相对偏移（如果代码段在低位）
            elif pos + 2 < len(exe_data):
                rel = struct.unpack_from('<h', exe_data, pos + 1)[0]
                call_target = pos + 3 + rel
                if call_target == target_addr:
                    calls_found.append(pos)
        pos += 1
    
    print(f"\n找到 {len(calls_found)} 处调用 0x{target_addr:X} 的位置:")
    for call_pos in calls_found[:10]:
        # 显示调用位置前后的汇编
        print(f"\n调用位置: 0x{call_pos:X}")
        print(f"  前20字节: {' '.join(f'{b:02X}' for b in exe_data[max(0,call_pos-30):call_pos+5])}")
        
        # 解析调用前的参数准备
        context_start = max(0, call_pos - 40)
        context = exe_data[context_start:call_pos]
        print(f"  上下文: {' '.join(f'{b:02X}' for b in context)}")

if __name__ == '__main__':
    main()
