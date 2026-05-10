#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>

typedef struct {
    uint32_t offset;
    uint32_t size;
} ResourceInfo;

int main() {
    const char* filepath = "game/FDOTHER.DAT";
    FILE* fp = fopen(filepath, "rb");
    
    if (!fp) {
        printf("无法打开文件: %s\n", filepath);
        return 1;
    }
    
    // 获取文件大小
    fseek(fp, 0, SEEK_END);
    long file_size = ftell(fp);
    fseek(fp, 0, SEEK_SET);
    
    printf("================================================================================\n");
    printf("FDOTHER.DAT 文件分析\n");
    printf("================================================================================\n");
    printf("文件路径: %s\n", filepath);
    printf("文件大小: %ld 字节 (%.1f KB)\n\n", file_size, file_size / 1024.0);
    
    // 读取整个文件
    unsigned char* data = (unsigned char*)malloc(file_size);
    if (!data) {
        printf("内存分配失败\n");
        fclose(fp);
        return 1;
    }
    
    fread(data, 1, file_size, fp);
    fclose(fp);
    
    // 解析文件头
    printf("文件头:\n");
    printf("  魔数 (偏移0-5): ");
    for (int i = 0; i < 6; i++) {
        printf("%02X ", data[i]);
    }
    printf("\n");
    
    uint32_t resource_count = *(uint32_t*)(data + 6);
    printf("  资源数量 (偏移6-9): %u\n\n", resource_count);
    
    // 解析偏移表
    uint32_t offset_table_start = 10;
    uint32_t data_start = offset_table_start + resource_count * 4;
    
    printf("偏移表起始: %u\n", offset_table_start);
    printf("数据区起始: %u\n\n", data_start);
    
    // 读取所有偏移
    ResourceInfo* resources = (ResourceInfo*)calloc(resource_count, sizeof(ResourceInfo));
    if (!resources) {
        printf("资源信息内存分配失败\n");
        free(data);
        return 1;
    }
    
    for (uint32_t i = 0; i < resource_count; i++) {
        uint32_t offset_pos = offset_table_start + i * 4;
        resources[i].offset = *(uint32_t*)(data + offset_pos);
        
        if (i + 1 < resource_count) {
            resources[i].size = resources[i+1].offset - resources[i].offset;
        } else {
            resources[i].size = file_size - resources[i].offset;
        }
    }
    
    // 打印前30个资源的偏移和大小
    printf("================================================================================\n");
    printf("前30个资源的偏移和大小\n");
    printf("================================================================================\n");
    printf("%-6s %-10s %-15s %-10s %-15s\n", "索引", "偏移", "偏移(十六进制)", "大小", "大小(十六进制)");
    printf("--------------------------------------------------------------------------------\n");
    
    for (int i = 0; i < 30 && i < resource_count; i++) {
        printf("%-6d %-10u 0x%-13X %-10u 0x%-13X\n", 
               i, resources[i].offset, resources[i].offset, 
               resources[i].size, resources[i].size);
    }
    
    if (resource_count > 30) {
        printf("... (共%u个资源)\n", resource_count);
    }
    printf("\n");
    
    // 读取每个资源的前4个字节（宽度和高度）
    printf("================================================================================\n");
    printf("每个资源的前4个字节（宽度x高度）\n");
    printf("================================================================================\n");
    printf("%-6s %-10s %-10s %-10s %-10s %-10s %-15s\n", "索引", "偏移", "宽度(LE)", "高度(LE)", "宽度(BE)", "高度(BE)", "疑似尺寸");
    printf("--------------------------------------------------------------------------------\n");
    
    for (int i = 0; i < 30 && i < resource_count; i++) {
        if (resources[i].offset + 4 > file_size) {
            printf("%-6d %-10u [超出范围]\n", i, resources[i].offset);
            continue;
        }
        
        unsigned char* ptr = data + resources[i].offset;
        uint16_t width_le = *(uint16_t*)(ptr);
        uint16_t height_le = *(uint16_t*)(ptr + 2);
        
        uint16_t width_be = (ptr[0] << 8) | ptr[1];
        uint16_t height_be = (ptr[2] << 8) | ptr[3];
        
        const char* size_str = "";
        char size_buf[50];
        
        if (width_le == 320 && height_le == 200) {
            size_str = "320x200 (LE)";
        } else if (width_le == 640 && height_le == 480) {
            size_str = "640x480 (LE)";
        } else if (width_be == 320 && height_be == 200) {
            size_str = "320x200 (BE)";
        } else if (width_be == 640 && height_be == 480) {
            size_str = "640x480 (BE)";
        } else {
            sprintf(size_buf, "%ux%u (LE)", width_le, height_le);
            size_str = size_buf;
        }
        
        printf("%-6d %-10u %-10u %-10u %-10u %-10u %-15s\n", 
               i, resources[i].offset, width_le, height_le, width_be, height_be, size_str);
    }
    printf("\n");
    
    // 重点关注索引 1,2,3,4,5,6,20 的资源
    printf("================================================================================\n");
    printf("重点关注资源: 索引 1,2,3,4,5,6,20\n");
    printf("================================================================================\n");
    
    int target_indices[] = {1, 2, 3, 4, 5, 6, 20};
    int target_count = sizeof(target_indices) / sizeof(target_indices[0]);
    
    for (int t = 0; t < target_count; t++) {
        int idx = target_indices[t];
        if (idx >= resource_count) {
            printf("\n--- 索引 %d: 超出范围 ---\n", idx);
            continue;
        }
        
        printf("\n============================================================\n");
        printf("资源索引 %d\n", idx);
        printf("============================================================\n");
        printf("文件偏移: %u (0x%08X)\n", resources[idx].offset, resources[idx].offset);
        printf("资源大小: %u 字节 (0x%08X)\n", resources[idx].size, resources[idx].size);
        
        if (resources[idx].offset + 16 <= file_size) {
            unsigned char* header = data + resources[idx].offset;
            printf("前16字节: ");
            for (int i = 0; i < 16; i++) {
                printf("%02X ", header[i]);
            }
            printf("\n");
            
            uint16_t w16_le = *(uint16_t*)(header);
            uint16_t h16_le = *(uint16_t*)(header + 2);
            printf("16位LE宽高: %u x %u\n", w16_le, h16_le);
            
            uint16_t w16_be = (header[0] << 8) | header[1];
            uint16_t h16_be = (header[2] << 8) | header[3];
            printf("16位BE宽高: %u x %u\n", w16_be, h16_be);
            
            uint32_t val32_0 = *(uint32_t*)(header);
            uint32_t val32_4 = *(uint32_t*)(header + 4);
            uint32_t val32_8 = *(uint32_t*)(header + 8);
            uint32_t val32_12 = *(uint32_t*)(header + 12);
            printf("32位LE值[0-3]: %u (0x%08X)\n", val32_0, val32_0);
            printf("32位LE值[4-7]: %u (0x%08X)\n", val32_4, val32_4);
            printf("32位LE值[8-11]: %u (0x%08X)\n", val32_8, val32_8);
            printf("32位LE值[12-15]: %u (0x%08X)\n", val32_12, val32_12);
        }
        
        printf("\n前128字节 Hex Dump:\n");
        uint32_t dump_end = resources[idx].offset + 128;
        if (dump_end > file_size) dump_end = file_size;
        
        for (uint32_t pos = resources[idx].offset; pos < dump_end; pos += 16) {
            printf("  %04X: ", pos - resources[idx].offset);
            
            // Hex部分
            for (int i = 0; i < 16; i++) {
                if (pos + i < file_size) {
                    printf("%02X ", data[pos + i]);
                } else {
                    printf("   ");
                }
            }
            
            printf(" ");
            
            // ASCII部分
            for (int i = 0; i < 16; i++) {
                if (pos + i < file_size) {
                    unsigned char c = data[pos + i];
                    if (c >= 32 && c < 127) {
                        printf("%c", c);
                    } else {
                        printf(".");
                    }
                }
            }
            printf("\n");
        }
        printf("\n");
    }
    
    // 文件统计信息
    printf("================================================================================\n");
    printf("文件统计信息\n");
    printf("================================================================================\n");
    
    if (resource_count > 0) {
        uint32_t last_resource_size = file_size - resources[resource_count - 1].offset;
        
        printf("资源数量: %u\n", resource_count);
        
        uint32_t min_size = resources[0].size;
        uint32_t max_size = resources[0].size;
        uint64_t total_size = 0;
        
        for (uint32_t i = 0; i < resource_count; i++) {
            if (resources[i].size < min_size) min_size = resources[i].size;
            if (resources[i].size > max_size) max_size = resources[i].size;
            total_size += resources[i].size;
        }
        
        printf("最小资源大小: %u 字节\n", min_size);
        printf("最大资源大小: %u 字节\n", max_size);
        printf("平均资源大小: %.1f 字节\n", (double)total_size / resource_count);
        printf("总数据大小: %lu 字节\n", total_size);
    }
    
    printf("\n分析完成\n");
    
    free(data);
    free(resources);
    
    return 0;
}
