/**
 * FDOTHER.DAT 资源加载和使用示例
 * 展示如何在游戏中加载和使用所有103个资源
 * 
 * 资源类型：
 * - 调色板 (PALETTE): 索引 0,8,57,76,99,101,102
 * - Tile图像 (TILE): 索引 1,10,11,15,18-34,37-45,54-62,65-75,96-100
 * - LMI1 Tile集 (LMI1): 索引 3,5,6,9,13,14,29
 * - 嵌套DAT (NESTED_DAT): 索引 7,12,31,48-53,63-64,77-95
 * - RAW数据 (RAW): 索引 2,4
 */

#include "fd2_fdother_resources.h"
#include "fd2_audio.h"
#include "fd2_palette.h"
#include "fd2_rle.h"
#include <stdio.h>

/* ========================================================================
 * 1. 调色板资源加载和使用
 * ======================================================================== */

/**
 * 加载主调色板（索引0）
 * 游戏中用于渲染所有图像
 */
int load_main_palette(u32* out_palette_rgb24) {
    fdother_palette_t palette;
    int ret = fdother_get_palette(FDOTHER_PALETTE_0, &palette);
    if (ret != 0) {
        printf("Error: Failed to load main palette (index 0)\n");
        return -1;
    }
    
    // 转换为RGB24格式用于SDL渲染
    if (out_palette_rgb24) {
        byte* rgb24 = (byte*)out_palette_rgb24;
        fdother_palette_to_rgb24(&palette, rgb24);
    }
    
    printf("Main palette loaded: index 0, 768 bytes\n");
    return 0;
}

/**
 * 加载标题画面调色板（索引76）
 */
int load_title_palette(u32* out_palette_rgb24) {
    fdother_palette_t palette;
    int ret = fdother_get_palette(FDOTHER_PALETTE_76, &palette);
    if (ret != 0) {
        printf("Error: Failed to load title palette (index 76)\n");
        return -1;
    }
    
    if (out_palette_rgb24) {
        byte* rgb24 = (byte*)out_palette_rgb24;
        fdother_palette_to_rgb24(&palette, rgb24);
    }
    
    printf("Title palette loaded: index 76, 768 bytes\n");
    return 0;
}

/* ========================================================================
 * 2. Tile图像资源加载和解码
 * ======================================================================== */

/**
 * 加载并解码单个Tile图像
 * @param tile_index: Tile资源索引
 * @param out_pixels: 输出像素缓冲（需要 width * height 字节）
 * @param out_width: 输出宽度
 * @param out_height: 输出高度
 * @return: 0成功，-1失败
 */
int load_and_decode_tile(int tile_index, byte* out_pixels, int* out_width, int* out_height) {
    fdother_tile_t tile;
    int ret = fdother_get_tile(tile_index, &tile);
    if (ret != 0) {
        printf("Error: Failed to load tile %d\n", tile_index);
        return -1;
    }
    
    if (out_width) *out_width = tile.width;
    if (out_height) *out_height = tile.height;
    
    if (out_pixels) {
        ret = fdother_decode_tile(&tile, out_pixels);
        if (ret != 0) {
            printf("Error: Failed to decode tile %d\n", tile_index);
            return -1;
        }
    }
    
    printf("Tile %d loaded: %dx%d, palette_window=%d\n", 
           tile_index, tile.width, tile.height, tile.palette_window);
    return 0;
}

/**
 * 加载全屏图像（320x200）
 * @param tile_index: 资源索引（11,15,55,61,62,74,75,97,100）
 * @param out_screen: 输出屏幕缓冲（需要320*200=64000字节）
 */
int load_screen_image(int tile_index, byte* out_screen) {
    return load_and_decode_tile(tile_index, out_screen, NULL, NULL);
}

/**
 * 加载菜单项图像（320x147）
 * @param menu_index: 菜单索引0-4，对应资源69-73
 * @param out_buffer: 输出缓冲（需要320*147=47040字节）
 */
int load_menu_image(int menu_index, byte* out_buffer) {
    if (menu_index < 0 || menu_index > 4) {
        printf("Error: Invalid menu index %d (must be 0-4)\n", menu_index);
        return -1;
    }
    
    int resource_index = 69 + menu_index;
    return load_and_decode_tile(resource_index, out_buffer, NULL, NULL);
}

