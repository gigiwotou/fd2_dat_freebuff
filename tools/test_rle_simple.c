/**
 * 测试RLE解码是否正确
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef unsigned char byte;
typedef unsigned short word;
typedef unsigned int dword;

/* RLE解码函数 - 与fd2_dat.c中的实现相同 */
int fd_decompress_rle(const byte *src, int src_size, byte *dst, int dst_width, int dst_height, int value_param) {
    int expected = dst_width * dst_height;
    int dst_idx = 0;
    int src_idx = 0;
    
    while (dst_idx < expected && src_idx < src_size) {
        byte ctrl = src[src_idx];
        src_idx++;
        
        int bit7 = (ctrl >> 7) & 1;
        int bit6 = (ctrl >> 6) & 1;
        int count = (ctrl & 0x3F) + 1;
        
        if (bit7 == 0) {
            if (bit6 == 0) {
                // FILL: 填充count个像素，值为下一个字节
                if (src_idx < src_size) {
                    byte fill_val = src[src_idx];
                    src_idx++;
                    if (value_param != -1) {
                        fill_val = (value_param + fill_val) & 0xFF;
                    }
                    for (int i = 0; i < count && dst_idx < expected; i++) {
                        dst[dst_idx] = fill_val;
                        dst_idx++;
                    }
                }
            } else {
                // SKIP: 跳过count个像素（填充0）
                dst_idx += count;
            }
        } else {
            if (bit6 == 0) {
                // COPY: 复制count个字节
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
                dst_idx += count;
            }
        }
    }
    
    return 0;
}

int main(int argc, char* argv[]) {
    /* 索引1的RLE数据（从调试脚本获取） */
    byte rle_data[] = {
        0x00, 0x56, 0x00, 0x00, 0x00, 0x33, 0x01, 0x00,
        0x00, 0x2e, 0x02, 0x00, 0x00, 0x1a, 0x03, 0x00,
        0x00, 0xac, 0x03, 0x00, 0x00, 0x37, 0x04, 0x00,
        0x00, 0x1e, 0x05, 0x00, 0x00, 0xa4, 0x05, 0x00,
        0x00, 0x25, 0x06, 0x00, 0x00, 0x8b, 0x06, 0x00,
        0x00, 0x12, 0x07, 0x00, 0x00, 0x72, 0x07, 0x00,
        0x00, 0xf9, 0x07, 0x00, 0x00, 0x3c, 0x08, 0x00,
        0x00, 0xc3, 0x08, 0x00, 0x00, 0x06, 0x09, 0x00,
        0x00, 0x8d, 0x09, 0x00, 0x00, 0xd0, 0x09, 0x00,
        0x00, 0x13, 0x0a, 0x00, 0x00, 0x56, 0x0a, 0x00
    };
    int rle_size = sizeof(rle_data);
    
    byte dst[576];  /* 24x24 */
    memset(dst, 0, sizeof(dst));
    
    int width = 24;
    int height = 24;
    int palette_window = 20;
    
    fd_decompress_rle(rle_data, rle_size, dst, width, height, palette_window);
    
    /* 显示解码结果 */
    printf("解码结果: 24x24\n");
    int non_zero = 0;
    for (int row = 0; row < height; row++) {
        for (int col = 0; col < width; col++) {
            int idx = row * width + col;
            byte val = dst[idx];
            if (val != 0) non_zero++;
            printf("%s", val == 0 ? "." : "#");
        }
        printf("\n");
    }
    
    printf("\n非零像素: %d / %d\n", non_zero, width * height);
    
    /* 显示前20个像素值 */
    printf("\n前20个像素值: ");
    for (int i = 0; i < 20; i++) {
        printf("%3d ", dst[i]);
    }
    printf("\n");
    
    return 0;
}
