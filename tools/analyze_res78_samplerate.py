#!/usr/bin/env python3
"""
深度解析res78头部结构，查找采样率信息
根据IDA分析，采样率可能存储在样本数据头部
"""
import struct
import os
import sys

def main():
    base_dir = os.path.dirname(os.path.dirname(__file__))
    fdother_path = os.path.join(base_dir, 'game', 'FDOTHER.DAT')
    
    if not os.path.exists(fdother_path):
        print(f"错误: 找不到 FDOTHER.DAT")
        sys.exit(1)
    
    with open(fdother_path, 'rb') as f:
        magic = f.read(6)
        count = struct.unpack('<I', f.read(4))[0]
        
        f.seek(10)
        offsets = []
        for i in range(count):
            offsets.append(struct.unpack('<I', f.read(4))[0]))
    
    idx = 78
    start = offsets[idx]
    end = offsets[idx + 1] if idx + 1 < count else os.path.getsize(fdother_path)
    size = end - start
    
    with open(fdother_path, 'rb') as f:
        f.seek(start)
        res78 = f.read(size)
    
    print(f"res78总大小: {size} bytes (0x{size:x})")
    print(f"\n完整头部分析 (前128字节):")
    print("=" * 80)
    for i in range(0, min(128, len(res78)), 16):
        hex_str = ' '.join(f'{b:02x}' for b in res78[i:i+16])
        ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in res78[i:i+16])
        print(f"  {i:04x}: {hex_str:<48s} {ascii_str}")
    
    # 尝试不同偏移处读取采样率
    print(f"\n可能的采样率字段 (DWORD):")
    print("=" * 80)
    for offset in range(0, 64, 4):
        val = struct.unpack_from('<I', res78, offset)[0]
        # 检查是否是常见采样率
        if 1000 <= val <= 50000:
            print(f"  偏移+{offset:02x}: {val} Hz - **可能的采样率!**")
    
    # 检查是否有类似WAV的fmt头
    print(f"\n检查常见音频文件头标记:")
    print("=" * 80)
    # RIFF头
    if res78[:4] == b'RIFF':
        print("  发现RIFF标记!")
    if res78[:4] == b'FORM':
        print("  发现FORM标记 (IFF)")
    
    # 检查是否有类似"fmt "的标记
    for i in range(0, 64):
        chunk = res78[i:i+4]
        if chunk == b'fmt ' or chunk == b'data' or chunk == b'smpl':
            print(f"  偏移+{i:02x}: 发现'{chunk.decode('ascii', errors='replace')}'标记")
    
    # 分析头部结构
    print(f"\n头部字段详细分析:")
    print("=" * 80)
    print(f"  +0x00 (DWORD): {struct.unpack_from('<I', res78, 0)[0]}")
    print(f"  +0x04 (DWORD): {struct.unpack_from('<I', res78, 4)[0]}")
    print(f"  +0x08 (DWORD): {struct.unpack_from('<I', res78, 8)[0]}")
    print(f"  +0x0C (DWORD): {struct.unpack_from('<I', res78, 12)[0]} (之前认为是样本大小: 6359)")
    print(f"  +0x10 (DWORD): {struct.unpack_from('<I', res78, 16)[0]}")
    print(f"  +0x14 (DWORD): {struct.unpack_from('<I', res78, 20)[0]}")
    print(f"  +0x18 (DWORD): {struct.unpack_from('<I', res78, 24)[0]}")
    print(f"  +0x1C (DWORD): {struct.unpack_from('<I', res78, 28)[0]}")
    print(f"  +0x20 (DWORD): {struct.unpack_from('<I', res78, 32)[0]}")
    
    # 如果0x0C是样本大小6359，那么样本数据应该从某个固定偏移开始
    sample_size = struct.unpack_from('<I', res78, 12)[0]
    print(f"\n样本数据分析 (假设大小={sample_size}):")
    print("=" * 80)
    
    # 尝试不同的样本起始位置
    for sample_start in [0x20, 0x24, 0x28, 0x30, 0x40]:
        if sample_start + sample_size <= len(res78):
            sample_data = res78[sample_start:sample_start + sample_size]
            print(f"\n假设样本从0x{sample_start:x}开始:")
            print(f"  前16字节: {sample_data[:16].hex()}")
            
            # 计算时长
            for rate in [5512, 8000, 11025, 16000, 22050]:
                # IMA ADPCM 4-bit: 每字节2个采样
                duration_adpcm = (sample_size * 2) / rate
                print(f"  IMA ADPCM @ {rate}Hz: {duration_adpcm:.3f}秒")
                
                # 16-bit PCM: 每2字节1个采样
                duration_pcm = (sample_size / 2) / rate
                print(f"  16-bit PCM @ {rate}Hz: {duration_pcm:.3f}秒")

if __name__ == '__main__':
    main()