/* ========================================================================
 * 3. LMI1 Tile集资源加载
 * ======================================================================== */

/**
 * 加载LMI1 Tile集并获取所有tile
 * @param lmi1_index: LMI1资源索引（3,5,6,9,13,14,29）
 * @param out_tileset: 输出Tile集结构
 */
int load_lmi1_tileset(int lmi1_index, fdother_lmi1_t* out_tileset) {
    int ret = fdother_get_lmi1(lmi1_index, out_tileset);
    if (ret != 0) {
        printf("Error: Failed to load LMI1 tileset %d\n", lmi1_index);
        return -1;
    }
    
    printf("LMI1 tileset %d loaded: %d tiles\n", lmi1_index, out_tileset->tile_count);
    return 0;
}

/**
 * 从LMI1 Tile集中获取单个tile并解码
 * @param lmi1: LMI1 Tile集
 * @param tile_index: Tile索引
 * @param out_pixels: 输出像素缓冲
 * @return: 0成功，-1失败
 */
int decode_lmi1_tile(const fdother_lmi1_t* lmi1, int tile_index, byte* out_pixels) {
    u16 width, height;
    const byte* rle_data;
    u32 rle_size;
    
    int ret = fdother_lmi1_get_tile(lmi1, tile_index, &width, &height, &rle_data, &rle_size);
    if (ret != 0) {
        printf("Error: Failed to get tile %d from LMI1\n", tile_index);
        return -1;
    }
    
    if (out_pixels) {
        // 使用调色板窗口-1（默认）进行解码
        ret = fd_decompress_rle(rle_data, rle_size, out_pixels, width, height, -1);
        if (ret != 0) {
            printf("Error: Failed to decode LMI1 tile %d\n", tile_index);
            return -1;
        }
    }
    
    return 0;
}

/* ========================================================================
 * 4. 嵌套DAT资源加载
 * ======================================================================== */

/**
 * 加载嵌套DAT资源
 * @param nested_index: 嵌套DAT索引（7,12,31,63等）
 * @param out_nested: 输出嵌套DAT结构
 */
int load_nested_dat(int nested_index, fdother_nested_dat_t* out_nested) {
    int ret = fdother_get_nested_dat(nested_index, out_nested);
    if (ret != 0) {
        printf("Error: Failed to load nested DAT %d\n", nested_index);
        return -1;
    }
    
    printf("Nested DAT %d loaded: %d sub-resources\n", 
           nested_index, out_nested->resource_count);
    return 0;
}

/**
 * 从嵌套DAT中获取单个子资源（Tile）并解码
 * @param nested: 嵌套DAT
 * @param resource_index: 子资源索引
 * @param out_pixels: 输出像素缓冲
 * @param out_width: 输出宽度
 * @param out_height: 输出高度
 */
int decode_nested_dat_resource(const fdother_nested_dat_t* nested, 
                               int resource_index, 
                               byte* out_pixels,
                               int* out_width, int* out_height) {
    u32 size;
    const byte* data = fdother_nested_get_resource(nested, resource_index, &size);
    if (!data) {
        printf("Error: Failed to get resource %d from nested DAT\n", resource_index);
        return -1;
    }
    
    // 解析为Tile
    fdother_tile_t tile;
    int ret = fdother_parse_tile(data, size, &tile);
    if (ret != 0) {
        printf("Error: Resource %d is not a valid tile\n", resource_index);
        return -1;
    }
    
    if (out_width) *out_width = tile.width;
    if (out_height) *out_height = tile.height;
    
    if (out_pixels) {
        // 使用tile中的调色板窗口偏移
        ret = fd_decompress_rle(tile.rle_data, tile.rle_size, 
                               out_pixels, tile.width, tile.height, tile.palette_window);
        if (ret != 0) {
            printf("Error: Failed to decode nested resource %d\n", resource_index);
            return -1;
        }
    }
    
    return 0;
}

/* ========================================================================
 * 5. 音效资源加载和播放
 * ======================================================================== */

