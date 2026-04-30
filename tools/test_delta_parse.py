#!/usr/bin/env python3
"""
测试正确的delta解析 - 0xFF等>=0x80字节应继续作为delta的一部分
"""

import struct
from pathlib import Path

def test_delta_parse(filepath):
    with open(filepath, 'rb') as f:
        data = f.read()
    
    evnt_pos = data.find(b'EVNT')
    chunk_size = struct.unpack('>I', data[evnt_pos+4:evnt_pos+8])[0]
    pos = evnt_pos + 8
    end = pos + chunk_size
    
    print(f"\n{filepath.name}")
    print(f"First 60 raw bytes from EVNT:")
    for i in range(0, min(60, chunk_size), 16):
        chunk = data[pos+i:pos+i+16]
        hex_str = ' '.join(f'{b:02X}' for b in chunk)
        ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in chunk)
        print(f"  {pos+i:04X}: {hex_str:<48} {ascii_str}")
    
    # 解析第一个事件
    print(f"\nParsing first event:")
    delta_bytes = []
    delta = 0
    start_pos = pos
    
    # Delta时间可以有多个字节，直到遇到最高位为0的字节
    max_bytes = 10
    count = 0
    while pos < end and count < max_bytes:
        byte = data[pos]
        delta_bytes.append(byte)
        pos += 1
        count += 1
        delta = (delta << 7) | (byte & 0x7F)
        print(f"  delta byte: 0x{byte:02X} (bit7={byte >> 7})")
        if not (byte & 0x80):
            break
    
    print(f"Delta value: {delta}")
    print(f"Current position: {pos:#x}")
    print(f"Next byte: 0x{data[pos]:02X}")
    
    # 状态字节
    status = data[pos]
    pos += 1
    print(f"Status: 0x{status:02X}")
    
    if status == 0xFF:
        meta_type = data[pos]
        pos += 1
        print(f"Meta type: 0x{meta_type:02X}")
        
        # 解析长度
        length = 0
        while pos < end:
            byte = data[pos]
            pos += 1
            length = (length << 7) | byte
            if not (byte & 0x80):
                break
        print(f"Length: {length}")
        
        # 读取数据
        data_bytes = data[pos:pos+length]
        print(f"Data: {' '.join(f'{b:02X}' for b in data_bytes)}")

def main():
    track_dir = Path("output/fdmus_tracks")
    for idx in [0, 11]:
        track_file = track_dir / f"track_{idx:03d}.bin"
        if track_file.exists():
            test_delta_parse(track_file)

if __name__ == "__main__":
    main()
