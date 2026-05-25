#!/usr/bin/env python3
"""
重新分析 _FDOTHER.DAT__13 加载的资源数据结构

从sub_2EB9F:
  eax = a5 + 4*a6
  edx = a5 + *(DWORD*)(eax+8)
  width = *(WORD*)(edx)
  height = *(WORD*)(edx+2)
  rle_data = edx + 9

这意味着资源数据格式:
  [0-?]: 元数据表 (每个条目至少12字节)
  [?+]: tile数据 (有宽高头)

或者资源数据就是嵌套DAT，但sub_2EB9F使用不同的访问方式
"""
import struct

dat_path = r'D:\workspace\fd2_dat_freebuff\bin\FDOTHER.DAT'

with open(dat_path, 'rb') as f:
    data = f.read()

if data[:6] != b'LLLLLL':
    print("不是有效的 FDOTHER.DAT 文件")
else:
    count = struct.unpack_from('<I', data, 6)[0]
    offsets = []
    for i in range(count):
        offset = struct.unpack_from('<I', data, 10 + i * 4)[0]
        offsets.append(offset)
    
    # v36 = "?355[\\]^"
    # 场景0: 63
    scene0_idx = 63
    res_start = offsets[scene0_idx]
    res_end = offsets[scene0_idx+1] if scene0_idx+1 < len(offsets) else len(data)
    res_data = data[res_start:res_end]
    
    print(f"索引63资源:")
    print(f"  大小: {len(res_data)} 字节")
    print(f"  前6字节: {res_data[:6].hex()} = {res_data[:6]}")
    
    if res_data[:6] == b'LLLLLL':
        print(f"  是嵌套DAT格式")
        nested_count = struct.unpack_from('<I', res_data, 6)[0]
        print(f"  嵌套资源数: {nested_count}")
        
        # 查看偏移表
        print(f"\n  偏移表 (前10个):")
        for i in range(min(10, nested_count)):
            offset = struct.unpack_from('<I', res_data, 10 + i*4)[0]
            print(f"    [{i}] 0x{offset:06X} ({offset})")
            if offset >= len(res_data):
                print(f"      -> 偏移超出资源大小")
                break
        
        # 检查第一个tile的完整数据
        if nested_count > 0:
            tile0_offset = struct.unpack_from('<I', res_data, 10)[0]
            if tile0_offset < len(res_data):
                tile0_data = res_data[tile0_offset:tile0_offset+64]
                print(f"\n  Tile 0 前64字节:")
                for i in range(0, 64, 16):
                    hex_str = ' '.join(f'{b:02X}' for b in tile0_data[i:i+16])
                    print(f"    {i:03d}: {hex_str}")
                
                # 尝试从不同角度解析
                print(f"\n  尝试解析tile头:")
                # 假设 [0-1]width, [2-3]height
                w = struct.unpack_from('<H', tile0_data, 0)[0]
                h = struct.unpack_from('<H', tile0_data, 2)[0]
                print(f"    [0-3]: w={w}, h={h}")
                
                # 假设 [4-7]是其他元数据
                if len(tile0_data) >= 8:
                    v = struct.unpack_from('<I', tile0_data, 4)[0]
                    print(f"    [4-7]: 0x{v:08X}")
                
                # 从偏移9开始是RLE数据
                print(f"    [9]: RLE数据起始")
                
                # 但之前我们看到字节值都是0x7C等，这是RLE像素数据
                # 所以可能tile数据没有宽高头，宽高从其他地方来
                
    else:
        print(f"  不是嵌套DAT格式")
        # 查看完整前256字节
        print(f"\n  前256字节:")
        for i in range(0, 256, 16):
            hex_str = ' '.join(f'{b:02X}' for b in res_data[i:i+16])
            print(f"    {i:03d}: {hex_str}")
        
        # 尝试不同的解析方式
        print(f"\n  尝试解析:")
        # 可能是 [num_tiles:2][? :2][offset_table...]
        num_tiles = struct.unpack_from('<H', res_data, 0)[0]
        print(f"    [0-1] WORD: {num_tiles}")
        
        # 或者 [width:2][height:2][offset_table...]
        w = struct.unpack_from('<H', res_data, 0)[0]
        h = struct.unpack_from('<H', res_data, 2)[0]
        print(f"    [0-1] width?: {w}")
        print(f"    [2-3] height?: {h}")
