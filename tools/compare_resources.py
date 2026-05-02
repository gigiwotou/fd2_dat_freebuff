#!/usr/bin/env python3
"""
对比多个resource的格式，找出res78的特殊之处
"""
import struct
import os
import wave

def load_resource(res_id):
    dat_path = os.path.join('game', 'FDOTHER.DAT')
    with open(dat_path, 'rb') as f:
        f.seek(0x10)
        table_offset = struct.unpack_from('<I', f.read(4), 0)[0]
        
        f.seek(table_offset + res_id * 8)
        res_offset = struct.unpack_from('<I', f.read(4), 0)[0]
        res_size = struct.unpack_from('<I', f.read(4), 0)[0]
        
        f.seek(res_offset)
        raw = f.read(res_size)
    
    return raw, res_size

def analyze_resource(res_id, raw, res_size):
    print(f"\n{'='*60}")
    print(f"Resource #{res_id} ({res_size} bytes)")
    print(f"{'='*60}")
    
    # 打印前128字节
    print(f"前128字节:")
    for i in range(0, min(128, len(raw)), 16):
        hex_str = ' '.join(f'{b:02x}' for b in raw[i:i+16])
        ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in raw[i:i+16])
        print(f"  {i:04x}: {hex_str:<48s} {ascii_str}")
    
    # 解析头部
    if res_size >= 12:
        v0 = struct.unpack_from('<I', raw, 0)[0]
        v2 = struct.unpack_from('<I', raw, 2)[0]
        v4 = struct.unpack_from('<I', raw, 4)[0]
        v6 = struct.unpack_from('<I', raw, 6)[0]
        v8 = struct.unpack_from('<I', raw, 8)[0]
        v10 = struct.unpack_from('<I', raw, 10)[0]
        
        print(f"\n头部解析:")
        print(f"  *(0)  = 0x{v0:x} ({v0})")
        print(f"  *(2)  = 0x{v2:x} ({v2})")
        print(f"  *(4)  = 0x{v4:x} ({v4})")
        print(f"  *(6)  = 0x{v6:x} ({v6})")
        print(f"  *(8)  = 0x{v8:x} ({v8})")
        print(f"  *(10) = 0x{v10:x} ({v10})")
        
        # 可能的样本区域
        if v6 > 0 and v6 < res_size and v10 > v6 and v10 <= res_size:
            sample_start = v6
            sample_end = v10
            sample_size = v10 - v6
            print(f"\n  可能的样本区域: [{v6} - {v10}] ({sample_size} bytes)")
    
    # 字节统计
    if res_size > 0:
        print(f"\n字节统计:")
        print(f"  范围: 0x{min(raw):02x} - 0x{max(raw):02x}")
        print(f"  平均值: {sum(raw)/len(raw):.1f}")
        
        # 高频字节
        from collections import Counter
        counter = Counter(raw)
        print(f"  最常见的5个字节: {counter.most_common(5)}")

def decode_ima_adpcm(data, initial_predictor=0, initial_index=0):
    """IMA ADPCM解码"""
    IMA_STEP_TABLE = [
        7, 8, 9, 10, 11, 12, 13, 14, 16, 17, 19, 21, 23, 25, 28, 31, 34,
        37, 41, 45, 50, 55, 60, 66, 73, 80, 88, 97, 107, 118, 130, 143,
        157, 173, 190, 209, 230, 253, 279, 307, 337, 371, 408, 449, 494,
        544, 598, 658, 724, 796, 876, 963, 1060, 1166, 1282, 1411, 1552,
        1707, 1878, 2066, 2272, 2499, 2749, 3024, 3327, 3660, 4026, 4428,
        4871, 5358, 5894, 6484, 7132, 7845, 8630, 9493, 10442, 11487,
        12635, 13899, 15289, 16818, 18500, 20350, 22385, 24623, 27086,
        29794, 32767
    ]
    IMA_INDEX_TABLE = [-1, -1, -1, -1, 2, 4, 6, 8, -1, -1, -1, -1, 2, 4, 6, 8]
    
    output = []
    predictor = initial_predictor
    index = initial_index
    
    for byte in data:
        for nibble in [(byte >> 4) & 0x0F, byte & 0x0F]:
            step = IMA_STEP_TABLE[index]
            delta = 0
            if nibble & 0x04: delta += step
            if nibble & 0x02: delta += step >> 1
            if nibble & 0x01: delta += step >> 2
            delta += step >> 3
            
            if nibble & 0x08:
                predictor -= delta
            else:
                predictor += delta
            
            predictor = max(-32768, min(32767, predictor))
            output.append(struct.pack('<h', predictor))
            
            index += IMA_INDEX_TABLE[nibble]
            index = max(0, min(88, index))
    
    return b''.join(output)

