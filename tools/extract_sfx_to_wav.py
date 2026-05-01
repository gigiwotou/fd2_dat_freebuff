#!/usr/bin/env python3
"""
Extract audio samples from FDOTHER.DAT and convert to WAV.

From IDA analysis:
1. sub_25A96 plays samples from a buffer loaded by sub_111BA
2. The buffer contains multiple samples with an index table
3. Sample format appears to be 8-bit unsigned PCM at 11025 Hz
4. The buffer structure (from resource #78 used in sub_20421):
   - First 6 bytes: "LLLLLL" or similar header
   - Next 4 bytes: sub-count
   - Next 4*count bytes: offset table
   - Each sub-resource starts with a 4-byte header (2 bytes size, 2 bytes unknown)
   
Key call chains:
- sub_20421 (a5==1): loads FDOTHER.DAT resource #78 (0x4E), plays sample #0 (lightning)
- sub_1F894 (scroll): calls sub_25A96 with _FDOTHER.DAT_ from resource #74 (0x4A)  
- Menu sounds: _FDOTHER.DAT_ from resource #7 (0x7) or #8 (0x8)
"""

import struct
import wave
import io
from pathlib import Path


def read_resource(fdother_data, index):
    """Read a single resource from FDOTHER.DAT by index."""
    count = struct.unpack_from('<I', fdother_data, 6)[0]
    if index >= count:
        return None
    
    offset_table_start = 10
    start = struct.unpack_from('<I', fdother_data, offset_table_start + index * 4)[0]
    end = struct.unpack_from('<I', fdother_data, offset_table_start + (index + 1) * 4)[0] if index + 1 < count else len(fdother_data)
    
    return fdother_data[start:end]


def parse_sample_buffer(raw_data, label=""):
    """
    Parse a sample buffer that contains multiple audio samples.
    
    Based on IDA analysis of sub_25A96:
    - a5+4*a6 gives the offset table entry
    - a5[6*a6] = sample offset
    - a5[10*a6] = next sample offset (or end)
    
    The buffer structure:
    - Header: may be "LLLLLL" or raw data
    - Offset table at specific positions
    """
    samples = {}
    
    # Try different header types
    if raw_data[:6] == b'LLLLLL':
        # LLLLLL header with sub-count
        sub_count = struct.unpack_from('<I', raw_data, 6)[0]
        offset_table = 10
        
        for i in range(min(sub_count, 20)):
            try:
                sub_off = struct.unpack_from('<I', raw_data, offset_table + i * 4)[0]
                sub_end = struct.unpack_from('<I', raw_data, offset_table + (i + 1) * 4)[0] if i + 1 < sub_count else len(raw_data)
                
                # Sanity check
                if sub_off >= len(raw_data) or sub_end > len(raw_data) or sub_off >= sub_end:
                    break
                
                sub_size = sub_end - sub_off
                sub_data = raw_data[sub_off:sub_end]
                
                # Check header pattern: 2 bytes size + 2 bytes unknown + audio data
                if len(sub_data) >= 4:
                    hdr_size = struct.unpack_from('<H', sub_data, 0)[0]
                    hdr_unknown = struct.unpack_from('<H', sub_data, 2)[0]
                    
                    # The actual audio data might start after the 4-byte header
                    # or might be the entire sub_data
                    audio_data = sub_data[4:] if hdr_size < sub_size else sub_data
                    
                    samples[i] = {
                        'offset': sub_off,
                        'size': sub_size,
                        'hdr_size': hdr_size,
                        'hdr_unknown': hdr_unknown,
                        'audio': audio_data
                    }
            except:
                break
        
        return {'type': 'LLLLLL', 'samples': samples}
    
    elif raw_data[:4] == b'LMI1':
        # LMI1 header - this is a different format (maybe compressed)
        offset_table = 4
        # Look for pattern of 4-byte offsets
        sub_count = 0
        for i in range(20):
            off_pos = offset_table + i * 4
            if off_pos + 4 > len(raw_data):
                break
            
            val = struct.unpack_from('<I', raw_data, off_pos)[0]
            if val < len(raw_data) and val > 0:
                sub_count = i + 1
            else:
                break
        
        return {'type': 'LMI1', 'sample_count': sub_count, 'data': raw_data}
    
    else:
        # Try to detect if it's raw sample data
        # Check for 4-byte offset table pattern
        return {'type': 'raw', 'data': raw_data}