/**
 * 音效数据结构
 * 根据MCP分析，音效存储在索引31的嵌套DAT中
 * 格式: [start_offset:4][end_offset:4] per sound
 */
typedef struct {
    const byte* sound_data;    // 音效数据指针
    u32 sound_size;            // 音效大小
    int sample_rate;           // 采样率 (通常11025Hz)
    int bits;                  // 位深度 (8或16)
    int channels;              // 声道 (1=单声道, 2=立体声)
} fdother_sound_t;

/**
 * 从音效DAT（索引31）中获取音效
 * @param sound_index: 音效索引（0-15等）
 * @param out_sound: 输出音效结构
 */
int fdother_get_sound(int sound_index, fdother_sound_t* out_sound) {
    // 音效数据在索引31的嵌套DAT中
    fdother_nested_dat_t nested;
    int ret = fdother_get_nested_dat(31, &nested);
    if (ret != 0) {
        printf("Error: Failed to load sound DAT (index 31)\n");
        return -1;
    }
    
    u32 size;
    const byte* data = fdother_nested_get_resource(&nested, sound_index, &size);
    if (!data) {
        printf("Error: Sound %d not found\n", sound_index);
        return -1;
    }
    
    out_sound->sound_data = data;
    out_sound->sound_size = size;
    out_sound->sample_rate = 11025;  // 默认采样率
    out_sound->bits = 8;             // 默认8位
    out_sound->channels = 1;         // 默认单声道
    
    return 0;
}

/**
 * 播放音效
 * @param sound_index: 音效索引
 * @param loop_count: 循环次数（1=不循环，>1=循环，-1=停止）
 */
int fdother_play_sound(int sound_index, int loop_count) {
    fdother_sound_t sound;
    int ret = fdother_get_sound(sound_index, &sound);
    if (ret != 0) {
        return -1;
    }
    
    // 使用现有的音频系统播放
    // 这里需要集成fd2_audio.c中的播放函数
    printf("Playing sound %d: %d bytes, %dHz, %d-bit, %s\n", 
           sound_index, sound.sound_size, sound.sample_rate, 
           sound.bits, sound.channels == 1 ? "mono" : "stereo");
    
    // TODO: 集成到SDL音频系统
    // fd2_audio_play_sample(sound.sound_data, sound.sound_size, 
    //                       sound.sample_rate, sound.bits, sound.channels, loop_count);
    
    return 0;
}

/**
 * 停止所有音效
 */
void fdother_stop_all_sounds(void) {
    // TODO: 调用音频系统停止函数
    printf("Stopping all sounds\n");
}

/* ========================================================================
 * 6. 完整的资源加载示例
 * ======================================================================== */

/**
 * 游戏启动时加载所有必要的资源
 */
int fdother_load_all_game_resources(void) {
    printf("\n=== Loading FDOTHER.DAT Resources ===\n\n");
    
    // 1. 加载FDOTHER.DAT文件
    int ret = fdother_load("game/FDOTHER.DAT");
    if (ret != 0) {
        printf("Error: Failed to load FDOTHER.DAT\n");
        return -1;
    }
    
    // 2. 加载主调色板（索引0）
    u32 palette_rgb24[256];
    ret = load_main_palette(palette_rgb24);
    if (ret != 0) {
        printf("Warning: Failed to load main palette\n");
    }
    
    // 3. 加载关键Tile图像
    printf("\n--- Loading Key Tile Images ---\n");
    
    // 字符位图（16x16）- 用于文本渲染
    byte char_tile_16x16[16 * 16];
    load_and_decode_tile(18, char_tile_16x16, NULL, NULL);
    
    // 全屏图像（320x200）- 用于背景
    byte screen_buffer[320 * 200];
    load_screen_image(11, screen_buffer);
    
    // 菜单项（320x147）- 用于开场动画菜单
    byte menu_buffer[320 * 147];
    load_menu_image(0, menu_buffer);
    
    // 4. 加载LMI1 Tile集
    printf("\n--- Loading LMI1 Tilesets ---\n");
    fdother_lmi1_t lmi1;
    load_lmi1_tileset(5, &lmi1);  // 138个tile的Tile集
    
    // 5. 加载嵌套DAT
    printf("\n--- Loading Nested DATs ---\n");
    fdother_nested_dat_t nested;
    load_nested_dat(12, &nested);  // 122个子资源
    
    // 6. 测试音效加载
    printf("\n--- Testing Sound Loading ---\n");
    fdother_sound_t sound;
    fdother_get_sound(0, &sound);  // 获取音效0
    
    printf("\n=== All Resources Loaded Successfully ===\n\n");
    return 0;
}

