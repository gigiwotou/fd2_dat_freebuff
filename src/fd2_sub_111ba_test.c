#include "fd2_decoder.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* Test sub_111BA: load single resource from DAT file */
static int test_load_single_resource(void) {
    u8* resource;
    u32 size;

    printf("Test: Load FDOTHER.DAT resource 0 (palette, 768 bytes)\n");

    /* sub_111BA offset table starts at byte 6, not byte 10 */
    /* Resource 0 is at offset 422, size 768 (palette) */
    resource = fd2_dat_load_resource("game/FDOTHER.DAT", NULL, 0);
    if (!resource) {
        printf("  FAILED: fd2_dat_load_resource returned NULL\n");
        return 0;
    }

    size = fd2_last_loaded_size;
    printf("  Loaded size: %u bytes (expected 768)\n", size);

    if (size != 768) {
        printf("  FAILED: expected 768 bytes, got %u\n", size);
        free(resource);
        return 0;
    }

    printf("  SUCCESS\n");
    free(resource);
    return 1;
}

/* Test: Load FDOTHER.DAT resource 3 (battle terrain UI) */
static int test_load_terrain_ui(void) {
    u8* resource;
    u32 size;

    printf("Test: Load FDOTHER.DAT resource 1 (terrain UI frame)\n");

    /* Resource 1: offset 1190, size 2235 */
    resource = fd2_dat_load_resource("game/FDOTHER.DAT", NULL, 1);
    if (!resource) {
        printf("  FAILED: fd2_dat_load_resource returned NULL\n");
        return 0;
    }

    size = fd2_last_loaded_size;
    printf("  Loaded size: %u bytes\n", size);

    printf("  SUCCESS\n");
    free(resource);
    return 1;
}

/* Test: Load FDOTHER.DAT resource 5 (terrain UI images) */
static int test_load_terrain_ui_images(void) {
    u8* resource;
    u32 size;

    printf("Test: Load FDOTHER.DAT resource 5 (terrain UI images)\n");

    resource = fd2_dat_load_resource("game/FDOTHER.DAT", NULL, 5);
    if (!resource) {
        printf("  FAILED: fd2_dat_load_resource returned NULL\n");
        return 0;
    }

    size = fd2_last_loaded_size;
    printf("  Loaded size: %u bytes\n", size);

    /* Check if it's a nested DAT (starts with LLLLLL) */
    if (size >= 6 && memcmp(resource, "LLLLLL", 6) == 0) {
        u32 inner_count;
        memcpy(&inner_count, resource + 6, 4);
        printf("  Nested DAT with %u inner resources\n", inner_count);
    }

    printf("  SUCCESS\n");
    free(resource);
    return 1;
}

/* Test: Load FDSHAP.DAT resource 0 (palette) */
static int test_load_fdshap_palette(void) {
    u8* resource;
    u32 size;

    printf("Test: Load FDSHAP.DAT resource 0 (first resource)\n");

    resource = fd2_dat_load_resource("game/FDSHAP.DAT", NULL, 0);
    if (!resource) {
        printf("  FAILED: fd2_dat_load_resource returned NULL\n");
        return 0;
    }

    size = fd2_last_loaded_size;
    printf("  Loaded size: %u bytes\n", size);

    printf("  SUCCESS\n");
    free(resource);
    return 1;
}

/* Test: Resource switching (free old, load new) */
static int test_resource_switch(void) {
    u8* resource;
    u32 size;

    printf("Test: Resource switching (load resource 10, then switch to 11)\n");

    /* Load resource 10 */
    resource = fd2_dat_load_resource("game/FDOTHER.DAT", NULL, 10);
    if (!resource) {
        printf("  FAILED: initial load returned NULL\n");
        return 0;
    }
    size = fd2_last_loaded_size;
    printf("  Initial load (index 10): %u bytes\n", size);

    /* Switch to resource 11 (should free old resource) */
    resource = fd2_dat_load_resource("game/FDOTHER.DAT", resource, 11);
    if (!resource) {
        printf("  FAILED: switch load returned NULL\n");
        return 0;
    }
    size = fd2_last_loaded_size;
    printf("  After switch (index 11): %u bytes\n", size);

    printf("  SUCCESS\n");
    free(resource);
    return 1;
}

int main(void) {
    int passed = 0;
    int total = 5;

    printf("========================================\n");
    printf("  sub_111BA Resource Loader Tests\n");
    printf("========================================\n\n");

    if (test_load_single_resource()) passed++;
    printf("\n");

    if (test_load_terrain_ui()) passed++;
    printf("\n");

    if (test_load_terrain_ui_images()) passed++;
    printf("\n");

    if (test_load_fdshap_palette()) passed++;
    printf("\n");

    if (test_resource_switch()) passed++;
    printf("\n");

    printf("========================================\n");
    printf("  Results: %d/%d passed\n", passed, total);
    printf("========================================\n");

    return (passed == total) ? 0 : 1;
}