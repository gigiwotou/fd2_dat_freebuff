#!/usr/bin/env python3
"""
为res78闪电音效尝试IMA ADPCM解码。

从IDA分析可知：
1. sub_25A96直接调用AIL_set_sample_address，没有调用AIL_set_sample_type
2. AIL库默认的sample type是8-bit unsigned PCM
3. 但数据可能是IMA ADPCM压缩的

尝试：
1. 将res78样本0(6800字节)当作IMA ADPCM 4-bit解码
2. 6800字节 * 2 = 13600个采样点
3. 如果采样率是11025Hz，约1.2秒 - 合理的音效长度
"""

import struct
import wave
import io
from pathlib import Path


def ima_adpcm_decode_8bit(adpcm_data, initial_predictor=0, initial_index=0):
    """Decode IMA ADPCM 4-bit data to 8-bit unsigned PCM."""
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
    
    for byte in adpcm_data:
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
            
            predictor = max(0, min(255, predictor))
            output.append(predictor)
            
            index += IMA_INDEX_TABLE[nibble]
            index = max(0, min(88, index))
    
    return bytes(output)


def ima_adpcm_decode_16bit(adpcm_data, initial_predictor=0, initial_index=0):
    """Decode IMA ADPCM 4-bit data to 16-bit signed PCM."""
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
    predictor = initial_predictor  # 16-bit signed
    index = initial_index
    
    for byte in adpcm_data:
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


def pcm_to_wav(pcm_data, sample_rate=11025, channels=1, bits_per_sample=8):
    """Convert PCM data to WAV format."""
    wav_buffer = io.BytesIO()
    with wave.open(wav_buffer, 'wb') as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(bits_per_sample // 8)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm_data)
    return wav_buffer.getvalue()


def main():
    with open("game/FDOTHER.DAT", "rb") as f:
        data = f.read()
    
    count = struct.unpack_from('<I', data, 6)[0]
    offsets = []
    for i in range(count):
        off = struct.unpack_from('<I', data, 10 + i * 4)[0]
        offsets.append(off)
    
    res_idx = 78
    res_start = offsets[res_idx]
    res_end = offsets[res_idx + 1] if res_idx + 1 < len(offsets) else len(data)
    raw = data[res_start:res_end]
    
    output_dir = Path("output/sfx_wav/res078_lightning_adpcm")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Parse internal structure
    count1 = struct.unpack_from('<H', raw, 0)[0]
    count2 = struct.unpack_from('<H', raw, 2)[0]
    
    internal_offsets = []
    for i in range(count2):
        pos = 4 + i * 4
        if pos + 4 <= len(raw):
            val = struct.unpack_from('<I', raw, pos)[0]
            internal_offsets.append(val)
    internal_offsets.append(len(raw))
    
    print(f"Res78: {len(raw)} bytes")
    print(f"Internal offsets: {[hex(o) for o in internal_offsets]}")
    
    for sample_idx in range(len(internal_offsets) - 1):
        s = internal_offsets[sample_idx]
        e = internal_offsets[sample_idx + 1]
        sample_data = raw[s:e]
        
        if len(sample_data) < 20:
            continue
        
        print(f"\nSample[{sample_idx}]: offset 0x{s:x}-0x{e:x}, size={len(sample_data)} bytes")
        
        # Try IMA ADPCM 4-bit -> 8-bit PCM
        for init_pred in [0, 128]:
            for init_idx in [0, 10, 20, 40]:
                decoded_8bit = ima_adpcm_decode_8bit(sample_data, init_pred, init_idx)
                for sr in [5512, 8000, 11025, 16000, 22050]:
                    wav = pcm_to_wav(decoded_8bit, sr, bits_per_sample=8)
                    (output_dir / f"sample{sample_idx}_adpcm8_p{init_pred}_i{init_idx}_{sr}hz.wav").write_bytes(wav)
        
        # Try IMA ADPCM 4-bit -> 16-bit PCM
        for init_pred in [0, 128, 1024]:
            for init_idx in [0, 10, 20, 40]:
                decoded_16bit = ima_adpcm_decode_16bit(sample_data, init_pred, init_idx)
                for sr in [5512, 8000, 11025, 16000, 22050]:
                    wav = pcm_to_wav(decoded_16bit, sr, bits_per_sample=16)
                    (output_dir / f"sample{sample_idx}_adpcm16_p{init_pred}_i{init_idx}_{sr}hz.wav").write_bytes(wav)
        
        # Also try: treat as raw 16-bit LE PCM
        if len(sample_data) % 2 == 0:
            for sr in [5512, 8000, 11025, 16000, 22050]:
                wav = pcm_to_wav(sample_data, sr, bits_per_sample=16)
                (output_dir / f"sample{sample_idx}_raw16le_{sr}hz.wav").write_bytes(wav)
        
        # Try: treat as raw 8-bit PCM
        for sr in [5512, 8000, 11025, 16000, 22050]:
            wav = pcm_to_wav(sample_data, sr, bits_per_sample=8)
            (output_dir / f"sample{sample_idx}_raw8_{sr}hz.wav").write_bytes(wav)
    
    print(f"\nGenerated files in: {output_dir}")
    print("Please test and tell me which one sounds like thunder/lightning")


if __name__ == "__main__":
    main()
