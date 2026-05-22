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
    
    /* 计算累计子文本数量，找到哪个资源包含索引514 */
    printf("\nCumulative sub-text counts:\n");
    int total = 0;
    int found_resource = -1;
    
    for (int i = 0; i < (int)count; i++) {
        dword off_s, off_e;
        memcpy(&off_s, fdtxt + 10 + i * 4, 4);
        if (i + 1 < (int)count)
            memcpy(&off_e, fdtxt + 10 + (i+1) * 4, 4);
        else
            off_e = (dword)fsize;
        
        if (off_s >= fsize) continue;
        
        int16_t sc;
        memcpy(&sc, fdtxt + off_s, 2);
        
        if (sc > 0 && sc < 2000) {
            int prev_total = total;
            total += sc;
            
            /* 检查514是否在这个资源的范围内 */
            if (found_resource < 0 && prev_total <= 514 && 514 < total) {
                found_resource = i;
                printf("  >>> Index 514 is in Resource %d (local index %d) <<<\n", 
                       i, 514 - prev_total);
            }
            
            if (sc >= 20) {
                printf("  Resource %d: sub-count=%d, cumulative=%d-%d\n", 
                       i, sc, prev_total, total-1);
            }
        }
    }
    
    printf("\nTotal sub-texts: %d\n", total);
    printf("Index 514 found in resource: %d\n", found_resource);
    
    /* 如果找到了，显示该资源的子文本514的内容 */
    if (found_resource >= 0) {
        /* 重新计算局部索引 */
        int local_idx = 0;
        int cum = 0;
        for (int i = 0; i <= found_resource; i++) {
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
                    if (i < found_resource) {
                        cum += sc;
                    } else {
                        local_idx = 514 - cum;
                    }
                }
            }
        }
        
        printf("\nResource %d, local sub-text index %d (global 514):\n", found_resource, local_idx);
        
        dword r_start, r_end;
        memcpy(&r_start, fdtxt + 10 + found_resource * 4, 4);
        memcpy(&r_end, fdtxt + 10 + (found_resource+1) * 4, 4);
        
        int16_t sc;
        memcpy(&sc, fdtxt + r_start, 2);
        
        if (local_idx < sc) {
            int16_t sub_off;
            memcpy(&sub_off, fdtxt + r_start + 2 + local_idx * 2, 2);
            printf("  Sub-text offset: %d\n", sub_off);
            
            int16_t* txt_ptr = (int16_t*)(fdtxt + r_start + 2 + sub_off * 2);
            printf("  Text content (first 30 words): ");
            for (int j = 0; j < 30 && txt_ptr[j] != -1; j++) {
                printf("%d ", txt_ptr[j]);
            }
            printf("\n");
        }
    }
    
    /* 同时检查549和550 */
    printf("\n\n=== Checking indices 549 and 550 ===\n");
    int targets[] = {549, 550};
    for (int t = 0; t < 2; t++) {
        int target_idx = targets[t];
        int resource = -1, local = 0;
        int current_cum = 0;
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
                    if (current_cum <= target_idx && target_idx < current_cum + sc) {
                        resource = i;
                        local = target_idx - current_cum;
                        break;
                    }
                    current_cum += sc;
                }
            }
        }
        printf("Index %d: Resource %d, local index %d\n", target_idx, resource, local);
    }
    
    free(fdtxt);
    return 0;
}
