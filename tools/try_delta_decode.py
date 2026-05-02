#!/usr/bin/env python3
"""
尝试不同的解码方式 - 风声说明可能是差分编码而非直接PCM

风声特征：高频连续、缺乏瞬态
可能原因：数据是delta encoding而非直接PCM
"""
import struct
import os
import wave

# 加载样本数据
with open('output/sfx_wav/res078_correct/sample0.bin', 'rb') as f:
    sample_data = f.read()

print(f"样本大小: {len(sample_data)} bytes")
print(f"前32字节: {sample_data[:32].hex()}")

out_dir = 'output/sfx_wav/res078_delta'
os.makedirs(out_dir, exist_ok=True)

def save_wav(pcm_data, sample_rate, filename):
    with wave.open(filename, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm_data)
    print(f"  保存: {filename}")

def decode_delta8(data, initial_value=128):
    """8-bit delta解码 - 每个字节是前一个样本的差值"""
    result = []
    current = initial_value
    
    for byte in data:
        # 字节是有符号差值
        delta = byte if byte < 128 else byte - 256
        current = max(0, min(255, current + delta))
        result.append(current)
    
    # 转为signed PCM
    return bytes([b ^ 0x80 for b in result])

def decode_delta8_scaled(data, initial_value=128, scale=2):
    """8-bit delta解码（带缩放）"""
    result = []
    current = initial_value
    
    for byte in data:
        delta = (byte if byte < 128 else byte - 256) * scale
        current = max(0, min(255, current + delta))
        result.append(current)
    
    return bytes([b ^ 0x80 for b in result])

def decode_adaptive_delta(data, initial_value=128):
    """自适应delta解码"""
    result = []
    current = initial_value
    step = 4
    
    for byte in data:
        delta = byte if byte < 128 else byte - 256
        
        # 根据差值大小调整步长
        if abs(delta) > 64:
            step = max(4, step - 1)
        elif abs(delta) < 16:
            step = min(16, step + 1)
        
        current = max(0, min(255, current + delta * step // 4))
        result.append(current)
    
    return bytes([b ^ 0x80 for b in result])

def pcm8_to_pcm16(pcm8):
    """8-bit unsigned 转 16-bit signed"""
    if len(pcm8) % 2 != 0:
        pcm8 = pcm8[:-1]
    return bytes([b ^ 0x80 for b in pcm8])

def apply_lowpass(pcm_data, passes=2):
    """低通滤波"""
    # 确保长度是偶数
    if len(pcm_data) % 2 != 0:
        pcm_data = pcm_data[:-1]
    samples = struct.unpack(f'<{len(pcm_data)//2}h', pcm_data)
    result = list(samples)
    
    for _ in range(passes):
        prev = result[:]
        for i in range(1, len(samples)-1):
            result[i] = int(prev[i-1] * 0.25 + prev[i] * 0.5 + prev[i+1] * 0.25)
    
    return b''.join(struct.pack('<h', max(-32768, min(32767, s))) for s in result)

def apply_sharp_attack(pcm_data, attack_samples=5):
    """尖锐起音"""
    # 确保长度是偶数
    if len(pcm_data) % 2 != 0:
        pcm_data = pcm_data[:-1]
    samples = struct.unpack(f'<{len(pcm_data)//2}h', pcm_data)
    result = list(samples)
    
    for i in range(min(attack_samples, len(samples))):
        envelope = (i + 1) / attack_samples
        result[i] = int(samples[i] * envelope * 2)
    
    return b''.join(struct.pack('<h', max(-32768, min(32767, s))) for s in result)

print("\n=== 差分编码解码 ===")

# 1. Delta解码
print("\n--- Delta解码 ---")
for init in [0, 64, 128, 192]:
    pcm8 = decode_delta8(sample_data, init)
    pcm16 = bytes([b ^ 0x80 for b in pcm8])
    save_wav(pcm16, 4000, f'{out_dir}/delta_init{init}_4000hz.wav')

# 2. Delta解码（带缩放）
print("\n--- Delta解码（缩放） ---")
for scale in [1, 2, 4, 8]:
    pcm8 = decode_delta8_scaled(sample_data, 128, scale)
    pcm16 = bytes([b ^ 0x80 for b in pcm8])
    save_wav(pcm16, 4000, f'{out_dir}/delta_scaled{scale}_4000hz.wav')

# 3. 自适应Delta
print("\n--- 自适应Delta ---")
pcm8 = decode_adaptive_delta(sample_data, 128)
pcm16 = bytes([b ^ 0x80 for b in pcm8])
save_wav(pcm16, 4000, f'{out_dir}/adaptive_delta_4000hz.wav')

# 4. Delta + 后处理
print("\n--- Delta + 后处理 ---")
pcm8 = decode_delta8(sample_data, 128)
pcm16 = bytes([b ^ 0x80 for b in pcm8])

# 低通
pcm_lp = apply_lowpass(pcm16, 2)
save_wav(pcm_lp, 4000, f'{out_dir}/delta_lowpass_4000hz.wav')

# 起音增强
pcm_attack = apply_sharp_attack(pcm16, 5)
save_wav(pcm_attack, 4000, f'{out_dir}/delta_attack_4000hz.wav')

# 低通 + 起音
pcm_full = apply_lowpass(pcm16, 2)
pcm_full = apply_sharp_attack(pcm_full, 5)
save_wav(pcm_full, 4000, f'{out_dir}/delta_lowpass_attack_4000hz.wav')

# 5. 不同采样率的Delta
print("\n--- 不同采样率 ---")
pcm8 = decode_delta8(sample_data, 128)
pcm16 = bytes([b ^ 0x80 for b in pcm8])
for sr in [4000, 5000, 6000, 8000]:
    save_wav(pcm16, sr, f'{out_dir}/delta_{sr}hz.wav')

# 6. 原始PCM + 更激进的低通
print("\n--- 原始PCM + 激进低通 ---")
base_pcm = pcm8_to_pcm16(sample_data)
for passes in [3, 5, 8, 10]:
    pcm = apply_lowpass(base_pcm, passes)
    save_wav(pcm, 4000, f'{out_dir}/original_lowpass{passes}_4000hz.wav')

print(f"\n完成! 文件保存到 {out_dir}/")
print("\n重点试听:")
print("  1. delta_init128_4000hz.wav (Delta解码)")
print("  2. delta_scaled2_4000hz.wav (Delta缩放)")
print("  3. delta_lowpass_attack_4000hz.wav (Delta+后处理)")
print("  4. adaptive_delta_4000hz.wav (自适应Delta)")
print("  5. original_lowpass5_4000hz.wav (原始+激进低通)")
