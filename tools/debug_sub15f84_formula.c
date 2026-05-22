#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>

typedef unsigned char u8;
typedef unsigned int dword;

int main() {
    FILE* fp = fopen("game/FDTXT.DAT", "rb");
    if (!fp) { printf("Cannot open FDTXT.DAT\n"); return 1; }
    
    fseek(fp, 0, SEEK_END);
    size_t fsize = ftell(fp);
    fseek(fp, 0, SEEK_SET);
    
    u8* fdtxt = (u8*)malloc(fsize);
    fread(fdtxt, 1, fsize, fp);
    fclose(fp);
    
    /* 资源0的数据指针 */
    dword r0_start;
    memcpy(&r0_start, fdtxt + 10, 4);
    u8* arg0 = fdtxt + r0_start;
    
    printf("Resource 0 file offset: 0x%x\n", r0_start);
    printf("arg0 (resource 0 pointer): %p\n\n", (void*)arg0);
    
    /* 按照sub_15F84的公式计算索引514的文本数据 */
    /* v15 = (int16*)(*(int16*)(arg0 + 2*arg4) + arg0) */
    
    int arg4 = 514;
    u8* pos = arg0 + 2 * arg4;  /* arg0 + 1028 */
    
    printf("Position for index 514:\n");
    printf("  arg0 + 2*514 = %p (file offset 0x%zx)\n", 
           (void*)pos, (size_t)(pos - fdtxt));
    
    /* 读取该位置的值 */
    int16_t offset_val;
    memcpy(&offset_val, pos, 2);
    printf("  Value at this position: %d (0x%04x)\n", offset_val, offset_val);
    
    /* 计算文本数据指针 */
    int16_t* v15 = (int16_t*)(offset_val + arg0);
    printf("  Text data pointer: %p (file offset 0x%zx)\n\n", 
           (void*)v15, (size_t)(v15 - (int16_t*)fdtxt) * 2);
    
    /* 显示文本内容 */
    printf("Text content (字形索引):\n");
    for (int i = 0; i < 40 && v15[i] != -1; i++) {
        printf("%d ", v15[i]);
    }
    printf("\n\n");
    
    /* 同样计算索引515 */
    arg4 = 515;
    pos = arg0 + 2 * arg4;
    memcpy(&offset_val, pos, 2);
    v15 = (int16_t*)(offset_val + arg0);
    printf("Index 515 text:\n");
    for (int i = 0; i < 30 && v15[i] != -1; i++) {
        printf("%d ", v15[i]);
    }
    printf("\n\n");
    
    /* 测试场景索引162 (slot 1的场景) */
    arg4 = 514 + 162;  /* = 676 */
    pos = arg0 + 2 * arg4;
    printf("Index %d (514+162):\n", arg4);
    printf("  Position: %p\n", (void*)pos);
    
    if ((size_t)(pos - fdtxt) + 2 < fsize) {
        memcpy(&offset_val, pos, 2);
        printf("  Value: %d\n", offset_val);
        
        v15 = (int16_t*)(offset_val + arg0);
        printf("  Text: ");
        for (int i = 0; i < 30 && v15[i] != -1; i++) {
            printf("%d ", v15[i]);
        }
        printf("\n");
    } else {
        printf("  OUT OF RANGE!\n");
    }
    
    free(fdtxt);
    return 0;
}
