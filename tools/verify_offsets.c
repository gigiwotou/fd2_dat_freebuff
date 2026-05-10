#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

int main() {
    FILE* f = fopen("d:\\workspace\\fd2_dat_freebuff\\game\\FDOTHER.DAT", "rb");
    if (!f) {
        printf("Cannot open FDOTHER.DAT\n");
        return 1;
    }
    
    fseek(f, 0, SEEK_END);
    long file_size = ftell(f);
    fseek(f, 0, SEEK_SET);
    
    printf("File size: %ld bytes\n", file_size);
    
    // 读取整个文件
    uint8_t* data = (uint8_t*)malloc(file_size);
    fread(data, 1, file_size, f);
    fclose(f);
    
    // 检查文件头
    printf("Magic (0-5): ");
    for (int i = 0; i < 6; i++) printf("%02X ", data[i]);
    printf("\n");
    
    // 从偏移6开始解析偏移表
    printf("\nOffset table (from offset 6):\n");
    
    int count = 0;
    uint32_t offsets[500];
    
    for (int i = 0; i < 500; i++) {
        uint32_t offset;
        memcpy(&offset, data + 6 + i * 4, 4);
        
        if (offset >= (uint32_t)file_size) {
            count = i;
            printf("[%d] offset=%u (0x%X) - exceeds file size, stopping\n", i, offset, offset);
            break;
        }
        offsets[i] = offset;
    }
    
    printf("\nTotal resources: %d\n\n", count);
    
    // 检查前30个资源
    for (int i = 0; i < 30 && i < count; i++) {
        uint32_t start = offsets[i];
        uint32_t end = (i + 1 < count) ? offsets[i + 1] : (uint32_t)file_size;
        uint32_t size = end - start;
        
        uint16_t w, h;
        memcpy(&w, data + start, 2);
        memcpy(&h, data + start + 2, 2);
        
        if (w > 0 && w <= 640 && h > 0 && h <= 480) {
            printf("[%2d] start=%7u, size=%6u, dims=%ux%u [IMAGE]\n", i, start, size, w, h);
        } else {
            printf("[%2d] start=%7u, size=%6u, header=%02X %02X %02X %02X [OTHER]\n", 
                   i, start, size, data[start], data[start+1], data[start+2], data[start+3]);
        }
    }
    
    // 重点检查1,2,3,4,5,6,20
    printf("\n=== Key resources ===\n");
    int indices[] = {1, 2, 3, 4, 5, 6, 20};
    for (int j = 0; j < 7; j++) {
        int i = indices[j];
        if (i < count) {
            uint32_t start = offsets[i];
            uint32_t end = (i + 1 < count) ? offsets[i + 1] : (uint32_t)file_size;
            uint32_t size = end - start;
            
            uint16_t w, h;
            memcpy(&w, data + start, 2);
            memcpy(&h, data + start + 2, 2);
            
            printf("Index %d: start=%u, size=%u, w=%u, h=%u\n", i, start, size, w, h);
        }
    }
    
    free(data);
    return 0;
}
