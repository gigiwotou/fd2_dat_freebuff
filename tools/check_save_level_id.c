#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>

typedef unsigned char u8;

/* 查看存档文件中的关卡ID */
int main() {
    /* 检查output目录下的存档文件 */
    for (int i = 0; i < 4; i++) {
        char filename[256];
        snprintf(filename, sizeof(filename), "output/save%d.dat", i);
        
        FILE* fp = fopen(filename, "rb");
        if (!fp) {
            printf("存档%d: 不存在\n", i);
            continue;
        }
        
        fseek(fp, 0, SEEK_END);
        size_t fsize = ftell(fp);
        fseek(fp, 0, SEEK_SET);
        
        u8* data = (u8*)malloc(fsize);
        fread(data, 1, fsize, fp);
        fclose(fp);
        
        printf("存档%d: 大小=%zu\n", i, fsize);
        
        /* 检查偏移2560处的字节（关卡ID） */
        if (fsize > 2560) {
            u8 level_id = data[2560];
            printf("  关卡ID (偏移2560): %d\n", level_id);
            printf("  FDTXT索引: %d (514+关卡ID)\n", 514 + level_id);
            printf("  子场景索引: %d (550+关卡ID)\n", 550 + level_id);
        }
        
        /* 打印前100字节 */
        printf("  前100字节: ");
        for (int j = 0; j < 100 && j < (int)fsize; j++) {
            printf("%02x ", data[j]);
        }
        printf("\n\n");
        
        free(data);
    }
    
    return 0;
}
