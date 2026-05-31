/* sub_4EBFF: 渲染像素数据到屏幕缓冲区（包含RLE解码） */
/* 根据IDA Pro MCP反编译代码1:1实现 */
/* void __cdecl sub_4EBFF(_BYTE *a1, __int16 *a2, int a3) */
/* 参数: dst=目标缓冲区, src=源数据(包含4字节宽高头), pitch=行间距 */
void sub_4EBFF(byte* dst, byte* src, int pitch) {
    /* 4ec0c  lodsw        ; 从src读取width (ESI+=2) */
    /* 4ec0e  mov  bp, ax  ; BP = width */
    /* 4ec11  lodsw        ; 从src读取height (ESI+=2) */
    /* 4ec13  mov  dx, ax  ; DX = height */
    word width = src[0] | (src[1] << 8);
    word height = src[2] | (src[3] << 8);
    
    /* 像素数据从偏移4开始 (ESI已经前进了4字节) */
    byte* pixel_data = src + 4;
    
    /* 4ec16  xor  ecx, ecx ; ECX = 0 */
    /* 4ec18  xor  ax, ax   ; AX = 0 */
    /* sub_4EC66状态变量 */
    byte ah = 0;        /* EC66运行长度计数器 */
    byte prev_al = 0;   /* EC66上次读取的像素值 */
    int src_idx = 0;
    
    /* 外层循环: DX = height行 */
    /* 4ec1b  push edi     ; 保存行起始 */
    for (int y = 0; y < height; y++) {
        byte* row_start = dst;  /* push edi - 保存行起始位置 */
        
        /* 4ec1c  mov  cx, bp  ; CX = width */
        /* 内层循环: CX = width次 */
        for (int x = 0; x < width; x++) {
            /* 4ec1f  call sub_4EC66 ; 获取像素值 */
            if (ah > 0) {
                /* EC66: 4ec66 or ah, ah; jz loc_4EC6D; dec ah; retn */
                ah--;
            } else {
                /* EC66: 4ec6d lodsb; cmp al, 0C0h; ja loc_4EC75 */
                byte al = pixel_data[src_idx++];
                
                if (al > 0xC0) {
                    /* EC66: 4ec75 mov ah, al; sub ah, 0C1h; lodsb; retn */
                    ah = al - 0xC1;
                    al = pixel_data[src_idx++];
                    prev_al = al;
                } else {
                    /* EC66: 4ec72 xor ah, ah; retn */
                    ah = 0;
                    prev_al = al;
                }
            }
            /* 4ec24  stosb        ; 存储到dst[EDI], EDI++ */
            *dst++ = prev_al;
        }
        
        /* 4ec27  pop edi      ; 恢复行起始 */
        /* 4ec28  add  edi, ebx ; EDI += pitch */
        dst = row_start + pitch;
    }
}