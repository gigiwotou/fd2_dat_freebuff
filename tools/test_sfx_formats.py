#!/usr/bin/env python3
"""
Try different audio formats to find the correct one for FDOTHER.DAT samples.
User feedback: audio plays with rhythm but sounds sharp/pitched with noise.
"""

import struct
import wave
import io
from pathlib import Path


def pcm8_to_wav(pcm_data, sample_rate=11025):
    wav_buffer = io.BytesIO()
    with wave.open(wav_buffer, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(1)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm_data)
    return wav_buffer.getvalue()


def pcm16le_to_wav(pcm_data, sample_rate=11025):
    wav_buffer = io.BytesIO()
    with wave.open(wav_buffer, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm_data)
    return wav_buffer.getvalue()


def decode_ima_adpcm_8bit(adpcm_data, initial_pred=128, initial_index=0):
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
    predictor = initial_pred
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
    
    offset_table_start = 10
    count = struct.unpack_from('<I', data, 6)[0]
    offsets = []
    for i in range(count):
        off = struct.unpack_from('<I', data, offset_table_start + i * 4)[0]
        offsets.append(off)
    
    output_dir = Path("output/sfx_format_test")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Test key resources
    test_resources = [7, 8, 9, 15, 74, 78]
    
    for res_idx in test_resources:
        if res_idx >= count:
            continue
        
        start = offsets[res_idx]
        end = offsets[res_idx + 1] if res_idx + 1 < count else len(data)
        raw = data[start:end]
        
        res_dir = output_dir / f"res{res_idx:03d}_{len(raw)}bytes"
        res_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"\n{'='*60}")
        print(f"Resource [{res_idx}] - {len(raw)} bytes")
        print(f"First 32: {raw[:32].hex()}")
        
        # Try different header skip sizes and formats
        header_sizes = [0, 4, 6, 8, 12, 16]
        
        for hdr_skip in header_sizes:
            if len(raw) <= hdr_skip + 10:
                continue
            
            audio_data = raw[hdr_skip:]
            
            # Format 1: Raw 8-bit unsigned PCM
            wav8 = pcm8_to_wav(audio_data, 11025)
            (res_dir / f"skip{hdr_skip}_8bit_11025.wav").write_bytes(wav8)
            
            # Format 1b: Raw 8-bit at different sample rates
            for sr in [8000, 12000, 16000, 22050]:
                wav8_sr = pcm8_to_wav(audio_data, sr)
                (res_dir / f"skip{hdr_skip}_8bit_{sr}.wav").write_bytes(wav8_sr)
            
            # Format 2: Raw 16-bit LE PCM (if data length is even)
            if len(audio_data) % 2 == 0:
                wav16 = pcm16le_to_wav(audio_data, 11025)
                (res_dir / f"skip{hdr_skip}_16bit_11025.wav").write_bytes(wav16)
            
            # Format 3: IMA ADPCM with different initial values
            for init_pred, init_idx in [(128, 0), (0, 0), (128, 4), (0, 4)]:
                try:
                    pcm = decode_ima_adpcm_8bit(audio_data, init_pred, init_idx)
                    wav = pcm8_to_wav(pcm, 11025)
                    (res_dir / f"skip{hdr_skip}_adpcm_p{init_pred}i{init_idx}.wav").write_bytes(wav)
                except:
                    pass
        
        # Save raw for external analysis
        (res_dir / "raw.bin").write_bytes(raw)
        
        # Statistical analysis
        print(f"  Stats: min={min(raw)}, max={max(raw)}, avg={sum(raw)/len(raw):.1f}")
        print(f"  Unique values: {len(set(raw))}")
        
        # Check if it's 16-bit aligned (pairs of bytes)
        if len(raw) > 4:
            # Look at byte pairs
            pairs = []
            for i in range(0, min(len(raw)-1, 100), 2):
                val_le = struct.unpack_from('<H', raw, i)[0]
                val_be = struct.unpack_from('>H', raw, i)[0]
                pairs.append((val_le, val_be))
            
            le_min = min(p[0] for p in pairs)
            le_max = max(p[0] for p in pairs)
            print(f"  16-bit LE range: {le_min}-{le_max}")
        
        print(f"  Generated {len(list(res_dir.glob('*.wav')))} WAV files")

if __name__ == "__main__":
    main()
