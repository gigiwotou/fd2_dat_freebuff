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
    
    /* Scan all resources for sub-text count info */
    printf("\nResources with sub-text count >= 30:\n");
    for (int i = 0; i < count; i++) {
        dword off_s = 0, off_e = 0;
        memcpy(&off_s, fdtxt + 10 + i * 4, 4);
        if (i + 1 < count) memcpy(&off_e, fdtxt + 10 + (i+1) * 4, 4);
        else off_e = (dword)fsize;
        
        if (off_s < fsize && (off_e - off_s) >= 2) {
            if (off_e - off_s >= 10 && memcmp(fdtxt + off_s, "LLLLLL", 6) == 0) {
                dword nc;
                memcpy(&nc, fdtxt + off_s + 6, 4);
                if (nc >= 30) {
                    printf("  Resource %d: nested DAT, sub-count=%u, size=%u\n", i, nc, off_e-off_s);
                }
            } else {
                int16_t c;
                memcpy(&c, fdtxt + off_s, 2);
                if (c >= 30 && c < 2000) {
                    printf("  Resource %d: sub-count=%d, size=%u\n", i, c, off_e-off_s);
                }
            }
        }
    }
    
    /* Also check resource 30 specifically (has 92 sub-texts) */
    printf("\nResource 30 details (has many sub-texts):\n");
    int i = 30;
    dword off_s = 0, off_e = 0;
    memcpy(&off_s, fdtxt + 10 + i * 4, 4);
    memcpy(&off_e, fdtxt + 10 + (i+1) * 4, 4);
    printf("  Offset: 0x%x - 0x%x, size=%u\n", off_s, off_e, off_e-off_s);
    
    int16_t c;
    memcpy(&c, fdtxt + off_s, 2);
    printf("  Sub-text count: %d\n", c);
    
    /* Show first few sub-texts content */
    printf("  First 5 sub-texts:\n");
    for (int j = 0; j < 5 && j < c; j++) {
        int16_t sub_off;
        memcpy(&sub_off, fdtxt + off_s + 2 + j * 2, 2);
        int16_t* txt_ptr = (int16_t*)(fdtxt + off_s + 2 + sub_off * 2);
        printf("    Sub %d: ", j);
        /* Print first 20 words */
        for (int k = 0; k < 20 && txt_ptr[k] >= 0 && txt_ptr[k] > 0x20; k++) {
            printf("%04x ", txt_ptr[k]);
        }
        printf("\n");
    }
    
    free(fdtxt);
    return 0;
}
