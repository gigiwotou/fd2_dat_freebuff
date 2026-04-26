#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>

typedef struct {
    uint32_t start;
    uint32_t size;
} resource_t;

int main(int argc, char** argv) {
    if (argc < 2) {
        fprintf(stderr, "Usage: %s <FDOTHER.DAT>\n", argv[0]);
        return 1;
    }

    FILE* f = fopen(argv[1], "rb");
    if (!f) {
        fprintf(stderr, "Cannot open %s\n", argv[1]);
        return 1;
    }

    fseek(f, 0, SEEK_END);
    long file_size = ftell(f);
    fseek(f, 0, SEEK_SET);

    uint8_t* data = (uint8_t*)malloc(file_size);
    fread(data, 1, file_size, f);
    fclose(f);

    /* Read resource count */
    uint32_t res_count;
    memcpy(&res_count, data + 6, 4);
    printf("FDOTHER.DAT: %u resources, file size=%ld\n", res_count, file_size);

    /* Build resource table */
    resource_t* resources = (resource_t*)calloc(res_count, sizeof(resource_t));
    for (uint32_t i = 0; i < res_count; i++) {
        uint32_t offset;
        memcpy(&offset, data + 10 + i * 4, 4);
        resources[i].start = offset;
        if (i + 1 < res_count) {
            resources[i].size = resources[i + 1].start - offset;
        } else {
            resources[i].size = (uint32_t)file_size - offset;
        }
    }

    /* Check resources 69-73 and 74 (title) */
    printf("\n=== Resource Dimensions ===\n");
    int indices[] = {69, 70, 71, 72, 73, 74, 75, 76};
    for (int i = 0; i < sizeof(indices)/sizeof(indices[0]); i++) {
        int idx = indices[i];
        if ((uint32_t)idx >= res_count) {
            printf("Resource %d: NOT FOUND (count=%u)\n", idx, res_count);
            continue;
        }
        
        uint16_t w, h;
        memcpy(&w, data + resources[idx].start, 2);
        memcpy(&h, data + resources[idx].start + 2, 2);
        
        printf("Resource %d: size=%u bytes, width=%u, height=%u, stride=%d\n",
               idx, resources[idx].size, w, h, 147);
        
        /* Check if height matches expected 147 */
        if (h != 147 && idx >= 69 && idx <= 73) {
            printf("  *** WARNING: height %d != 147! This will cause buffer overlap! ***\n", h);
        }
    }

    /* Check what the scroll buffer would look like */
    printf("\n=== Scroll Buffer Layout ===\n");
    printf("Buffer size: 320 x 735 = %u bytes\n", 320 * 735);
    int total_h = 0;
    for (int i = 0; i < 5; i++) {
        int idx = 69 + i;
        uint16_t h;
        memcpy(&h, data + resources[idx].start + 2, 2);
        int dst_y = 147 * i;
        printf("Frame %d (res %d): dst_y=%d, image_h=%d, end_y=%d\n",
               i, idx, dst_y, h, dst_y + h);
        total_h = dst_y + h;
    }
    printf("Total height used: %d (expected: 735)\n", total_h);

    free(data);
    free(resources);
    return 0;
}
