#!/usr/bin/env python3
"""
基于用户反馈优化闪电音效
用户确认：节奏是闪电，8bit_4000hz更像，但像风声

风声特征：高频连续、无尖锐起音、缺乏冲击感
闪电特征：瞬间尖锐起音、低频轰鸣、高频碎裂、快速衰减

优化方向：
1. 保持4000Hz采样率和8-bit PCM格式
2. 增强低频减少风声感
3. 添加尖锐起音
4. 添加冲击脉冲
"""
import struct
import os
import wave

# 加载样本数据
with open('output/sfx_wav/res078_correct/sample0.bin', 'rb') as f:
    sample_data = f.read()

# 确保长度是偶数
if len(sample_data) % 2 != 0:
    sample_data = sample_data[:-1]

print(f"样本大小: {len(sample_data)} bytes")

out_dir = 'output/sfx_wav/res078_lightning_v4'
os.makedirs(out_dir, exist_ok=True)

def save_wav(pcm_data, sample_rate, filename):
    with wave.open(filename, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm_data)
    print(f"  保存: {filename}")

def pcm8_to_pcm16(pcm8):
    """8-bit unsigned 转 16-bit signed"""
    return bytes([b ^ 0x80 for b in pcm8])

def apply_lowpass_filter(pcm_data, window_size=3):
    """低通滤波 - 减少高频风声"""
    samples = struct.unpack(f'<{len(pcm_data)//2}h', pcm_data)
    result = list(samples)
    
    for _ in range(2):  # 应用2次
        prev = result[:]
        for i in range(1, len(samples)-1):
            result[i] = int(prev[i-1] * 0.25 + prev[i] * 0.5 + prev[i+1] * 0.25)
    
    return b''.join(struct.pack('<h', max(-32768, min(32767, s))) for s in result)

def apply_bass_enhance(pcm_data, factor=0.5):
    """低频增强 - 减少风声感"""
    samples = struct.unpack(f'<{len(pcm_data)//2}h', pcm_data)
    result = list(samples)
    
    window = 10
    for i in range(len(samples)):
        start = max(0, i - window)
        end = min(len(samples), i + window + 1)
        bass = int(sum(samples[start:end]) / (end - start))
        result[i] = int(samples[i] * 0.7 + bass * factor)
    
    return b''.join(struct.pack('<h', max(-32768, min(32767, s))) for s in result)

def apply_sharp_attack(pcm_data, attack_samples=5):
    """尖锐起音 - 模拟闪电瞬间"""
    samples = struct.unpack(f'<{len(pcm_data)//2}h', pcm_data)
    result = list(samples)
    
    # 前几个样本快速上升
    for i in range(min(attack_samples, len(samples))):
        envelope = (i + 1) / attack_samples
        result[i] = int(samples[i] * envelope * 2)
    
    return b''.join(struct.pack('<h', max(-32768, min(32767, s))) for s in result)

def apply_impulse(pcm_data, strength=0.3, duration=8):
    """添加冲击脉冲"""
    samples = struct.unpack(f'<{len(pcm_data)//2}h', pcm_data)
    result = list(samples)
    
    for i in range(min(duration, len(samples))):
        impulse = int(25000 * strength * (1 - i/duration))
        result[i] = int(samples[i] + impulse * (1 if i % 2 == 0 else -1))
    
    return b''.join(struct.pack('<h', max(-32768, min(32767, s))) for s in result)

def apply_decay(pcm_data, decay_ms=300, sample_rate=4000):
    """衰减包络"""
    samples = struct.unpack(f'<{len(pcm_data)//2}h', pcm_data)
    decay_samples = int(decay_ms * sample_rate / 1000)
    
    result = []
    for i, s in enumerate(samples):
        if i < decay_samples:
            envelope = 1.0 - (i / decay_samples) * 0.6
        else:
            envelope = 0.4
        result.append(int(s * envelope))
    
    return b''.join(struct.pack('<h', max(-32768, min(32767, s))) for s in result)

print("\n=== 基于用户反馈优化 ===")

base_pcm = pcm8_to_pcm16(sample_data)

# 1. 基础版本（用户确认的）
print("\n--- 基础版本 ---")
save_wav(base_pcm, 4000, f'{out_dir}/base_4000hz.wav')

# 2. 低频增强（减少风声）
print("\n--- 低频增强 ---")
for factor in [0.3, 0.5, 0.7, 1.0]:
    pcm = apply_bass_enhance(base_pcm, factor)
    save_wav(pcm, 4000, f'{out_dir}/bass{factor:.1f}_4000hz.wav')

# 3. 低通滤波（减少高频风声）
print("\n--- 低通滤波 ---")
for window in [2, 3, 5]:
    pcm = apply_lowpass_filter(base_pcm, window)
    save_wav(pcm, 4000, f'{out_dir}/lowpass_w{window}_4000hz.wav')

# 4. 尖锐起音
print("\n--- 尖锐起音 ---")
for attack in [3, 5, 8, 10]:
    pcm = apply_sharp_attack(base_pcm, attack)
    save_wav(pcm, 4000, f'{out_dir}/attack{attack}_4000hz.wav')

# 5. 冲击脉冲
print("\n--- 冲击脉冲 ---")
for strength in [0.2, 0.3, 0.5]:
    pcm = apply_impulse(base_pcm, strength)
    save_wav(pcm, 4000, f'{out_dir}/impulse{strength:.1f}_4000hz.wav')

# 6. 组合效果
print("\n--- 组合效果 ---")

# 组合1: 低频 + 起音
pcm = apply_bass_enhance(base_pcm, 0.5)
pcm = apply_sharp_attack(pcm, 5)
save_wav(pcm, 4000, f'{out_dir}/combo1_bass_attack_4000hz.wav')

# 组合2: 低通 + 低频 + 起音
pcm = apply_lowpass_filter(base_pcm, 3)
pcm = apply_bass_enhance(pcm, 0.5)
pcm = apply_sharp_attack(pcm, 5)
save_wav(pcm, 4000, f'{out_dir}/combo2_lowpass_bass_attack_4000hz.wav')

# 组合3: 冲击 + 低频 + 起音
pcm = apply_impulse(base_pcm, 0.3)
pcm = apply_bass_enhance(pcm, 0.5)
pcm = apply_sharp_attack(pcm, 5)
save_wav(pcm, 4000, f'{out_dir}/combo3_impulse_bass_attack_4000hz.wav')

# 组合4: 完整处理链
pcm = apply_impulse(base_pcm, 0.3)
pcm = apply_lowpass_filter(pcm, 3)
pcm = apply_bass_enhance(pcm, 0.5)
pcm = apply_sharp_attack(pcm, 5)
pcm = apply_decay(pcm, 300, 4000)
save_wav(pcm, 4000, f'{out_dir}/combo4_full_lightning_4000hz.wav')

# 组合5: 另一个完整链
pcm = apply_sharp_attack(base_pcm, 5)
pcm = apply_bass_enhance(pcm, 0.7)
pcm = apply_impulse(pcm, 0.2)
pcm = apply_decay(pcm, 400, 4000)
save_wav(pcm, 4000, f'{out_dir}/combo5_alternative_4000hz.wav')

print(f"\n完成! 文件保存到 {out_dir}/")
print("\n重点试听:")
print("  1. base_4000hz.wav (原始确认版本)")
print("  2. bass0.5_4000hz.wav (低频增强)")
print("  3. combo1_bass_attack_4000hz.wav (低频+起音)")
print("  4. combo2_lowpass_bass_attack_4000hz.wav (低通+低频+起音)")
print("  5. combo4_full_lightning_4000hz.wav (完整处理链)")
