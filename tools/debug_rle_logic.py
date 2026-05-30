"""
根据MCP汇编代码精确分析RLE解码逻辑
"""

def analyze_rle_logic():
    """
    分析sub_4E98D的汇编代码逻辑：
    
    4e9e3  lodsb              ; 读取控制字节到al
    4e9e4  mov     cl, al     ; cl = 控制字节
    4e9e6  shl     cl, 1      ; cl左移1位，CF = 原bit7
    4e9e8  jb      short loc_4EA17  ; 如果CF=1(bit7=1)，跳转到4EA17
    
    ; bit7=0的分支
    4e9ea  shl     cl, 1      ; 再左移1位，CF = 原bit6
    4e9ec  jb      short loc_4EA00  ; 如果CF=1(bit6=1)，跳转到4EA00
    
    ; bit7=0, bit6=0 → FILL
    4e9ee  shr     cl, 2
    4e9f1  inc     cl
    4e9f3  sub     bx, cx
    4e9f6  lodsb              ; 读取填充值
    4e9f7  rep stosb          ; 填充count个位置
    
    ; 4EA00: bit7=0, bit6=1 → COPY特殊
    4ea00  shr     cl, 2
    4ea03  inc     cl
    4ea05  sub     bx, cx
    4ea08  sub     bx, cx     ; count_0减双倍
    4ea0b  lodsb              ; 读取要复制的值
    4ea0c  inc     edi
    4ea0d  stosb
    4ea0e  loop    loc_4EA0C  ; 循环写入
    
    ; 4EA17: bit7=1的分支
    4ea17  shl     cl, 1      ; 再左移，检查bit6
    4ea19  jb      short loc_4EA2C  ; 如果bit6=1，跳转到4EA2C
    
    ; bit7=1, bit6=0 → COPY标准
    4ea1b  shr     cl, 2
    4ea1e  inc     cl
    4ea20  sub     bx, cx
    4ea23  rep movsb          ; 从src复制count个字节
    
    ; 4EA2C: bit7=1, bit6=1 → SKIP
    4ea2c  shr     cl, 2
    4ea2f  inc     cl
    4ea31  add     edi, ecx   ; dst += count
    4ea33  sub     bx, cx
    
    所以正确的映射是：
    - bit7=0, bit6=0: FILL (读取1个值，填充count个位置)
    - bit7=0, bit6=1: COPY特殊 (读取1个值，循环写入count次)
    - bit7=1, bit6=0: COPY标准 (从src复制count个字节)
    - bit7=1, bit6=1: SKIP (跳过count个位置)
    """
    print("正确的RLE操作映射:")
    print("  bit7=0, bit6=0: FILL")
    print("  bit7=0, bit6=1: COPY特殊")
    print("  bit7=1, bit6=0: COPY标准")
    print("  bit7=1, bit6=1: SKIP")

if __name__ == "__main__":
    analyze_rle_logic()
