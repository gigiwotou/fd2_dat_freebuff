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
    
    /* Read magic (6 bytes) */
    char magic[7] = {0};
    fread(magic, 1, 6, f);
    
    /* Read resource count (4 bytes at offset 6) */
    uint32_t count;
    fseek(f, 6, SEEK_SET);
    fread(&count, 4, 1, f);
    
    printf("Magic: %s\n", magic);
    printf("Resource count: %u\n\n", count);
    
    /* Read all offsets */
    uint32_t* offsets = (uint32_t*)malloc(count * 4);
    fseek(f, 10, SEEK_SET);
    fread(offsets, 4, count, f);
    
    /* Check resources 69-74 */
    for (int i = 69; i <= 74; i++) {
        if (i < (int)count) {
            uint32_t start = offsets[i];
            uint32_t end = (i + 1 < (int)count) ? offsets[i + 1] : 0;
            fseek(f, 0, SEEK_END);
            if (end == 0) end = ftell(f);
            uint32_t size = end - start;
            
            /* Read width/height header if size >= 4 */
            if (size >= 4) {
                fseek(f, start, SEEK_SET);
                uint16_t w, h;
                fread(&w, 2, 1, f);
                fread(&h, 2, 1, f);
                printf("Resource %d: offset=0x%X, size=%u, width=%u, height=%u\n", 
                       i, start, size, w, h);
            } else {
                printf("Resource %d: offset=0x%X, size=%u\n", i, start, size);
            }
        } else {
            printf("Resource %d: NOT FOUND (count=%u)\n", i, count);
        }
    }
    
    free(offsets);
    fclose(f);
    return 0;
}
