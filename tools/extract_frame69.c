#include <stdio.h>
#include <stdlib.h>
#include "fd2_decoder.h"

int main() {
    fd2_dat_t dat;
    if (fd2_dat_load(&dat, "bin/FDOTHER.DAT") != 0) {
        fprintf(stderr, "Failed to load\n");
        return 1;
    }
    
    u32 size;
    const u8* res = fd2_dat_get_resource(&dat, 69, &size);
    if (!res) {
        printf("No resource\n");
        fd2_dat_free(&dat);
        return 1;
    }
    
    int w, h;
    if (fd2_image_get_dimensions(res, size, &w, &h) != 0) {
        printf("Invalid dimensions\n");
        fd2_dat_free(&dat);
        return 1;
    }
    
    printf("Decoding %dx%d image\n", w, h);
    
    u8* pixels = NULL;
    if (fd2_rle_decompress_from_resource(res, size, &pixels, &w, &h, -1) != 0) {
        printf("Failed to decode\n");
        fd2_dat_free(&dat);
        return 1;
    }
    
    /* Save as raw grayscale PPM */
    FILE* f = fopen("bin/frame69.ppm", "wb");
    fprintf(f, "P6\n%d %d\n255\n", w, h);
    for (int i = 0; i < w * h; i++) {
        u8 v = pixels[i];
        fwrite(&v, 1, 1, f);
        fwrite(&v, 1, 1, f);
        fwrite(&v, 1, 1, f);
    }
    fclose(f);
    
    printf("Saved to bin/frame69.ppm\n");
    
    free(pixels);
    fd2_dat_free(&dat);
    return 0;
}