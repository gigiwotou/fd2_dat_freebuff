/*
 * 查找FDOTHER.DAT中的对话框背景图
 * 目标：找到310x86的图像资源
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>

static uint8_t* load_file(const char* filename, size_t* out_size)
{
    FILE* fp = fopen(filename, "rb");
    if (!fp) return NULL;
    fseek(fp, 0, SEEK_END);
    size_t size = ftell(fp);
    fseek(fp, 0, SEEK_SET);
    uint8_t* data = (uint8_t*)malloc(size);
    if (data) fread(data, 1, size, fp);
    fclose(fp);
    if (out_size) *out_size = size;
    return data;
}

static void hex_dump(const uint8_t* data, size_t len, const char* label)
{
    printf("=== %s (%zu bytes) ===\n", label, len);
    for (size_t i = 0; i < len && i < 64; i += 16) {
        printf("  %04zx: ", i);
        for (size_t j = 0; j < 16 && i+j < len; j++) {
            printf("%02X ", data[i+j]);
        }
        printf("\n");
    }
    if (len > 64) printf("  ... (%zu more bytes)\n", len - 64);
}

int main(void)
{
    const char* dat_path = "game/FDOTHER.DAT";
    size_t dat_size;
    uint8_t* dat = load_file(dat_path, &dat_size);
    if (!dat) {
        printf("无法加载 %s\n", dat_path);
        return 1;
    }

    printf("FDOTHER.DAT 文件大小: %zu 字节\n\n", dat_size);
    
    /* 解析DAT头部 */
    if (dat_size < 10) {
        printf("文件太小\n");
        free(dat);
        return 1;
    }

    /* 打印头部10字节 */
    printf("=== 头部 (10 bytes) ===\n");
    printf("  0000: ");
    for (int i = 0; i < 10; i++) {
        printf("%02X ", dat[i]);
    }
    printf("\n");

    /* 尝试WORD偏移表 */
    uint32_t count_word;
    memcpy(&count_word, dat + 8, 2);
    printf("\n尝试WORD偏移表: 数量=%d\n", count_word);
    
    if (count_word > 0 && count_word < 1000) {
        uint32_t offset_table_end = 10 + count_word * 2;
        printf("  偏移表结束位置: 0x%X\n", offset_table_end);
        
        if (offset_table_end <= dat_size) {
            /* 读取第一个偏移验证 */
            uint16_t first_off;
            memcpy(&first_off, dat + 10, 2);
            printf("  第一个偏移: 0x%04X\n", first_off);
            
            if (first_off >= 10 && first_off < dat_size) {
                printf("  WORD偏移表验证通过\n\n");
                
                printf("\n资源列表 (WORD偏移表):\n");
                for (uint32_t i = 0; i < count_word; i++) {
                    uint16_t off;
                    if (10 + i * 2 + 2 > dat_size) break;
                    memcpy(&off, dat + 10 + i * 2, 2);
                    
                    uint32_t next_off = dat_size;
                    if (i + 1 < count_word) {
                        memcpy(&next_off, dat + 10 + (i + 1) * 2, 2);
                    }
                    
                    if (off >= dat_size) {
                        printf("  资源 %3d: 偏移=0x%04X (超出范围，停止)\n", i, off);
                        break;
                    }
                    
                    if (next_off > dat_size) {
                        next_off = dat_size;
                    }
                    
                    uint32_t res_size = next_off - off;
                    
                    if (res_size > dat_size / 2 || res_size == 0 || res_size > 1000000) {
                        printf("  资源 %3d: 偏移=0x%04X, 大小=%6d (异常)\n", i, off, res_size);
                        continue;
                    }
                    
                    printf("  资源 %3d: 偏移=0x%04X, 大小=%6d 字节", i, off, res_size);
                    
                    if (res_size >= 8 && off + 4 <= dat_size) {
                        uint8_t* res = dat + off;
                        int16_t w, h;
                        memcpy(&w, res, 2);
                        memcpy(&h, res + 2, 2);
                        
                        if (w > 0 && w < 1000 && h > 0 && h < 1000) {
                            printf(" -> 尺寸=%dx%d", w, h);
                            
                            if (w == 310 && h == 86) {
                                printf(" *** 找到对话框背景图！ ***");
                            }
                        }
                    }
                    printf("\n");
                }
            }
        }
    }

    /* 尝试DWORD偏移表 */
    uint32_t count_dword;
    memcpy(&count_dword, dat + 6, 4);
    printf("\n尝试DWORD偏移表: 数量=%d\n", count_dword);
    
    if (count_dword > 0 && count_dword < 1000) {
        uint32_t offset_table_end = 10 + count_dword * 4;
        printf("  偏移表结束位置: 0x%X\n", offset_table_end);
        
        if (offset_table_end <= dat_size) {
            uint32_t first_off;
            memcpy(&first_off, dat + 10, 4);
            printf("  第一个偏移: 0x%08X\n", first_off);
            
            if (first_off >= 10 && first_off < dat_size) {
                printf("  DWORD偏移表验证通过\n\n");
                
                printf("\n资源列表 (DWORD偏移表):\n");
                for (uint32_t i = 0; i < count_dword; i++) {
                    uint32_t off;
                    if (10 + i * 4 + 4 > dat_size) break;
                    memcpy(&off, dat + 10 + i * 4, 4);
                    
                    uint32_t next_off = dat_size;
                    if (i + 1 < count_dword) {
                        memcpy(&next_off, dat + 10 + (i + 1) * 4, 4);
                    }
                    
                    if (off >= dat_size) {
                        printf("  资源 %3d: 偏移=0x%08X (超出范围，停止)\n", i, off);
                        break;
                    }
                    
                    if (next_off > dat_size) {
                        next_off = dat_size;
                    }
                    
                    uint32_t res_size = next_off - off;
                    
                    if (res_size > dat_size / 2 || res_size == 0 || res_size > 1000000) {
                        printf("  资源 %3d: 偏移=0x%08X, 大小=%6d (异常)\n", i, off, res_size);
                        continue;
                    }
                    
                    printf("  资源 %3d: 偏移=0x%08X, 大小=%6d 字节", i, off, res_size);
                    
                    if (res_size >= 8 && off + 4 <= dat_size) {
                        uint8_t* res = dat + off;
                        int16_t w, h;
                        memcpy(&w, res, 2);
                        memcpy(&h, res + 2, 2);
                        
                        if (w > 0 && w < 1000 && h > 0 && h < 1000) {
                            printf(" -> 尺寸=%dx%d", w, h);
                            
                            if (w == 310 && h == 86) {
                                printf(" *** 找到对话框背景图！ ***");
                            }
                        }
                    }
                    printf("\n");
                }
            }
        }
    }

    free(dat);
    return 0;
}
