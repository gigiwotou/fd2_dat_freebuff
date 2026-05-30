/**
 * 测试RLE解码是否正确 - C版本
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef unsigned char byte;
typedef unsigned short word;
typedef unsigned int dword;

/* RLE解码函数 - 与fd2_dat.c中的实现完全相同 */
int fd_decompress_rle(const byte *src, int src_size, byte *dst, int dst_width, int dst_height, int value_param) {
    int expected = dst_width * dst_height;
    int dst_idx = 0;
    int src_idx = 0;
    
    printf("RLE解码开始: src_size=%d, dst_width=%d, dst_height=%d, value_param=%d\n", 
           src_size, dst_width, dst_height, value_param);
    
    while (dst_idx < expected && src_idx < src_size) {
        byte ctrl = src[src_idx];
        src_idx++;
        
        int bit7 = (ctrl >> 7) & 1;
        int bit6 = (ctrl >> 6) & 1;
        int count = (ctrl & 0x3F) + 1;
        
        printf("  控制字节: 0x%02x, bit7=%d, bit6=%d, count=%d, src_idx=%d, dst_idx=%d\n", 
               ctrl, bit7, bit6, count, src_idx, dst_idx);
        
        if (bit7 == 0) {
            if (bit6 == 0) {
                // FILL: 填充count个像素，值为下一个字节
                if (src_idx < src_size) {
                    byte fill_val = src[src_idx];
                    src_idx++;
                    if (value_param != -1) {
                        fill_val = (value_param + fill_val) & 0xFF;
                    }
                    printf("    FILL: count=%d, fill_val=0x%02x\n", count, fill_val);
                    for (int i = 0; i < count && dst_idx < expected; i++) {
                        dst[dst_idx] = fill_val;
                        dst_idx++;
                    }
                }
            } else {
                // SKIP: 跳过count个像素（填充0）
                printf("    SKIP: count=%d\n", count);
                dst_idx += count;
            }
        } else {
            if (bit6 == 0) {
                // COPY: 复制count个字节
                printf("    COPY: count=%d\n", count);
                for (int i = 0; i < count && dst_idx < expected && src_idx < src_size; i++) {
                    byte val = src[src_idx];
                    src_idx++;
                    if (value_param != -1) {
                        val = (value_param + val) & 0xFF;
                    }
                    dst[dst_idx] = val;
                    dst_idx++;
                }
            } else {
                // SKIP: 跳过count个像素
                printf("    SKIP: count=%d\n", count);
                dst_idx += count;
            }
        }
    }
    
    printf("RLE解码完成: dst_idx=%d, expected=%d\n", dst_idx, expected);
    return 0;
}

int main(int argc, char* argv[]) {
    /* 索引1的RLE数据（从游戏文件提取） */
    /* 这里需要实际从FDOTHER.DAT中提取索引1的RLE数据 */
    /* 暂时用Python分析得到的数据 */
    
    FILE* fp = fopen("game/FDOTHER.DAT", "rb");
    if (!fp) {
        printf("无法打开FDOTHER.DAT\n");
        return 1;
    }
    
    /* 读取偏移表 */
    fseek(fp, 6, SEEK_SET);
    dword offsets[103];
    for (int i = 0; i < 103; i++) {
        fread(&offsets[i], 4, 1, fp);
    }
    
    /* 读取索引1数据 */
    dword idx1_start = offsets[1];
    dword idx1_end = offsets[2];
    dword idx1_size = idx1_end - idx1_start;
    
    printf("索引1: 偏移 %u - %u, 大小 %u\n", idx1_start, idx1_end, idx1_size);
    
    byte* idx1_data = (byte*)malloc(idx1_size);
    fseek(fp, idx1_start, SEEK_SET);
    fread(idx1_data, 1, idx1_size, fp);
    fclose(fp);
    
    /* 解析头 */
    word w = idx1_data[0] | (idx1_data[1] << 8);
    word h = idx1_data[2] | (idx1_data[3] << 8);
    byte byte5 = idx1_data[5];
    
    printf("宽度: %u, 高度: %u, 字节5: 0x%02x\n", w, h, byte5);
    
    int header_size;
    word palette_window;
    const byte* rle_data;
    int rle_size;
    
    if (byte5 != 0) {
        header_size = 8;
        palette_window = idx1_data[4] | (idx1_data[5] << 8);
        rle_data = idx1_data + 8;
        rle_size = idx1_size - 8;
    } else {
        header_size = 5;
        palette_window = idx1_data[4];
        rle_data = idx1_data + 5;
        rle_size = idx1_size - 5;
    }
    
    printf("头大小: %d, 调色板窗口: %u, RLE大小: %d\n", header_size, palette_window, rle_size);
    printf("RLE前16字节: ");
    for (int i = 0; i < 16 && i < rle_size; i++) {
        printf("%02x ", rle_data[i]);
    }
    printf("\n");
    
    /* 解码 */
    int expected = w * h;
    byte* dst = (byte*)malloc(expected);
    memset(dst, 0, expected);
    
    fd_decompress_rle(rle_data, rle_size, dst, w, h, -1);  /* 不应用调色板窗口 */
    
    /* 显示结果 */
    printf("\n解码结果: %dx%d\n", w, h);
    int non_zero = 0;
    for (int row = 0; row < h; row++) {
        for (int col = 0; col < w; col++) {
            int idx = row * w + col;
            byte val = dst[idx];
            if (val != 0) non_zero++;
            printf("%s", val == 0 ? "." : "#");
        }
        printf("\n");
    }
    
    printf("\n非零像素: %d / %d\n", non_zero, w * h);
    
    /* 应用调色板窗口后显示 */
    printf("\n应用调色板窗口(%d)后:\n", palette_window);
    for (int row = 0; row < h; row++) {
        for (int col = 0; col < w; col++) {
            int idx = row * w + col;
            byte val = dst[idx];
            int adjusted = (palette_window + val) & 0xFF;
            if (val == 0) {
                printf(".");
            } else {
                printf("%02x", adjusted);
            }
        }
        printf("\n");
    }
    
    free(dst);
    free(idx1_data);
    
    return 0;
}
