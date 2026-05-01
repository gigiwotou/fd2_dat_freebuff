#!/usr/bin/env python3
"""
Test multiple audio format variations to find the correct one.
User feedback: "可以听到声音，每个目录下的音频听起来相同，能听出由节奏，
但声音尖锐，并伴有杂音。"

问题分析：
1. 能听出节奏 = 确实是音频数据，位置正确
2. 声音尖锐 = 可能采样率太低（实际应该更高）或解码方式错误
3. 有杂音 = 可能包含了文件头/偏移表等非音频数据，或者字节序错误

需要测试更多格式：
- 原始数据可能是 16-bit PCM (little-endian)
- 可能是 signed 而不是 unsigned
- 可能是立体声 (stereo)
- 采样率可能不是 11025 (可能是 22050, 44100 等)
- 数据可能是字节反转的
- 可能需要过滤掉某些特定的头部结构
"""

import struct
import wave
import io
from pathlib import Path


def pcm_to_wav(pcm_data, sample_rate=11025, channels=1, bits_per_sample=8, signed=False):
    """Convert raw PCM data to WAV format."""
    wav_buffer = io.BytesIO()
    with wave.open(wav_buffer, 'wb') as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(bits_per_sample // 8)
        wf.setframerate(sample_rate)
        
        # If unsigned 8-bit, data should already be in correct format
        # If signed 8-bit, convert from unsigned
        if bits_per_sample == 8 and not signed:
            wf.writeframes(pcm_data)
        else:
            wf.writeframes(pcm_data)
    return wav_buffer.getvalue()


def convert_unsigned_to_signed_8bit(data):
    """Convert unsigned 8-bit PCM (0-255) to signed 8-bit PCM (-128 to 127)."""
    return bytes((b - 128) % 256 for b in data)


def convert_signed_to_unsigned_8bit(data):
    """Convert signed 8-bit PCM (-128 to 127) to unsigned 8-bit PCM (0-255)."""
    return bytes((b + 128) % 256 for b in data)


def reverse_byte_order_16bit(data):
    """Reverse byte order for 16-bit data (swap low/high bytes)."""
    if len(data) % 2 != 0:
        data = data[:-1]  # Remove last byte if odd length
    
    result = bytearray()
    for i in range(0, len(data), 2):
        result.append(data[i + 1])  # High byte first
        result.append(data[i])       # Low byte second
    return bytes(result)


def extract_interleaved_stereo(data):
    """Extract left or right channel from interleaved stereo data."""
    left = data[0::2]   # Even bytes
    right = data[1::2]  # Odd bytes
    return left, right


def ima_adpcm_decode_8bit(adpcm_data, initial_predictor=128, initial_index=0):
    """
    Decode IMA ADPCM 4-bit data to 8-bit unsigned PCM.
    """
    if len(adpcm_data) < 2:
        return bytes(adpcm_data)
    
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


def main():
    with open("game/FDOTHER.DAT", "rb") as f:
        data = f.read()
    
    count = struct.unpack_from('<I', data, 6)[0]
    offsets = []
    for i in range(count):
        off = struct.unpack_from('<I', data, 10 + i * 4)[0]
        offsets.append(off)
    
    output_dir = Path("output/sfx_format_test3")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Test resource 9 (274 bytes - simple structure)
    test_resources = [9, 15, 78]
    
    for res_idx in test_resources:
        if res_idx >= len(offsets):
            continue
            
        start = offsets[res_idx]
        end = offsets[res_idx + 1] if res_idx + 1 < len(offsets) else len(data)
        raw = data[start:end]
        
        res_dir = output_dir / f"res{res_idx}_{len(raw)}bytes"
        res_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"\n{'='*60}")
        print(f"Resource [{res_idx}] - {len(raw)} bytes")
        print(f"First 32 bytes: {raw[:32].hex()}")
        
        # Test different header skip sizes
        for hdr_skip in [0, 2, 4, 6, 8, 12, 16]:
            if len(raw) <= hdr_skip + 10:
                continue
            
            audio_data = raw[hdr_skip:]
            
            # ===== Test Group 1: 8-bit unsigned PCM at different sample rates =====
            for sr in [5512, 8000, 11025, 16000, 22050, 32000, 44100]:
                wav = pcm_to_wav(audio_data, sr, channels=1, bits_per_sample=8)
                (res_dir / f"skip{hdr_skip}_u8_{sr}hz.wav").write_bytes(wav)
            
            # ===== Test Group 2: 8-bit signed PCM =====
            signed_data = convert_unsigned_to_signed_8bit(audio_data)
            for sr in [5512, 8000, 11025, 16000, 22050, 32000, 44100]:
                wav = pcm_to_wav(signed_data, sr, channels=1, bits_per_sample=8)
                (res_dir / f"skip{hdr_skip}_s8_{sr}hz.wav").write_bytes(wav)
            
            # ===== Test Group 3: 16-bit PCM (little-endian) =====
            if len(audio_data) >= 4:
                # Make even length
                if len(audio_data) % 2 != 0:
                    audio_data_16 = audio_data[:-1]
                else:
                    audio_data_16 = audio_data
                
                for sr in [5512, 8000, 11025, 16000, 22050, 32000, 44100]:
                    wav = pcm_to_wav(audio_data_16, sr, channels=1, bits_per_sample=16)
                    (res_dir / f"skip{hdr_skip}_le16_{sr}hz.wav").write_bytes(wav)
                
                # Test with byte-swapped 16-bit
                swapped = reverse_byte_order_16bit(audio_data_16)
                for sr in [5512, 8000, 11025, 16000, 22050, 32000, 44100]:
                    wav = pcm_to_wav(swapped, sr, channels=1, bits_per_sample=16)
                    (res_dir / f"skip{hdr_skip}_be16_{sr}hz.wav").write_bytes(wav)
                
                # Test stereo (16-bit)
                left, right = extract_interleaved_stereo(audio_data_16)
                for sr in [5512, 8000, 11025, 16000, 22050, 32000, 44100]:
                    # Left channel only
                    wav = pcm_to_wav(left, sr, channels=1, bits_per_sample=16)
                    (res_dir / f"skip{hdr_skip}_stereo_L_{sr}hz.wav").write_bytes(wav)
                    
                    # Right channel only
                    wav = pcm_to_wav(right, sr, channels=1, bits_per_sample=16)
                    (res_dir / f"skip{hdr_skip}_stereo_R_{sr}hz.wav").write_bytes(wav)
            
            # ===== Test Group 4: IMA ADPCM with different initial parameters =====
            for init_pred in [0, 64, 128, 192, 255]:
                for init_idx in [0, 10, 20, 30, 40]:
                    decoded = ima_adpcm_decode_8bit(audio_data, init_pred, init_idx)
                    for sr in [5512, 8000, 11025, 22050]:
                        wav = pcm_to_wav(decoded, sr, channels=1, bits_per_sample=8)
                        (res_dir / f"skip{hdr_skip}_adpcm_p{init_pred}_i{init_idx}_{sr}hz.wav").write_bytes(wav)
        
        print(f"Generated WAV files in: {res_dir}")
        print("Please test files with names like:")
        print("  - skip0_u8_22050hz.wav          (8-bit unsigned, 22050 Hz)")
        print("  - skip4_s8_11025hz.wav          (8-bit signed, skip 4 bytes)")
        print("  - skip0_le16_22050hz.wav        (16-bit little-endian, 22050 Hz)")
        print("  - skip0_be16_11025hz.wav        (16-bit big-endian, 11025 Hz)")
        print("  - skip0_stereo_L_22050hz.wav    (Stereo left channel)")
        print("  - skip0_adpcm_p128_i0_11025hz.wav (IMA ADPCM default)")


if __name__ == "__main__":
    main()
