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
    printf("Magic: %.*s\n", 6, fdtxt);
    
    dword count;
    memcpy(&count, fdtxt + 6, 4);
    printf("Resource count: %u\n", count);
    
    /* Scan all resources */
    for (int i = 0; i < count; i++) {
        dword off_s = 0, off_e = 0;
        memcpy(&off_s, fdtxt + 10 + i * 4, 4);
        if (i + 1 < count) memcpy(&off_e, fdtxt + 10 + (i+1) * 4, 4);
        else off_e = (dword)fsize;
        
        if (off_s >= fsize) continue;
        
        /* Check for nested DAT magic */
        if (off_e - off_s >= 10 && memcmp(fdtxt + off_s, "LLLLLL", 6) == 0) {
            dword nc;
            memcpy(&nc, fdtxt + off_s + 6, 4);
            printf("  Resource %d: nested DAT, sub-count=%u, size=%u\n", i, nc, off_e-off_s);
        } else {
            int16_t c;
            memcpy(&c, fdtxt + off_s, 2);
            if (c > 0 && c < 2000) {
                printf("  Resource %d: sub-count=%d, size=%u\n", i, c, off_e-off_s);
            }
        }
    }
    
    free(fdtxt);
    return 0;
}
