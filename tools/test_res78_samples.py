#!/usr/bin/env python3
"""
为 res78 闪电音效生成更多测试变体，特别是跳过内部偏移表后的样本数据。
"""

import struct
import wave
import io
from pathlib import Path


def convert_to_be16_audio(data):
    if len(data) % 2 != 0:
        data = data[:-1]
    result = bytearray()
    for i in range(0, len(data), 2):
        result.append(data[i + 1])
        result.append(data[i])
    return bytes(result)


def pcm16_to_wav(pcm_data, sample_rate=8000, channels=1):
    if len(pcm_data) % 2 != 0:
        pcm_data = pcm_data[:-1]
    wav_buffer = io.BytesIO()
    with wave.open(wav_buffer, 'wb') as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(2)
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
    start = offsets[res_idx]
    end = offsets[res_idx + 1] if res_idx + 1 < len(offsets) else len(data)
    raw = data[start:end]
    
    output_dir = Path("output/sfx_wav/res078_lightning_test3")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Resource [{res_idx}] - {len(raw)} bytes")
    
    # Parse internal structure: first 4 bytes = (count1, count2)
    count1 = struct.unpack_from('<H', raw, 0)[0]
    count2 = struct.unpack_from('<H', raw, 2)[0]
    print(f"Header: count1={count1}, count2={count2}")
    
    # Read offset table starting at byte 4
    internal_offsets = []
    for i in range(count2):
        pos = 4 + i * 4
        if pos + 4 <= len(raw):
            val = struct.unpack_from('<I', raw, pos)[0]
            internal_offsets.append(val)
            print(f"  internal_offset[{i}] = 0x{val:x} ({val})")
    
    # Extract individual samples based on internal offsets
    if len(internal_offsets) > 1:
        for i in range(len(internal_offsets) - 1):
            s = internal_offsets[i]
            e = internal_offsets[i + 1]
            if s < len(raw) and e <= len(raw) and e > s:
                sample_data = raw[s:e]
                print(f"\nSample[{i}]: offset 0x{s:x}-0x{e:x}, size={len(sample_data)} bytes")
                print(f"  First 32 bytes: {sample_data[:32].hex()}")
                
                be16 = convert_to_be16_audio(sample_data)
                
                # Try different sample rates for each sample
                for sr in [2000, 4000, 5512, 8000, 11025, 16000]:
                    wav = pcm16_to_wav(be16, sr)
                    (output_dir / f"sample{i}_{sr}hz.wav").write_bytes(wav)
    
    # Also try: skip the entire header (count1*4 + 4 bytes) and treat rest as audio
    header_size = 4 + count2 * 4
    if len(raw) > header_size + 100:
        audio_data = raw[header_size:]
        print(f"\nSkipping header ({header_size} bytes): {len(audio_data)} bytes of audio data")
        print(f"  First 32 bytes: {audio_data[:32].hex()}")
        
        be16 = convert_to_be16_audio(audio_data)
        
        for sr in [2000, 4000, 5512, 8000, 11025, 16000]:
            wav = pcm16_to_wav(be16, sr)
            (output_dir / f"skip_header_{sr}hz.wav").write_bytes(wav)
        
        # Also try skip_header with further offsets
        val1 = struct.unpack_from('<H', audio_data, 0)[0]
        val2 = struct.unpack_from('<H', audio_data, 2)[0]
        print(f"  After header: val1={val1}, val2={val2}")
        
        if val1 > 0 and val1 < 50 and val2 > 0 and val2 < 50:
            sub_offsets = []
            for i in range(val2):
                pos = 4 + i * 4
                if pos + 4 <= len(audio_data):
                    sub_val = struct.unpack_from('<I', audio_data, pos)[0]
                    sub_offsets.append(sub_val)
            
            if len(sub_offsets) > 1:
                for i in range(len(sub_offsets) - 1):
                    s = sub_offsets[i]
                    e = sub_offsets[i + 1]
                    if s < len(audio_data) and e <= len(audio_data) and e > s and (e - s) > 50:
                        sub_sample = audio_data[s:e]
                        be16_sub = convert_to_be16_audio(sub_sample)
                        for sr in [2000, 4000, 5512, 8000, 11025]:
                            wav = pcm16_to_wav(be16_sub, sr)
                            (output_dir / f"sub_sample{i}_{sr}hz.wav").write_bytes(wav)
                        print(f"  Sub-sample[{i}]: offset 0x{s:x}-0x{e:x}, size={e-s} bytes")
    
    print(f"\n生成的测试文件在: {output_dir}")
    print("\n建议试听:")
    print("  sample0_*.wav - 第一个内部样本（较小，可能是元数据）")
    print("  sample1_*.wav - 第二个内部样本（较大，可能是实际音效）")
    print("  skip_header_*.wav - 跳过整个头部后的数据")


if __name__ == "__main__":
    main()
