#!/usr/bin/env python3
"""
重新解析res78头部，找到正确的样本偏移和大小
"""
import struct
import os

def main():
    base_dir = os.path.dirname(os.path.dirname(__file__))
    fdother_path = os.path.join(base_dir, 'game', 'FDOTHER.DAT')
    
    with open(fdother_path, 'rb') as f:
        magic = f.read(6)
        count = struct.unpack('<I', f.read(4))[0]
        
        f.seek(10)
        offsets = []
        for i in range(count):
            offsets.append(struct.unpack('<I', f.read(4))[0])
        
        idx = 78
        res_start = offsets[idx]
        res_end = offsets[idx + 1] if idx + 1 < count else os.path.getsize(fdother_path)
        f.seek(res_start)
        res78 = f.read(res_end - res_start)
    
    print(f"res78总大小: {len(res78)} 字节")
    print(f"头部16字节: {res78[:16].hex(' ')}")
    
    # int32解析
    h = struct.unpack_from('<4I', res78, 0)
    print(f"\nint32解析:")
    print(f"  h[0] = {h[0]} (0x{h[0]:x})")
    print(f"  h[1] = {h[1]} (0x{h[1]:x})")
    print(f"  h[2] = {h[2]} (0x{h[2]:x}) <- 这应该是样本2的偏移=16")
    print(f"  h[3] = {h[3]} (0x{h[3]:x}) <- 这应该是样本2的大小=6359")
    
    # 验证: 16 + 6359 = 6375
    # 剩余: 6801 - 6375 = 426 字节
    # 这些剩余字节是什么?
    
    sample2_start = h[2]  # 16
    sample2_size = h[3]   # 6359
    sample2_end = sample2_start + sample2_size  # 6375
    
    print(f"\n样本2:")
    print(f"  起始: {sample2_start}")
    print(f"  大小: {sample2_size}")
    print(f"  结束: {sample2_end}")
    print(f"  剩余字节: {len(res78) - sample2_end}")
    
    # 看看剩余字节是什么
    if sample2_end < len(res78):
        remainder = res78[sample2_end:]
        print(f"\n剩余{len(remainder)}字节:")
        print(f"  前32字节: {remainder[:32].hex(' ')}")
        non_zero = sum(1 for b in remainder if b != 0)
        print(f"  非零字节: {non_zero}")
    
    # 提取真正的样本2数据
    sample2_data = res78[sample2_start:sample2_end]
    print(f"\n样本2数据:")
    print(f"  大小: {len(sample2_data)}")
    print(f"  前64字节: {sample2_data[:64].hex(' ')}")
    print(f"  后32字节: {sample2_data[-32:].hex(' ')}")
    
    # 保存到文件
    output_dir = os.path.join(base_dir, 'output', 'sfx_wav', 'lightning_correct')
    os.makedirs(output_dir, exist_ok=True)
    
    sample_path = os.path.join(output_dir, 'lightning_6359.bin')
    with open(sample_path, 'wb') as f:
        f.write(sample2_data)
    print(f"\n样本数据保存到: {sample_path}")
    
    # 统计字节分布
    hist = [0] * 256
    for b in sample2_data:
        hist[b] += 1
    
    print(f"\n字节值分布 (按16分组):")
    for i in range(0, 256, 16):
        total = sum(hist[i:i+16])
        if total > 0:
            bar = '#' * (total // 50)
            print(f"  {i:3d}-{i+15:3d}: {total:5d} {bar}")

if __name__ == '__main__':
    main()
