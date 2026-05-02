#!/usr/bin/env python3
"""
优化闪电音效 - 使其更像闪电而不是风声

闪电特征：
1. 尖锐的起音（快速冲击）
2. 低频轰鸣（打雷感）
3. 高频碎裂声（电弧）
4. 短促但有回音衰减
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

out_dir = 'output/sfx_wav/res078_lightning_v2'
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

def apply_sharp_attack(pcm_data, attack_samples=5):
    """增强起音 - 让开始更尖锐"""
    samples = struct.unpack(f'<{len(pcm_data)//2}h', pcm_data)
    result = list(samples)
    
    # 前几个样本快速上升到最大值
    for i in range(min(attack_samples, len(samples))):
        factor = (i + 1) / attack_samples
        result[i] = int(samples[i] * factor * 2)
    
    return b''.join(struct.pack('<h', max(-32768, min(32767, s))) for s in result)

def apply_bass_rumble(pcm_data, intensity=0.8):
    """添加低频轰鸣 - 模拟雷声"""
    samples = struct.unpack(f'<{len(pcm_data)//2}h', pcm_data)
    result = list(samples)
    
    # 计算低频成分
    window = 10
    for i in range(len(samples)):
        start = max(0, i - window)
        end = min(len(samples), i + window + 1)
        low_freq = int(sum(samples[start:end]) / (end - start))
        # 叠加低频
        result[i] = int(samples[i] * 0.6 + low_freq * intensity)
    
    return b''.join(struct.pack('<h', max(-32768, min(32767, s))) for s in result)

def add_crackle(pcm_data, intensity=0.3):
    """添加高频碎裂声 - 模拟电弧"""
    import random
    random.seed(42)  # 可重复
    
    samples = struct.unpack(f'<{len(pcm_data)//2}h', pcm_data)
    result = list(samples)
    
    # 随机添加尖锐的脉冲
    for i in range(0, len(samples), 3):
        if random.random() < 0.1:
            spike = random.randint(-20000, 20000) * intensity
            result[i] = int(samples[i] + spike)
    
    return b''.join(struct.pack('<h', max(-32768, min(32767, s))) for s in result)

def apply_decay_envelope(pcm_data, decay_ms=500, sample_rate=4000):
    """应用衰减包络 - 闪电快速消失"""
    samples = struct.unpack(f'<{len(pcm_data)//2}h', pcm_data)
    decay_samples = int(decay_ms * sample_rate / 1000)
    
    result = []
    for i, s in enumerate(samples):
        if i < decay_samples:
            envelope = 1.0 - (i / decay_samples) * 0.7
        else:
            envelope = 0.3
        result.append(int(s * envelope))
    
    return b''.join(struct.pack('<h', max(-32768, min(32767, s))) for s in result)

def apply_distortion(pcm_data, amount=0.5):
    """轻度失真 - 增加粗糙感"""
    samples = struct.unpack(f'<{len(pcm_data)//2}h', pcm_data)
    result = []
    
    for s in samples:
        # 软削波
        val = s / 32767.0
        val = val * (1 + amount)
        val = max(-1.0, min(1.0, val))
        result.append(int(val * 32767))
    
    return b''.join(struct.pack('<h', s) for s in result)

print("\n=== 闪电音效优化 ===")

base_pcm = pcm8_to_pcm16(sample_data)

# 1. 基础版本
print("\n--- 基础版本 ---")
for sr in [4000, 5000, 6000, 8000]:
    save_wav(base_pcm, sr, f'{out_dir}/base_{sr}hz.wav')

# 2. 增强起音
print("\n--- 增强起音 ---")
for attack in [2, 5, 10]:
    pcm = apply_sharp_attack(base_pcm, attack)
    save_wav(pcm, 4000, f'{out_dir}/attack{attack}_4000hz.wav')

# 3. 低频轰鸣
print("\n--- 低频轰鸣 ---")
for intensity in [0.3, 0.5, 0.8, 1.0]:
    pcm = apply_bass_rumble(base_pcm, intensity)
    save_wav(pcm, 4000, f'{out_dir}/bass{intensity:.1f}_4000hz.wav')

# 4. 添加碎裂声
print("\n--- 添加碎裂声 ---")
for intensity in [0.1, 0.2, 0.3, 0.5]:
    pcm = add_crackle(base_pcm, intensity)
    save_wav(pcm, 4000, f'{out_dir}/crackle{intensity:.1f}_4000hz.wav')

# 5. 衰减包络
print("\n--- 衰减包络 ---")
for decay in [300, 500, 800]:
    pcm = apply_decay_envelope(base_pcm, decay, 4000)
    save_wav(pcm, 4000, f'{out_dir}/decay{decay}ms_4000hz.wav')

# 6. 组合效果
print("\n--- 组合效果 ---")

# 组合1: 起音 + 低频
pcm = apply_sharp_attack(base_pcm, 5)
pcm = apply_bass_rumble(pcm, 0.5)
save_wav(pcm, 4000, f'{out_dir}/combo1_attack_bass_4000hz.wav')

# 组合2: 起音 + 低频 + 碎裂
pcm = apply_sharp_attack(base_pcm, 5)
pcm = apply_bass_rumble(pcm, 0.5)
pcm = add_crackle(pcm, 0.2)
save_wav(pcm, 4000, f'{out_dir}/combo2_attack_bass_crackle_4000hz.wav')

# 组合3: 完整链 - 起音 + 低频 + 碎裂 + 衰减
pcm = apply_sharp_attack(base_pcm, 5)
pcm = apply_bass_rumble(pcm, 0.5)
pcm = add_crackle(pcm, 0.2)
pcm = apply_decay_envelope(pcm, 500, 4000)
save_wav(pcm, 4000, f'{out_dir}/combo3_full_chain_4000hz.wav')

# 组合4: 低频 + 失真
pcm = apply_bass_rumble(base_pcm, 0.8)
pcm = apply_distortion(pcm, 0.3)
save_wav(pcm, 4000, f'{out_dir}/combo4_bass_distortion_4000hz.wav')

# 组合5: 起音 + 低频 + 失真 + 衰减
pcm = apply_sharp_attack(base_pcm, 5)
pcm = apply_bass_rumble(pcm, 0.8)
pcm = apply_distortion(pcm, 0.3)
pcm = apply_decay_envelope(pcm, 500, 4000)
save_wav(pcm, 4000, f'{out_dir}/combo5_full_distortion_4000hz.wav')

# 7. 不同采样率的完整处理
print("\n--- 不同采样率完整处理 ---")
for sr in [4000, 5000, 6000, 8000]:
    pcm = apply_sharp_attack(base_pcm, 5)
    pcm = apply_bass_rumble(pcm, 0.5)
    pcm = add_crackle(pcm, 0.2)
    pcm = apply_decay_envelope(pcm, 500, sr)
    save_wav(pcm, sr, f'{out_dir}/full_chain_{sr}hz.wav')

print(f"\n完成! 文件保存到 {out_dir}/")
print("\n重点试听:")
print("  1. base_4000hz.wav (原始基础版本)")
print("  2. combo1_attack_bass_4000hz.wav (起音+低频)")
print("  3. combo2_attack_bass_crackle_4000hz.wav (起音+低频+碎裂)")
print("  4. combo3_full_chain_4000hz.wav (完整处理链)")
print("  5. combo5_full_distortion_4000hz.wav (完整+失真)")
print("  6. full_chain_8000hz.wav (高采样率完整处理)")
