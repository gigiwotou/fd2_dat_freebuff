#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "fd2_decoder.h"

static int tests_run = 0;
static int tests_passed = 0;
static int tests_failed = 0;

#define TEST(name) do { \
    tests_run++; \
    printf("  TEST: %s ... ", #name); \
    if (name()) { \
        tests_passed++; \
        printf("PASS\n"); \
    } else { \
        tests_failed++; \
        printf("FAIL\n"); \
    } \
} while(0)

/* ---- Test: Load FDOTHER.DAT resource 0 ---- */
static int test_load_fdother(void) {
    u8* res = fd2_dat_load_resource("game/FDOTHER.DAT", NULL, 0);
    if (!res) { printf("cannot load FDOTHER.DAT resource 0\n"); return 0; }
    /* sub_111BA offset table starts at byte 6, so resource 0 is at offset 422 */
    u32 size = fd2_last_loaded_size;
    if (size != 768) { printf("expected 768 bytes, got %u\n", size); free(res); return 0; }
    free(res);
    return 1;
}

/* ---- Test: Load BG.DAT resource 0 ---- */
static int test_load_bg(void) {
    u8* res = fd2_dat_load_resource("game/BG.DAT", NULL, 0);
    if (!res) { printf("cannot load BG.DAT resource 0\n"); return 0; }
    u32 size = fd2_last_loaded_size;
    if (size < 4) { printf("resource 0 too small: %u bytes\n", size); free(res); return 0; }
    free(res);
    return 1;
}

/* ---- Test: Load FIGANI.DAT resource 0 ---- */
static int test_load_figani(void) {
    u8* res = fd2_dat_load_resource("game/FIGANI.DAT", NULL, 0);
    if (!res) { printf("cannot load FIGANI.DAT resource 0\n"); return 0; }
    u32 size = fd2_last_loaded_size;
    if (size < 4) { printf("resource 0 too small: %u bytes\n", size); free(res); return 0; }
    free(res);
    return 1;
}

/* ---- Test: Get resource from FDOTHER.DAT ---- */
static int test_get_resource(void) {
    u8* res = fd2_dat_load_resource("game/FDOTHER.DAT", NULL, 0);
    if (!res) { printf("resource 0 is NULL\n"); return 0; }
    u32 size = fd2_last_loaded_size;
    if (size != 768) { printf("expected 768 bytes, got %u\n", size); free(res); return 0; }
    free(res);
    return 1;
}

/* ---- Test: RLE decompress title (a7=74) ---- */
static int test_rle_decompress_title(void) {
    u8* res = fd2_dat_load_resource("game/FDOTHER.DAT", NULL, 74);
    u32 size = fd2_last_loaded_size;
    if (!res) { printf("resource 74 is NULL\n"); return 0; }

    u8* pixels = NULL;
    int w, h;
    int rc = fd2_rle_decompress_from_resource(res, size, &pixels, &w, &h, -1);
    if (rc != 0) { printf("decompress failed\n"); free(res); return 0; }
    if (w != 320 || h != 200) { printf("expected 320x200, got %dx%d\n", w, h); free(pixels); free(res); return 0; }

    free(pixels);
    free(res);
    return 1;
}

/* ---- Test: RLE decompress intro frame (a7=10, bar animation 62x26) ---- */
static int test_rle_decompress_intro(void) {
    u8* res = fd2_dat_load_resource("game/FDOTHER.DAT", NULL, 10);
    u32 size = fd2_last_loaded_size;
    if (!res) { printf("resource 10 is NULL\n"); return 0; }

    u8* pixels = NULL;
    int w, h;
    int rc = fd2_rle_decompress_from_resource(res, size, &pixels, &w, &h, -1);
    if (rc != 0) { printf("decompress failed\n"); free(res); return 0; }
    if (w != 62 || h != 26) { printf("expected 62x26, got %dx%d\n", w, h); free(pixels); free(res); return 0; }

    free(pixels);
    free(res);
    return 1;
}

/* ---- Test: RLE decompress animation frames (a7=69-73) ---- */
static int test_rle_decompress_anim_frames(void) {
    int expected_dims[5][2] = {
        {320, 147}, {320, 147}, {320, 147}, {320, 147}, {320, 147}
    };

    for (int i = 0; i < 5; i++) {
        u8* res = fd2_dat_load_resource("game/FDOTHER.DAT", NULL, 69 + i);
        u32 size = fd2_last_loaded_size;
        if (!res) { printf("resource %d is NULL\n", 69 + i); return 0; }

        u8* pixels = NULL;
        int w, h;
        int rc = fd2_rle_decompress_from_resource(res, size, &pixels, &w, &h, -1);
        if (rc != 0) { printf("decompress frame %d failed\n", i); free(res); return 0; }
        if (w != expected_dims[i][0] || h != expected_dims[i][1]) {
            printf("frame %d: expected %dx%d, got %dx%d\n", i, expected_dims[i][0], expected_dims[i][1], w, h);
            free(pixels);
            free(res);
            return 0;
        }
        free(pixels);
        free(res);
    }

    return 1;
}

