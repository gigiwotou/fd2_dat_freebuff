#include <stdio.h>
#include <stdlib.h>
#include <string.h>
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
    
    /* Read resource count */
    uint32_t count;
    fseek(f, 6, SEEK_SET);
    fread(&count, 4, 1, f);
    
    /* Read all offsets */
    uint32_t* offsets = (uint32_t*)malloc(count * 4);
    fseek(f, 10, SEEK_SET);
    fread(offsets, 4, count, f);
    
    /* Get file size */
    fseek(f, 0, SEEK_END);
    long file_size = ftell(f);
    
    printf("Resource count: %u, file size: %ld\n\n", count, file_size);
    
    /* Check resources 65-80 to find the actual logo and scroll resources */
    for (int i = 65; i <= 80 && i < (int)count; i++) {
        uint32_t start = offsets[i];
        uint32_t end = (i + 1 < (int)count) ? offsets[i + 1] : (uint32_t)file_size;
        uint32_t size = end - start;
        
        if (size >= 4) {
            fseek(f, start, SEEK_SET);
            uint16_t w, h;
            fread(&w, 2, 1, f);
            fread(&h, 2, 1, f);
            printf("Resource %d: offset=0x%06X, size=%6u, %ux%u\n", i, start, size, w, h);
        } else {
            printf("Resource %d: offset=0x%06X, size=%6u\n", i, start, size);
        }
    }
    
    free(offsets);
    fclose(f);
    return 0;
}
