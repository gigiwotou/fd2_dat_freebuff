#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>

typedef unsigned char u8;
typedef unsigned int dword;

void print_char_pattern(u8* char_data) {
    for (int row = 0; row < 16; row++) {
        uint16_t bits;
        memcpy(&bits, char_data + row * 2, 2);
        bits = ((bits & 0xFF) << 8) | ((bits >> 8) & 0xFF);
        
        for (int col = 0; col < 16; col++) {
            printf("%c", (bits & (1 << (15 - col))) ? '#' : '.');
        }
        printf("\n");
    }
}

int main() {
    FILE* fp = fopen("game/FDOTHER.DAT", "rb");
    if (!fp) { printf("Cannot open FDOTHER.DAT\n"); return 1; }
    
    fseek(fp, 0, SEEK_END);
    size_t fsize = ftell(fp);
    fseek(fp, 0, SEEK_SET);
    
    u8* data = (u8*)malloc(fsize);
    fread(data, 1, fsize, fp);
    fclose(fp);
    
    printf("FDOTHER.DAT size: %zu\n", fsize);
    printf("Magic: %.*s\n", 6, data);
    
    dword count;
    memcpy(&count, data + 6, 4);
    printf("Resource count: %u\n", count);
    
    /* 获取资源3的偏移 */
    dword off3_start, off3_end;
    memcpy(&off3_start, data + 10 + 3 * 4, 4);
    memcpy(&off3_end, data + 10 + 4 * 4, 4);
    printf("\nResource 3 (font): offset 0x%x - 0x%x, size=%u\n", off3_start, off3_end, off3_end - off3_start);
    
    dword font_size = off3_end - off3_start;
    int char_count = font_size / 32;
    printf("Font characters: %d\n", char_count);
    
    /* 显示索引514的字符图案 */
    printf("\nCharacter at index 514:\n");
    if (514 < char_count) {
        u8* char_data = data + off3_start + 514 * 32;
        print_char_pattern(char_data);
    } else {
        printf("Index 514 out of range!\n");
    }
    
    /* 显示索引515的字符图案 */
    printf("\nCharacter at index 515:\n");
    if (515 < char_count) {
        u8* char_data = data + off3_start + 515 * 32;
        print_char_pattern(char_data);
    }
    
    /* 检查FDTXT.DAT中资源30的前几个子文本 */
    printf("\n\n=== FDTXT.DAT Resource 30 analysis ===\n");
    FILE* fdtxt_fp = fopen("game/FDTXT.DAT", "rb");
    if (fdtxt_fp) {
        fseek(fdtxt_fp, 0, SEEK_END);
        size_t fdtxt_size = ftell(fdtxt_fp);
        fseek(fdtxt_fp, 0, SEEK_SET);
        
        u8* fdtxt = (u8*)malloc(fdtxt_size);
        fread(fdtxt, 1, fdtxt_size, fdtxt_fp);
        fclose(fdtxt_fp);
        
        dword fdtxt_count;
        memcpy(&fdtxt_count, fdtxt + 6, 4);
        printf("FDTXT resource count: %u\n", fdtxt_count);
        
        /* 资源30的偏移 */
        dword r30_start, r30_end;
        memcpy(&r30_start, fdtxt + 10 + 30 * 4, 4);
        memcpy(&r30_end, fdtxt + 10 + 31 * 4, 4);
        printf("Resource 30: offset 0x%x - 0x%x, size=%u\n", r30_start, r30_end, r30_end - r30_start);
        
        int16_t sub_count;
        memcpy(&sub_count, fdtxt + r30_start, 2);
        printf("Sub-text count: %d\n", sub_count);
        
        /* 显示前10个子文本的字形索引 */
        printf("\nFirst 10 sub-texts word indices:\n");
        for (int i = 0; i < 10 && i < sub_count; i++) {
            int16_t sub_off;
            memcpy(&sub_off, fdtxt + r30_start + 2 + i * 2, 2);
            printf("  Sub %d (offset %d): ", i, sub_off);
            
            int16_t* txt_ptr = (int16_t*)(fdtxt + r30_start + 2 + sub_off * 2);
            /* 打印前30个词 */
            for (int j = 0; j < 30 && txt_ptr[j] != -1; j++) {
                if (txt_ptr[j] < 0) {
                    printf("[%d] ", txt_ptr[j]);
                } else {
                    printf("%d ", txt_ptr[j]);
                }
            }
            printf("\n");
        }
        
        free(fdtxt);
    }
    
    free(data);
    return 0;
}