def main():
    # 分析已知的音效资源
    # res9 之前确认是可以工作的
    res_ids = [9, 78, 10, 20, 50]
    
    for res_id in res_ids:
        try:
            raw, res_size = load_resource(res_id)
            analyze_resource(res_id, raw, res_size)
        except Exception as e:
            print(f"\nResource #{res_id} 加载失败: {e}")
    
    # 对比res9和res78
    print(f"\n{'='*60}")
    print("res9 vs res78 详细对比")
    print(f"{'='*60}")
    
    raw9, size9 = load_resource(9)
    raw78, size78 = load_resource(78)
    
    print(f"\nres9 大小: {size9}")
    print(f"res78 大小: {size78}")
    
    print(f"\nres9 前32字节:")
    for i in range(0, 32, 16):
        print(f"  {i:04x}: {' '.join(f'{b:02x}' for b in raw9[i:i+16])}")
    
    print(f"\nres78 前32字节:")
    for i in range(0, 32, 16):
        print(f"  {i:04x}: {' '.join(f'{b:02x}' for b in raw78[i:i+16])}")
    
    # 尝试用res9的成功参数解码res78
    print(f"\n{'='*60}")
    print("使用res9的参数解码res78")
    print(f"{'='*60}")
    
    out_dir = 'output/sfx_wav/res078_comparison'
    os.makedirs(out_dir, exist_ok=True)
    
    # 假设res9使用的是16-bit BE PCM 8000Hz skip 4
    # 尝试res78用相同参数
    if len(raw78) > 4:
        sample_data = raw78[4:]
        count = len(sample_data) // 2
        samples = struct.unpack_from(f'>{count}h', sample_data, 0)
        pcm = b''.join(struct.pack('<h', s) for s in samples)
        
        wav_path = f"{out_dir}/res78_16bit_be_8000_skip4.wav"
        with wave.open(wav_path, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(8000)
            wf.writeframes(pcm)
        print(f"保存: {wav_path}")
    
    # IMA ADPCM解码（从第4字节开始）
    if len(raw78) > 4:
        adpcm_data = raw78[4:]
        pcm = decode_ima_adpcm(adpcm_data, 0, 0)
        wav_path = f"{out_dir}/res78_adpcm_from4.wav"
        with wave.open(wav_path, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(22050)
            wf.writeframes(pcm)
        print(f"保存: {wav_path}")
    
    # 直接用res9的样本数据做对比
    if len(raw9) > 4:
        sample_data = raw9[4:]
        count = len(sample_data) // 2
        samples = struct.unpack_from(f'>{count}h', sample_data, 0)
        pcm = b''.join(struct.pack('<h', s) for s in samples[:1000])  # 只取前1000个样本
        
        print(f"\nres9样本前1000个统计:")
        samples_list = list(struct.unpack_from(f'>{len(sample_data)//2}h', sample_data, 0))
        print(f"  范围: {min(samples_list[:1000])} - {max(samples_list[:1000])}")
        print(f"  平均: {sum(samples_list[:1000])/1000:.1f}")
    
    print(f"\n完成! 检查 {out_dir}/ 目录")

if __name__ == '__main__':
    main()