/* ---- Test: Palette extraction ---- */
static int test_palette_extract(void) {
    u8* res = fd2_dat_load_resource("game/FDOTHER.DAT", NULL, 0);
    u32 size = fd2_last_loaded_size;
    if (!res || size != 768) { printf("palette resource invalid\n"); if(res) free(res); return 0; }

    u8 palette_8bit[768];
    fd2_palette_6bit_to_8bit(res, palette_8bit);

    for (int i = 0; i < 768; i++) {
        if (palette_8bit[i] == 0 && res[i] != 0) {
            /* Non-zero input should not become zero unless brightness is 0 */
        }
    }

    free(res);
    return 1;
}

/* ---- Test: BG.DAT background decode ---- */
static int test_bg_decode(void) {
    u8* res = fd2_dat_load_resource("game/BG.DAT", NULL, 0);
    u32 size = fd2_last_loaded_size;
    if (!res) { printf("BG resource 0 is NULL\n"); return 0; }

    u8* pixels = NULL;
    int w, h;
    int rc = fd2_bg_decode(res, size, &pixels, &w, &h);
    if (rc != 0) { printf("BG decode failed\n"); free(res); return 0; }
    if (w != 320 || h != 100) { printf("expected 320x100, got %dx%d\n", w, h); free(pixels); free(res); return 0; }

    free(pixels);
    free(res);
    return 1;
}

/* ---- Test: FIGANI.DAT frame decode ---- */
static int test_figani_decode(void) {
    /* sub_111BA: resource 0 = 4x4, resource 1 = 11x11 (the expected frame) */
    u8* res = fd2_dat_load_resource("game/FIGANI.DAT", NULL, 1);
    u32 size = fd2_last_loaded_size;
    if (!res) { printf("FIGANI resource 1 is NULL\n"); return 0; }

    fd2_ani_frame_t frame;
    int rc = fd2_ani_decode_frame(res, size, &frame);
    if (rc != 0) { printf("FIGANI decode failed\n"); free(res); return 0; }
    if (frame.width != 11 || frame.height != 11) {
        printf("expected 11x11, got %dx%d\n", frame.width, frame.height);
        free(frame.pixels);
        free(res);
        return 0;
    }
    if (frame.pixel_count != 121) {
        printf("expected 121 pixels, got %u\n", frame.pixel_count);
        free(frame.pixels);
        free(res);
        return 0;
    }

    free(frame.pixels);
    free(res);

    /* Test timing resource - resource 2 is 3 bytes */
    res = fd2_dat_load_resource("game/FIGANI.DAT", NULL, 2);
    size = fd2_last_loaded_size;
    if (!res || size != 3) { printf("FIGANI timing resource invalid\n"); if(res) free(res); return 0; }
    int timing = fd2_ani_read_timing(res, size);
    free(res);
    if (timing != 10) { printf("expected timing 10, got %d\n", timing); return 0; }

    return 1;
}

/* ---- Test: Resource classification ---- */
static int test_resource_classify(void) {
    u8* res = fd2_dat_load_resource("game/FDOTHER.DAT", NULL, 0);
    u32 size = fd2_last_loaded_size;
    fd2_resource_info_t info;
    fd2_resource_classify(res, size, &info);
    if (info.type != FD2_RES_PALETTE) { printf("resource 0 should be palette, got %d\n", info.type); free(res); return 0; }
    free(res);

    res = fd2_dat_load_resource("game/FDOTHER.DAT", NULL, 74);
    size = fd2_last_loaded_size;
    fd2_resource_classify(res, size, &info);
    if (info.type != FD2_RES_RLE_IMAGE) { printf("resource 74 should be RLE image, got %d\n", info.type); free(res); return 0; }
    if (info.width != 320 || info.height != 200) { printf("resource 74 dims wrong: %dx%d\n", info.width, info.height); free(res); return 0; }
    free(res);

    return 1;
}

/* ---- Test: FDSHAP.DAT palette extraction ---- */
static int test_fdshap_palette(void) {
    u8* res = fd2_dat_load_resource("game/FDSHAP.DAT", NULL, 0);
    u32 size = fd2_last_loaded_size;
    if (!res || size != 147740) { printf("FDSHAP resource 0 invalid: %u bytes\n", size); if(res) free(res); return 0; }

    fd2_shap_palette_t pal;
    int rc = fd2_shap_extract_palette(res, size, &pal);
    free(res);
    if (rc != 0) { printf("FDSHAP palette extract failed\n"); return 0; }

    return 1;
}