def try_as_8bit_pcm(data, sample_rate=11025):
    """Convert raw 8-bit unsigned PCM to WAV."""
    wav_buffer = io.BytesIO()
    with wave.open(wav_buffer, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(1)  # 8-bit
        wf.setframerate(sample_rate)
        wf.writeframes(data)
    return wav_buffer.getvalue()


def try_as_adpcm(data, sample_rate=11025):
    """
    Try to decode as IMA ADPCM (4-bit).
    Each byte contains two 4-bit samples.
    """
    if len(data) < 2:
        return None
    
    # IMA ADPCM decoding
    step_table = [
        7, 8, 9, 10, 11, 12, 13, 14, 16, 17, 19, 21, 23, 25, 28, 31, 34,
        37, 41, 45, 50, 55, 60, 66, 73, 80, 88, 97, 107, 118, 130, 143,
        157, 173, 190, 209, 230, 253, 279, 307, 337, 371, 408, 449, 494,
        544, 598, 658, 724, 796, 876, 963, 1060, 1166, 1282, 1411, 1552,
        1707, 1878, 2066, 2272, 2499, 2749, 3024, 3327, 3660, 4026, 4428,
        4871, 5358, 5894, 6484, 7132, 7845, 8630, 9493, 10442, 11487,
        12635, 13899, 15289, 16818, 18500, 20350, 22385, 24623, 27086,
        29794, 32767
    ]
    
    index_table = [-1, -1, -1, -1, 2, 4, 6, 8, -1, -1, -1, -1, 2, 4, 6, 8]
    
    # Decode each byte as two 4-bit nibbles
    output = []
    predictor = 128  # Start at center for 8-bit unsigned
    index = 0
    
    for byte in data:
        for nibble in [(byte >> 4) & 0x0F, byte & 0x0F]:
            diff = nibble
            step = step_table[index]
            
            # Calculate difference
            delta = 0
            if diff & 0x04:
                delta += step
            if diff & 0x02:
                delta += step >> 1
            if diff & 0x01:
                delta += step >> 2
            delta += step >> 3
            
            if diff & 0x08:
                predictor -= delta
            else:
                predictor += delta
            
            # Clamp to 0-255
            predictor = max(0, min(255, predictor))
            
            # Update index
            index += index_table[diff]
            index = max(0, min(88, index))
            
            output.append(predictor)
    
    wav_buffer = io.BytesIO()
    with wave.open(wav_buffer, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(1)  # 8-bit
        wf.setframerate(sample_rate)
        wf.writeframes(bytes(output))
    
    return wav_buffer.getvalue()


def extract_sfx_from_resource(fdother_data, resource_idx, output_dir):
    """Extract all samples from a specific FDOTHER.DAT resource."""
    raw_data = read_resource(fdother_data, resource_idx)
    if raw_data is None:
        print(f"Resource [{resource_idx}] not found")
        return
    
    print(f"\n{'='*80}")
    print(f"Resource [{resource_idx}] - {len(raw_data)} bytes")
    print(f"First 32 bytes: {raw_data[:32].hex()}")
    
    # Parse the buffer
    parsed = parse_sample_buffer(raw_data, f"res_{resource_idx}")
    
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if parsed['type'] == 'LLLLLL' and parsed['samples']:
        print(f"  Format: LLLLLL with {len(parsed['samples'])} samples")
        
        for idx, sample_info in parsed['samples'].items():
            audio_data = sample_info['audio']
            
            # Try as 8-bit PCM
            wav_data = try_as_8bit_pcm(audio_data)
            wav_path = output_dir / f"res{resource_idx}_sample{idx:02d}_pcm.wav"
            wav_path.write_bytes(wav_data)
            
            # Try as ADPCM
            adpcm_data = try_as_adpcm(audio_data)
            adpcm_path = output_dir / f"res{resource_idx}_sample{idx:02d}_adpcm.wav"
            adpcm_path.write_bytes(adpcm_data)
            
            # Also save raw
            raw_path = output_dir / f"res{resource_idx}_sample{idx:02d}.raw"
            raw_path.write_bytes(audio_data)
            
            print(f"  Sample [{idx}]: hdr={sample_info['hdr_size']}+{sample_info['hdr_unknown']}, "
                  f"audio_size={len(audio_data)} -> {wav_path.name}")
    
    elif parsed['type'] == 'raw':
        # Try the entire resource as a single sample
        print(f"  Format: raw data")
        
        wav_data = try_as_8bit_pcm(raw_data)
        wav_path = output_dir / f"res{resource_idx}_raw_pcm.wav"
        wav_path.write_bytes(wav_data)
        
        adpcm_data = try_as_adpcm(raw_data)
        adpcm_path = output_dir / f"res{resource_idx}_raw_adpcm.wav"
        adpcm_path.write_bytes(adpcm_data)
        
        raw_path = output_dir / f"res{resource_idx}.raw"
        raw_path.write_bytes(raw_data)
        
        print(f"  -> Saved as PCM: {wav_path.name}")
        print(f"  -> Saved as ADPCM: {adpcm_path.name}")


def main():
    fdother_path = Path("game/FDOTHER.DAT")
    if not fdother_path.exists():
        print(f"Error: {fdother_path} not found")
        return
    
    with open(fdother_path, 'rb') as f:
        fdother_data = f.read()
    
    print(f"FDOTHER.DAT size: {len(fdother_data)} bytes")
    
    # Resources used for sound effects based on IDA analysis:
    # - Resource #78 (0x4E): Used in sub_20421 for lightning sound (ANI#3)
    # - Resource #74 (0x4A): Used in scroll animation sound triggers
    # - Resource #7: Used in menu phase (sub_25A96 calls)
    # - Resource #8: Also used in animation sounds
    
    output_dir = Path("output/sfx_extracted")
    
    # Extract from key resources
    for res_idx in [7, 8, 74, 78, 9, 15]:
        extract_sfx_from_resource(fdother_data, res_idx, output_dir / f"resource_{res_idx}")


if __name__ == "__main__":
    main()
