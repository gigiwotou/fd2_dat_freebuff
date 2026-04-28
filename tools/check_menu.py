#!/usr/bin/env python3
"""
检查FDOTHER资源7, 8, 102和TITLE.DAT内容
"""

import struct
from pathlib import Path

DAT_MAGIC = b"LLLLLL"
GAME_DIR = Path("game")

def check_fdother_menu():
    fdother_path = GAME_DIR / "FDOTHER.DAT"
    data = fdother_path.read_bytes()
    
    print("=== FDOTHER.DAT 关键资源 ===")
    
    # 获取所有偏移
    res_count = struct.unpack_from("<I", data, 6)[0]
    offsets = []
    for i in range(res_count):
        offsets.append(struct.unpack_from("<I", data, 10 + i*4)[0])
    
    # 资源7
    s7, e7 = offsets[7], offsets[8] if 8 < len(offsets) else len(data)
    res7 = data[s7:e7]
    print(f"\n资源7: {len(res7)} 字节")
    print(f"  头4字节: {res7[:4].hex()} ({res7[:4]})")
    print(f"  是DAT: {res7[:6] == DAT_MAGIC}")
    
    # 资源8
    s8, e8 = offsets[8], offsets[9] if 9 < len(offsets) else len(data)
    res8 = data[s8:e8]
    print(f"\n资源8: {len(res8)} 字节")
    print(f"  头4字节: {res8[:4].hex()} ({res8[:4]})")
    if res8[:6] == DAT_MAGIC:
        inner_count = struct.unpack_from("<I", res8, 6)[0]
        print(f"  是嵌套DAT! 子资源数: {inner_count}")
        inner_offsets = []
        for i in range(inner_count):
            inner_offsets.append(struct.unpack_from("<I", res8, 10 + i*4)[0])
        for i in range(inner_count):
            s = inner_offsets[i]
            e = inner_offsets[i+1] if i+1 < len(inner_offsets) else len(res8)
            print(f"    [{i}] 偏移={s}, 大小={e-s}")
    
    # 资源101
    s101, e101 = offsets[101], offsets[102] if 102 < len(offsets) else len(data)
    res101 = data[s101:e101]
    print(f"\n资源101: {len(res101)} 字节")
    print(f"  头4字节: {res101[:4].hex()}")
    if res101[:6] == DAT_MAGIC:
        inner_count = struct.unpack_from("<I", res101, 6)[0]
        print(f"  是嵌套DAT! 子资源数: {inner_count}")
        inner_offsets = []
        for i in range(inner_count):
            inner_offsets.append(struct.unpack_from("<I", res101, 10 + i*4)[0])
        for i in range(min(10, inner_count)):
            s = inner_offsets[i]
            e = inner_offsets[i+1] if i+1 < len(inner_offsets) else len(res101)
            print(f"    [{i}] 偏移={s}, 大小={e-s}")
    
    # 资源102
    s102, e102 = offsets[102], offsets[103] if 103 < len(offsets) else len(data)
    res102 = data[s102:e102]
    print(f"\n资源102: {len(res102)} 字节")
    print(f"  头4字节: {res102[:4].hex()}")
    if res102[:6] == DAT_MAGIC:
        inner_count = struct.unpack_from("<I", res102, 6)[0]
        print(f"  是嵌套DAT! 子资源数: {inner_count}")
        inner_offsets = []
        for i in range(inner_count):
            inner_offsets.append(struct.unpack_from("<I", res102, 10 + i*4)[0])
        for i in range(min(10, inner_count)):
            s = inner_offsets[i]
            e = inner_offsets[i+1] if i+1 < len(inner_offsets) else len(res102)
            print(f"    [{i}] 偏移={s}, 大小={e-s}")
    
    # 列出资源0-15的大小
    print(f"\n资源0-15:")
    for i in range(16):
        s = offsets[i]
        e = offsets[i+1] if i+1 < len(offsets) else len(data)
        sz = e - s
        print(f"  [{i:2}] {sz:8} 字节")

def check_title_dat():
    title_path = GAME_DIR / "TITLE.DAT"
    if not title_path.exists():
        print(f"\nTITLE.DAT 不存在")
        return
    
    data = title_path.read_bytes()
    if data[:6] != DAT_MAGIC:
        print(f"\nTITLE.DAT: 无效")
        return
    
    res_count = struct.unpack_from("<I", data, 6)[0]
    print(f"\n=== TITLE.DAT ===")
    print(f"  资源数: {res_count}")
    
    offsets = []
    for i in range(res_count):
        offsets.append(struct.unpack_from("<I", data, 10 + i*4)[0])
    
    for i in range(res_count):
        s = offsets[i]
        e = offsets[i+1] if i+1 < len(offsets) else len(data)
        sz = e - s
        print(f"  [{i}] {sz:8} 字节, 头: {data[s:s+4].hex()}")

def main():
    check_fdother_menu()
    print()
    check_title_dat()

if __name__ == "__main__":
    main()
