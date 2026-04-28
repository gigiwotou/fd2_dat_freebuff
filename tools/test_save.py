#!/usr/bin/env python3
"""测试PIL保存"""

import struct
from pathlib import Path
from PIL import Image

fdshap = Path("game/FDSHAP.DAT").read_bytes()

# 简单测试
img = Image.new("RGB", (100, 100), (255, 0, 0))
output_path = Path("output/maps/test_save.png")
print(f"尝试保存到: {output_path.absolute()}")
print(f"目录存在: {output_path.parent.exists()}")

try:
    img.save(str(output_path))
    print(f"保存成功!")
    print(f"文件存在: {output_path.exists()}")
except Exception as e:
    print(f"保存失败: {e}")