/**
 * 释放所有资源
 */
void fdother_free_all_resources(void) {
    fdother_unload();
    printf("All FDOTHER.DAT resources freed\n");
}

/* ========================================================================
 * 7. 资源索引完整映射表
 * ======================================================================== */

/**
 * 获取资源描述
 */
const char* fdother_get_resource_description(int index) {
    switch (index) {
        // 调色板
        case 0: return "Main Palette";
        case 8: return "Palette Copy";
        case 57: return "Palette Copy";
        case 76: return "Title Screen Palette";
        case 99: return "Palette Copy";
        case 101: return "Palette Copy";
        case 102: return "Palette Copy";
        
        // Tile图像 - 图标
        case 1: return "24x24 Icon";
        case 10: return "62x26 Icon";
        case 18: return "16x16 Character A";
        case 19: return "30x30 Character A";
        case 20: return "16x16 Character B";
        case 21: return "30x30 Character B";
        case 22: case 23: return "14x14 Icon";
        case 24: case 25: return "12x12 Icon";
        case 26: case 27: return "18x18 Icon (large data)";
        case 28: case 30: return "32x32 Icon";
        case 32: case 33: return "10x10 Icon";
        case 34: return "101x101 Large Icon";
        case 37: case 38: return "5x5 Icon";
        case 39: case 43: return "33x33 Icon";
        case 42: return "312x192 Large Image";
        case 44: return "31x31 Image";
        case 45: return "59x59 Image";
        case 54: return "111x111 Image";
        case 58: return "20x20 Icon";
        case 65: return "5x5 Icon (large data)";
        case 66: return "14x14 Icon";
        case 67: case 68: return "9x9 Icon";
        case 96: return "24x24 Icon B";
        case 98: return "155x30 Bar Image";
        
        // Tile图像 - 全屏
        case 11: return "320x200 Fullscreen A";
        case 15: return "320x200 Fullscreen B";
        case 55: return "320x200 Fullscreen C";
        case 56: return "320x200 Fullscreen D";
        case 59: case 60: return "320x200 Fullscreen";
        case 61: return "320x200 Fullscreen G";
        case 62: return "320x200 Fullscreen H";
        case 74: return "320x200 Title Text";
        case 75: return "320x200 Fullscreen I";
        case 97: return "320x200 Fullscreen J";
        case 100: return "320x200 Fullscreen K";
        
        // Tile图像 - 菜单
        case 69: return "320x147 Menu A";
        case 70: return "320x147 Menu B";
        case 71: return "320x147 Menu C";
        case 72: return "320x147 Menu D";
        case 73: return "320x147 Menu E";
        
        // LMI1 Tile集
        case 3: return "LMI1 Tileset (23 tiles)";
        case 5: return "LMI1 Tileset (138 tiles)";
        case 6: return "LMI1 Tileset (230 tiles)";
        case 9: return "LMI1 Tileset (12 tiles)";
        case 13: return "LMI1 Tileset (28 tiles)";
        case 14: return "LMI1 Tileset (32 tiles)";
        case 29: return "LMI1 Tileset (24 tiles)";
        
        // 嵌套DAT
        case 7: return "Nested DAT (38 resources)";
        case 12: return "Nested DAT (122 resources)";
        case 31: return "Sound Effects DAT (62 sounds)";
        case 63: return "Nested DAT (130 resources)";
        case 64: return "Nested DAT (34 resources)";
        case 77: return "Nested DAT (26 resources)";
        case 78: return "Nested DAT (14 resources)";
        case 80: return "Nested DAT (74 resources)";
        
        // RAW数据
        case 2: return "Raw Data (37680 bytes) - likely font data";
        case 4: return "Raw Data (58368 bytes) - likely character bitmaps";
        
        default: return "Unknown Resource";
    }
}
