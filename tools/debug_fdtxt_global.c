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
    
    printf("FDTXT.DAT size: %zu\n", fsize);
    
    dword count;
    memcpy(&count, fdtxt + 6, 4);
    printf("Resource count: %u\n", count);
    
    /* 构建全局子文本索引表 */
    printf("\nBuilding global sub-text index table...\n");
    
    /* 存储每个资源的信息 */
    typedef struct {
        dword file_off;
        int16_t sub_count;
        int global_start;  /* 该资源的全局起始索引 */
    } res_info_t;
    
    res_info_t* res_info = (res_info_t*)calloc(count, sizeof(res_info_t));
    int global_idx = 0;
    
    for (int i = 0; i < (int)count; i++) {
        dword off_s, off_e;
        memcpy(&off_s, fdtxt + 10 + i * 4, 4);
        if (i + 1 < (int)count)
            memcpy(&off_e, fdtxt + 10 + (i+1) * 4, 4);
        else
            off_e = (dword)fsize;
        
        if (off_s < fsize) {
            int16_t sc;
            memcpy(&sc, fdtxt + off_s, 2);
            if (sc > 0 && sc < 2000) {
                res_info[i].file_off = off_s;
                res_info[i].sub_count = sc;
                res_info[i].global_start = global_idx;
                global_idx += sc;
            }
        }
    }
    
    printf("Total global sub-texts: %d\n", global_idx);
    
    /* 查找全局索引514, 515, 516, 549, 550 */
    int targets[] = {514, 515, 516, 549, 550, 551, 552};
    
    for (int t = 0; t < 7; t++) {
        int idx = targets[t];
        if (idx >= global_idx) {
            printf("\nGlobal index %d: OUT OF RANGE (max=%d)\n", idx, global_idx-1);
            continue;
        }
        
        /* 找到对应的资源 */
        int res = -1, local = 0;
        for (int i = 0; i < (int)count; i++) {
            if (res_info[i].sub_count > 0) {
                if (idx >= res_info[i].global_start && 
                    idx < res_info[i].global_start + res_info[i].sub_count) {
                    res = i;
                    local = idx - res_info[i].global_start;
                    break;
                }
            }
        }
        
        printf("\nGlobal index %d: Resource %d, local index %d\n", idx, res, local);
        
        if (res >= 0) {
            dword r_start = res_info[res].file_off;
            int16_t sc = res_info[res].sub_count;
            
            if (local < sc) {
                int16_t sub_off;
                memcpy(&sub_off, fdtxt + r_start + 2 + local * 2, 2);
                
                int16_t* txt_ptr = (int16_t*)(fdtxt + r_start + 2 + sub_off * 2);
                printf("  Text content: ");
                for (int j = 0; j < 40 && txt_ptr[j] != -1; j++) {
                    int16_t w = txt_ptr[j];
                    if (w < 0) {
                        printf("[%d] ", w);
                    } else {
                        printf("%d ", w);
                    }
                }
                printf("\n");
            }
        }
    }
    
    free(res_info);
    free(fdtxt);
    return 0;
}
