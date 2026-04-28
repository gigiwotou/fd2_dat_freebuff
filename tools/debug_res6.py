#!/usr/bin/env python3
"""
调试FDOTHER.DAT资源6的嵌套DAT结构
验证是否真的有125个子资源
"""

import struct
from pathlib import Path

GAME_DIR = Path("game")

def main():
    data = (GAME_DIR / "FDOTHER.DAT").read_bytes()
    
    # 读取偏移表
    res_count = struct.unpack_from("<I", data, 6)[0]
    offsets = []
    for i in range(res_count):
        offsets.append(struct.unpack_from("<I", data, 10 + i*4)[0])
    
    # 获取资源6
    start = offsets[6]
    end = offsets[7] if 7 < len(offsets) else len(data)
    res6_data = data[start:end]
    
    print(f"资源6: 偏移={start}, 大小={len(res6_data)}")
    print(f"前16字节(hex): {res6_data[:16].hex()}")
    
    # 验证LLLLLL头
    if res6_data[:6] == b"LLLLLL":
        print("确认: LLLLLL魔数")
    else:
        print("错误: 不是LLLLLL格式")
        return
    
    # 读取资源数
    nested_count = struct.unpack_from("<I", res6_data, 6)[0]
    print(f"嵌套资源数: {nested_count}")
    
    # 直接打印所有偏移数据（原始字节）
    print(f"\n偏移表原始数据 (前50个偏移):")
    for i in range(min(50, nested_count)):
        off_pos = 10 + i * 4
        if off_pos + 4 <= len(res6_data):
            offset_bytes = res6_data[off_pos:off_pos+4]
            offset = struct.unpack_from("<I", res6_data, off_pos)[0]
            print(f"  [{i:3}] bytes={offset_bytes.hex()}, offset={offset}, valid={'YES' if offset < len(res6_data) else 'NO'}")
    
    # 如果嵌套_count > 实际可读取的偏移数，说明数据有问题
    max_possible = (len(res6_data) - 10) // 4
    print(f"\n最大可能偏移数: {max_possible}")
    print(f"声明的偏移数: {nested_count}")
    
    if nested_count > max_possible:
        print(f"警告: 声明的偏移数超过文件能容纳的数量!")
        # 尝试修复: 只读取实际可用的偏移
        actual_count = max_possible
        print(f"实际可用偏移数: {actual_count}")
    else:
        actual_count = nested_count
    
    # 重新读取所有有效偏移
    nested_offsets = []
    for i in range(actual_count):
        off_pos = 10 + i * 4
        if off_pos + 4 <= len(res6_data):
            offset = struct.unpack_from("<I", res6_data, off_pos)[0]
            if offset < len(res6_data):
                nested_offsets.append(offset)
    
    print(f"\n有效偏移数: {len(nested_offsets)}")
    
    # 打印前20个资源
    print(f"\n前20个子资源:")
    for i in range(min(20, len(nested_offsets))):
        s = nested_offsets[i]
        e = nested_offsets[i+1] if i+1 < len(nested_offsets) else len(res6_data)
        sz = e - s
        if sz < 1000000:  # 只打印合理大小的资源
            header = res6_data[s:s+4].hex() if s < len(res6_data) else ""
            print(f"  [{i:3}] 偏移={s:8}, 大小={sz:8}, 头={header}")
    
    # 打印最后5个
    if len(nested_offsets) > 20:
        print(f"\n最后5个子资源:")
        for i in range(max(20, len(nested_offsets)-5), len(nested_offsets)):
            s = nested_offsets[i]
            e = nested_offsets[i+1] if i+1 < len(nested_offsets) else len(res6_data)
            sz = e - s
            if sz < 1000000:
                print(f"  [{i:3}] 偏移={s:8}, 大小={sz:8}")

if __name__ == "__main__":
    main()
