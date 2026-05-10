#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>

int main() {
    const char* filepath = "game/FDOTHER.DAT";
    FILE* fp = fopen(filepath, "rb");
    
    if (!fp) {
        printf("无法打开文件: %s\n", filepath);
        return 1;
    }
    
    fseek(fp, 0, SEEK_END);
    long file_size = ftell(fp);
    fseek(fp, 0, SEEK_SET);
    
    printf("================================================================================\n");
    printf("FDOTHER.DAT 文件分析\n");
    printf("================================================================================\n");
    printf("文件路径: %s\n", filepath);
    printf("文件大小: %ld 字节 (%.1f KB)\n\n", file_size, file_size / 1024.0);
    
    unsigned char* data = (unsigned char*)malloc(file_size);
    fread(data, 1, file_size, fp);
    fclose(fp);
    
    printf("文件头 (偏移0-5): ");
    for (int i = 0; i < 6; i++) printf("%02X ", data[i]);
    printf("\n");
    
    uint32_t resource_count = *(uint32_t*)(data + 6);
    printf("资源数量 (偏移6-9): %u\n\n", resource_count);
    
    uint32_t* offsets = (uint32_t*)calloc(resource_count, sizeof(uint32_t));
    for (uint32_t i = 0; i < resource_count; i++) {
        offsets[i] = *(uint32_t*)(data + 10 + i * 4);
    }
    
    printf("================================================================================\n");
    printf("前30个资源的偏移和大小\n");
    printf("================================================================================\n");
    printf("%-6s %-10s %-12s %-10s %-12s\n", "索引", "偏移", "偏移(hex)", "大小", "大小(hex)");
    printf("--------------------------------------------------------------------------------\n");
    
    for (int i = 0; i < 30 && i < resource_count; i++) {
        uint32_t size = (i + 1 < resource_count) ? offsets[i+1] - offsets[i] : file_size - offsets[i];
        printf("%-6d %-10u 0x%-10X %-10u 0x%-10X\n", i, offsets[i], offsets[i], size, size);
    }
    printf("\n");
    
    printf("================================================================================\n");
    printf("前30个资源的前4字节 (宽度x高度)\n");
    printf("================================================================================\n");
    printf("%-6s %-8s %-8s %-8s %-15s\n", "索引", "宽(LE)", "高(LE)", "宽(BE)", "高(BE)", "尺寸");
    printf("--------------------------------------------------------------------------------\n");
    
    for (int i = 0; i < 30 && i < resource_count; i++) {
        uint16_t w_le = *(uint16_t*)(data + offsets[i]);
        uint16_t h_le = *(uint16_t*)(data + offsets[i] + 2);
        uint16_t w_be = (data[offsets[i]] << 8) | data[offsets[i] + 1];
        uint16_t h_be = (data[offsets[i] + 2] << 8) | data[offsets[i] + 3];
        
        char size_info[50] = "";
        if (w_le <= 640 && h_le <= 480 && w_le > 0 && h_le > 0) {
            sprintf(size_info, "%ux%u(LE)", w_le, h_le);
        } else if (w_be <= 640 && h_be <= 480 && w_be > 0 && h_be > 0) {
            sprintf(size_info, "%ux%u(BE)", w_be, h_be);
        } else {
            sprintf(size_info, "%ux%u(LE)", w_le, h_le);
        }
        
        printf("%-6d %-8u %-8u %-8u %-8u %s\n", i, w_le, h_le, w_be, h_be, size_info);
    }
    printf("\n");
    
    printf("================================================================================\n");
    printf("重点关注资源: 索引 1,2,3,4,5,6,20\n");
    printf("================================================================================\n");
    
    int targets[] = {1, 2, 3, 4, 5, 6, 20};
    for (int t = 0; t < 7; t++) {
        int idx = targets[t];
        if (idx >= resource_count) continue;
        
        uint32_t size = (idx + 1 < resource_count) ? offsets[idx+1] - offsets[idx] : file_size - offsets[idx];
        
        printf("\n--- 资源索引 %d ---\n", idx);
        printf("文件偏移: %u (0x%08X)\n", offsets[idx], offsets[idx]);
        printf("资源大小: %u 字节 (0x%08X)\n", size, size);
        
        if (offsets[idx] + 16 <= file_size) {
            unsigned char* h = data + offsets[idx];
            printf("前16字节: ");
            for (int i = 0; i < 16; i++) printf("%02X ", h[i]);
            printf("\n");
            
            printf("16位LE宽高: %u x %u\n", *(uint16_t*)h, *(uint16_t*)(h+2));
            printf("32位LE值[0-3]: %u (0x%08X)\n", *(uint32_t*)h, *(uint32_t*)h);
        }
        
        printf("Hex Dump (前64字节):\n");
        for (uint32_t pos = offsets[idx]; pos < offsets[idx] + 64 && pos < file_size; pos += 16) {
            printf("  %04X: ", pos - offsets[idx]);
            for (int i = 0; i < 16 && pos + i < file_size; i++) printf("%02X ", data[pos + i]);
            printf(" ");
            for (int i = 0; i < 16 && pos + i < file_size; i++) {
                unsigned char c = data[pos + i];
                printf("%c", (c >= 32 && c < 127) ? c : '.');
            }
            printf("\n");
        }
    }
    
    printf("\n================================================================================\n");
    printf("统计信息\n");
    printf("================================================================================\n");
    printf("资源总数: %u\n", resource_count);
    
    uint32_t min_s = file_size, max_s = 0;
    uint64_t total_s = 0;
    for (uint32_t i = 0; i < resource_count; i++) {
        uint32_t s = (i + 1 < resource_count) ? offsets[i+1] - offsets[i] : file_size - offsets[i];
        if (s < min_s) min_s = s;
        if (s > max_s) max_s = s;
        total_s += s;
    }
    printf("最小: %u 字节\n", min_s);
    printf("最大: %u 字节\n", max_s);
    printf("平均: %.1f 字节\n", (double)total_s / resource_count);
    
    free(data);
    free(offsets);
    
    printf("\n分析完成\n");
    return 0;
}
