#!/usr/bin/env python3
"""
尝试差分编码和其他编码方式解码闪电音效
"""
import struct
import os
import wave

def write_wav(filepath, sample_rate, data, sample_width=2):
    with wave.open(filepath, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(sample_width)
        wf.setframerate(sample_rate)
        wf.writeframes(data)

def decode_dpcm(data, initial=128):
    """DPCM解码: 每个字节是差值"""
    output = []
    val = initial
    for byte in data:
        # 有符号差值
        delta = byte - 128 if byte >= 128 else byte
        val = max(0, min(255, val + delta))
        output.append(val)
    return bytes(output)

def decode_dpcm16(data, initial=0):
    """16-bit DPCM解码: 每2字节是差值"""
    output = []
    val = initial
    for i in range(0, len(data) - 1, 2):
        delta = struct.unpack_from('<h', data, i)[0]
        val = max(-32768, min(32767, val + delta))
        output.append(struct.pack('<h', val))
    return b''.join(output)

def decode_dpcm_scaled(data, initial=128, scale=1):
    """DPCM解码带缩放因子"""
    output = []
    val = initial
    for byte in data:
        delta = (byte - 128) * scale
        val = max(0, min(255, val + delta))
        output.append(val)
    return bytes(output)

def decode_adpcm_yamaha(data, initial_predictor=0, initial_step=0):
    """Yamaha ADPCM解码"""
    STEP_TABLE = [
        1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16,
        17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32,
        33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48,
        49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64,
        80, 96, 112, 128, 144, 160, 176, 192, 208, 224, 240, 256, 272, 288, 304, 320,
        384, 448, 512, 576, 640, 704, 768, 832, 896, 960, 1024, 1088, 1152, 1216, 1280, 1408,
        1536, 1664, 1792, 1920, 2048, 2176, 2304, 2432, 2560, 2816, 3072, 3328, 3584, 3840, 4096, 4480,
        4864, 5376, 5760, 6144, 6656, 7168, 7680, 8192
    ]
    INDEX_TABLE = [1, 1, 1, 1, 1, 1, 1, 1, -1, -1, -1, -1, -1, -1, -1, -1]
    
    output = []
    predictor = initial_predictor
    step_index = initial_step
    
    for byte in data:
        for nibble in [(byte >> 4) & 0x0F, byte & 0x0F]:
            step = STEP_TABLE[step_index]
            diff = step >> 3
            if nibble & 1: diff += step >> 2
            if nibble & 2: diff += step >> 1
            if nibble & 4: diff += step
            
            if nibble & 8:
                predictor -= diff
            else:
                predictor += diff
            
            predictor = max(-128, min(127, predictor))
            output.append(struct.pack('<h', predictor * 256))
            
            step_index += INDEX_TABLE[nibble]
            step_index = max(0, min(88, step_index))
    
    return b''.join(output)

def main():
    base_dir = os.path.dirname(os.path.dirname(__file__))
    sample_path = os.path.join(base_dir, 'output', 'sfx_wav', 'lightning_correct', 'lightning_6359.bin')
    
    with open(sample_path, 'rb') as f:
        sample_data = f.read()
    
    # 跳过16字节头
    audio_data = sample_data[16:]
    
    output_dir = os.path.join(base_dir, 'output', 'sfx_wav', 'lightning_v3')
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"样本大小: {len(sample_data)}, 音频数据: {len(audio_data)}")
    
    # 1. 差分编码 DPCM (8-bit)
    for rate in [5512, 8000, 11025, 16000, 22050]:
        for init in [0, 128, 100, 150]:
            decoded = decode_dpcm(audio_data, initial=init)
            write_wav(os.path.join(output_dir, f'dpcm_init{init}_{rate}hz.wav'), rate, decoded, 1)
    
    # 2. 带缩放的DPCM
    for rate in [5512, 8000, 11025]:
        for scale in [1, 2, 4, 8]:
            decoded = decode_dpcm_scaled(audio_data, initial=128, scale=scale)
            write_wav(os.path.join(output_dir, f'dpcm_scaled{scale}_{rate}hz.wav'), rate, decoded, 1)
    
    # 3. 16-bit DPCM
    for rate in [5512, 8000, 11025]:
        decoded = decode_dpcm16(audio_data, initial=0)
        write_wav(os.path.join(output_dir, f'dpcm16_{rate}hz.wav'), rate, decoded, 2)
    
    # 4. 直接作为有符号8-bit
    signed = bytes([(b - 128) % 256 for b in audio_data])
    for rate in [5512, 8000, 11025, 16000, 22050]:
        write_wav(os.path.join(output_dir, f'signed8_{rate}hz.wav'), rate, signed, 1)
    
    # 5. 尝试反转字节顺序
    reversed_data = audio_data[::-1]
    for rate in [5512, 8000, 11025]:
        write_wav(os.path.join(output_dir, f'reversed_8bit_{rate}hz.wav'), rate, reversed_data, 1)
    
    # 6. 尝试每两个字节作为一对 (big-endian 16-bit)
    be_data = b''
    for i in range(0, len(audio_data) - 1, 2):
        be_data += audio_data[i+1:i+2] + audio_data[i:i+1]
    for rate in [5512, 8000, 11025]:
        write_wav(os.path.join(output_dir, f'be16_{rate}hz.wav'), rate, be_data[:len(be_data)//2*2], 2)
    
    # 7. Yamaha ADPCM
    for rate in [5512, 8000, 11025]:
        decoded = decode_adpcm_yamaha(audio_data)
        write_wav(os.path.join(output_dir, f'yamaha_adpcm_{rate}hz.wav'), rate, decoded, 2)
    
    print(f"\n生成 {len(os.listdir(output_dir))} 个WAV文件到: {output_dir}")
    print("\n推荐试听:")
    print("  dpcm_init128_11025hz.wav")
    print("  dpcm_init128_8000hz.wav")
    print("  signed8_11025hz.wav")
    print("  dpcm_scaled2_11025hz.wav")
    print("  dpcm_scaled4_11025hz.wav")

if __name__ == '__main__':
    main()
