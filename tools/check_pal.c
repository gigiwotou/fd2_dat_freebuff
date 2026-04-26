#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>

int main(int argc, char** argv) {
    if (argc < 2) {
        fprintf(stderr, "Usage: %s <fdother.dat>\n", argv[0]);
        return 1;
    }
    
    FILE* f = fopen(argv[1], "rb");
    if (!f) {
        fprintf(stderr, "Cannot open %s\n", argv[1]);
        return 1;
    }
    
    uint32_t count;
    fseek(f, 6, SEEK_SET);
    fread(&count, 4, 1, f);
    
    uint32_t* offsets = (uint32_t*)malloc(count * 4);
    fseek(f, 10, SEEK_SET);
    fread(offsets, 4, count, f);
    
    fseek(f, 0, SEEK_END);
    long file_size = ftell(f);
    
    printf("Resource count: %u, file size: %ld\n\n", count, file_size);
    
    for (int i = 100; i <= 102 && i < (int)count; i++) {
        uint32_t start = offsets[i];
        uint32_t end = (i + 1 < (int)count) ? offsets[i + 1] : (uint32_t)file_size;
        uint32_t size = end - start;
        
        printf("Resource %d: offset=0x%06X, size=%6u", i, start, size);
        
        if (size >= 4) {
            fseek(f, start, SEEK_SET);
            uint16_t w, h;
            fread(&w, 2, 1, f);
            fread(&h, 2, 1, f);
            printf(", %ux%u", w, h);
            
            if (size == 768) {
                printf(" (PALETTE - 256 colors * 3 bytes)");
            }
        }
        printf("\n");
    }
    
    free(offsets);
    fclose(f);
    return 0;
}