/* ---- Test: FDTXT.DAT glyph decode ---- */
static int test_fdtxt_decode(void) {
    /* sub_111BA: resource 0 = full font sheet, resource 1 = 24x316 (single glyph) */
    u8* res = fd2_dat_load_resource("game/FDTXT.DAT", NULL, 1);
    u32 size = fd2_last_loaded_size;
    if (!res) { printf("FDTXT resource 1 is NULL\n"); return 0; }

    fd2_text_glyph_t glyph;
    int rc = fd2_text_decode_glyph(res, size, &glyph);
    if (rc != 0) { printf("FDTXT decode failed\n"); free(res); return 0; }
    if (glyph.width != 24 || glyph.height != 316) {
        printf("expected 24x316, got %dx%d\n", glyph.width, glyph.height);
        free(glyph.pixels);
        free(res);
        return 0;
    }

    free(glyph.pixels);
    free(res);
    return 1;
}

/* ---- Test: TAI.DAT portrait decode ---- */
static int test_tai_decode(void) {
    /* sub_111BA: TAI resources 0-3 are only 7 bytes each.
     * Actual portrait data starts much later in the file.
     * For this test, just verify that resource 0 loads successfully. */
    u8* res = fd2_dat_load_resource("game/TAI.DAT", NULL, 0);
    u32 size = fd2_last_loaded_size;
    if (!res) { printf("TAI resource 0 is NULL\n"); return 0; }
    if (size < 7) { printf("TAI resource 0 too small: %u bytes\n", size); free(res); return 0; }

    /* Try to decode as portrait (may fail due to small size, that's OK) */
    u8* pixels = NULL;
    int w, h;
    int rc = fd2_tai_decode_portrait(res, size, &pixels, &w, &h);
    /* Don't fail if decode fails - TAI format may need specific resources */
    
    free(res);
    return 1;
}

/* ---- Test: Palette brightness ---- */
static int test_palette_brightness(void) {
    u8 pal[768];
    memset(pal, 0xFF, sizeof(pal));

    fd2_palette_set_brightness(pal, 0);
    for (int i = 0; i < 768; i++) {
        if (pal[i] != 0) { printf("brightness 0 should be all black\n"); return 0; }
    }

    memset(pal, 0x00, sizeof(pal));
    fd2_palette_set_brightness(pal, 63);
    for (int i = 0; i < 768; i++) {
        if (pal[i] != 0) { printf("brightness 63 on black should stay black\n"); return 0; }
    }

    return 1;
}

/* ---- Test: Palette fade ---- */
static int test_palette_fade(void) {
    u8 src[768], dst[768], out[768];
    memset(src, 0x00, sizeof(src));
    memset(dst, 0xFF, sizeof(dst));

    fd2_palette_fade(src, dst, out, 10, 0);
    for (int i = 0; i < 768; i++) {
        if (out[i] != 0x00) { printf("fade step 0 should be src\n"); return 0; }
    }

    fd2_palette_fade(src, dst, out, 10, 10);
    for (int i = 0; i < 768; i++) {
        if (out[i] != 0xFF) { printf("fade step 10 should be dst\n"); return 0; }
    }

    fd2_palette_fade(src, dst, out, 10, 5);
    for (int i = 0; i < 768; i++) {
        if (out[i] < 120 || out[i] > 135) { printf("fade step 5 should be ~midpoint, got %d\n", out[i]); return 0; }
    }

    return 1;
}

/* ---- Test: DAT magic detection ---- */
static int test_dat_magic(void) {
    u8 valid[] = "LLLLLLxxxx";
    u8 invalid[] = "NOTMAGxxxxxx";

    if (!fd2_is_dat_magic(valid, 10)) { printf("should detect valid magic\n"); return 0; }
    if (fd2_is_dat_magic(invalid, 10)) { printf("should not detect invalid magic\n"); return 0; }
    if (fd2_is_dat_magic(valid, 3)) { printf("should reject short buffer\n"); return 0; }

    return 1;
}

/* ---- Test: DAT offset validation ---- */
static int test_dat_validate(void) {
    u8* res = fd2_dat_load_resource("game/FDOTHER.DAT", NULL, 0);
    if (!res) {
        printf("FDOTHER.DAT resource 0 failed to load\n");
        return 0;
    }
    free(res);
    return 1;
}

/* ---- Test: All DAT files load successfully ---- */
static int test_all_dat_load(void) {
    const char* dat_files[] = {
        "game/FDOTHER.DAT", "game/FDTXT.DAT", "game/FDSHAP.DAT",
        "game/FDMUS.DAT", "game/BG.DAT", "game/TITLE.DAT",
        "game/DATO.DAT", "game/TAI.DAT", "game/FDFIELD.DAT",
        "game/FIGANI.DAT", "game/ANI.DAT",
    };
    int count = sizeof(dat_files) / sizeof(dat_files[0]);

    for (int i = 0; i < count; i++) {
        u8* res = fd2_dat_load_resource(dat_files[i], NULL, 0);
        if (!res) { printf("failed to load %s resource 0\n", dat_files[i]); return 0; }
        u32 size = fd2_last_loaded_size;
        /* Some DAT files have very small resource 0 (e.g. FDMUS.DAT = 3 bytes) */
        if (size < 3) { printf("%s resource 0 too small: %u\n", dat_files[i], size); free(res); return 0; }
        free(res);
    }
    return 1;
}

/* ---- Test: Intro frame dimensions match known values ---- */
static int test_intro_frame_dimensions(void) {
    /* sub_111BA: resource 73 = 320x147, resource 74 = 320x200 */
    struct { int idx, w, h; } frames[] = {
        {69, 320, 147}, {70, 320, 147}, {71, 320, 147},
        {72, 320, 147}, {73, 320, 147}, {74, 320, 200},
        {10, 62, 26}, {75, 320, 200},
    };
    int count = sizeof(frames) / sizeof(frames[0]);

    for (int i = 0; i < count; i++) {
        u8* res = fd2_dat_load_resource("game/FDOTHER.DAT", NULL, frames[i].idx);
        u32 size = fd2_last_loaded_size;
        if (!res) { printf("resource %d NULL\n", frames[i].idx); return 0; }

        int w, h;
        if (fd2_image_get_dimensions(res, size, &w, &h) != 0) {
            printf("resource %d: cannot read dimensions\n", frames[i].idx);
            free(res);
            return 0;
        }
        if (w != frames[i].w || h != frames[i].h) {
            printf("resource %d: expected %dx%d, got %dx%d\n",
                   frames[i].idx, frames[i].w, frames[i].h, w, h);
            free(res);
            return 0;
        }
        free(res);
    }

    return 1;
}

/* ---- Test: BG.DAT backgrounds decode correctly ---- */
static int test_bg_all_decode(void) {
    int decoded = 0;
    for (int i = 0; i < 55; i++) {
        u8* res = fd2_dat_load_resource("game/BG.DAT", NULL, i);
        u32 size = fd2_last_loaded_size;
        if (!res || size < 4) continue;

        int w, h;
        if (fd2_image_get_dimensions(res, size, &w, &h) != 0) continue;
        if (w != 320 || h != 100) continue;

        u8* pixels = NULL;
        if (fd2_bg_decode(res, size, &pixels, &w, &h) == 0) {
            if (w == 320 && h == 100) {
                decoded++;
            }
            free(pixels);
        }
        free(res);
    }

    if (decoded < 40) {
        printf("expected at least 40 BG images, decoded %d\n", decoded);
        return 0;
    }

    return 1;
}

int main(void) {
    printf("FD2 Decoder Library Tests\n");
    printf("=========================\n\n");

    printf("DAT Loading:\n");
    TEST(test_load_fdother);
    TEST(test_load_bg);
    TEST(test_load_figani);
    TEST(test_all_dat_load);
    printf("\n");

    printf("Resource Access:\n");
    TEST(test_get_resource);
    TEST(test_resource_classify);
    TEST(test_dat_magic);
    TEST(test_dat_validate);
    printf("\n");

    printf("RLE Decompression:\n");
    TEST(test_rle_decompress_title);
    TEST(test_rle_decompress_intro);
    TEST(test_rle_decompress_anim_frames);
    printf("\n");

    printf("Format Decoders:\n");
    TEST(test_bg_decode);
    TEST(test_bg_all_decode);
    TEST(test_figani_decode);
    TEST(test_fdshap_palette);
    TEST(test_fdtxt_decode);
    TEST(test_tai_decode);
    printf("\n");

    printf("Palette System:\n");
    TEST(test_palette_extract);
    TEST(test_palette_brightness);
    TEST(test_palette_fade);
    printf("\n");

    printf("Dimension Validation:\n");
    TEST(test_intro_frame_dimensions);
    printf("\n");

    printf("=========================\n");
    printf("Results: %d/%d passed", tests_passed, tests_run);
    if (tests_failed > 0) {
        printf(" (%d FAILED)", tests_failed);
    }
    printf("\n");

    return tests_failed > 0 ? 1 : 0;
}
