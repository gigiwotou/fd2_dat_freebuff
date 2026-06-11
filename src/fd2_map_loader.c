/**
 * FD2 Map Loader and Renderer
 *
 * Loads map data from FDFIELD.DAT and FDSHAP.DAT files,
 * and renders the map with correct tiles and palette.
 *
 * Based on IDA analysis:
 *   - sub_1088D: Map loading function
 *   - sub_4DF4C: Terrain data processing
 *   - sub_12E38: Tile data extraction
 *   - sub_1ACF3: Tile rendering
 *   - sub_4E22A: RLE decompression
 */

#include "../include/fd2_map_loader.h"
#include "../include/fd2_rle.h"
#include "../include/fd2_dat_loader.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* ---- DAT File Format 2: No count, offset table from byte 6 ----
 * 解析函数已统一到 fd2_dat_loader_parse_entries_format2()
 * 原本地 parse_dat_entries() 和 get_resource() 已删除,统一使用 fd2_dat_loader_* 接口
 */

/* Load file & RLE 已统一到 fd2_dat_loader / fd2_rle 中
 * 原本地的 rle_decompress() 和 load_file() 已删除,统一使用 fd2_dat_loader_load_file() 接口
 */

/* ---- Public API ---- */

int fd2_map_init(fd2_map_t* map) {
    if (!map) return -1;

    memset(map, 0, sizeof(*map));
    map->tile_size = 24;
    map->loaded = false;
    return 0;
}

int fd2_map_load_from_dat(fd2_map_t* map, int map_id,
                          const char* fdfield_path,
                          const char* fdshap_path,
                          const char* fdother_path) {
    if (!map || !fdfield_path || !fdshap_path || !fdother_path) {
        return -1;
    }

    printf("fd2_map_load_from_dat: loading map %d\n", map_id);

    /* Load DAT files - 使用统一加载器 */
    u32 fdfield_size, fdshap_size, fdother_size;
    u8* fdfield_data = fd2_dat_loader_load_file(fdfield_path, &fdfield_size);
    u8* fdshap_data = fd2_dat_loader_load_file(fdshap_path, &fdshap_size);
    u8* fdother_data = fd2_dat_loader_load_file(fdother_path, &fdother_size);

    if (!fdfield_data || !fdshap_data || !fdother_data) {
        fprintf(stderr, "fd2_map_load_from_dat: failed to load DAT files\n");
        free(fdfield_data);
        free(fdshap_data);
        free(fdother_data);
        return -1;
    }

    /* Parse FDFIELD.DAT entries (format 2: no count, offsets from byte 6)
     * Note: byte 6-9 contains a count value (406), but format 2 treats it as offset[0].
     * This means offset[0] = 406, which points to actual layout data.
     * 使用统一 DAT 加载器解析
     */
    u32* fdfield_offsets = NULL;
    int fdfield_count = 0;
    if (fd2_dat_loader_parse_entries_format2(fdfield_data, fdfield_size, 512,
                                              &fdfield_offsets, &fdfield_count) != 0) {
        fprintf(stderr, "fd2_map_load_from_dat: cannot parse FDFIELD.DAT\n");
        goto cleanup;
    }
    printf("fd2_map_load_from_dat: FDFIELD.DAT parsed %d resources (format 2)\n", fdfield_count);

    /* Parse FDSHAP.DAT entries (format 2) */
    u32* fdshap_offsets = NULL;
    int fdshap_count = 0;
    if (fd2_dat_loader_parse_entries_format2(fdshap_data, fdshap_size, 128,
                                              &fdshap_offsets, &fdshap_count) != 0) {
        fprintf(stderr, "fd2_map_load_from_dat: cannot parse FDSHAP.DAT\n");
        goto cleanup;
    }
    printf("fd2_map_load_from_dat: FDSHAP.DAT parsed %d resources (format 2)\n", fdshap_count);

    /* Parse FDOTHER.DAT entries (format 2) */
    u32* fdother_offsets = NULL;
    int fdother_count = 0;
    if (fd2_dat_loader_parse_entries_format2(fdother_data, fdother_size, 512,
                                              &fdother_offsets, &fdother_count) != 0) {
        fprintf(stderr, "fd2_map_load_from_dat: cannot parse FDOTHER.DAT\n");
        goto cleanup;
    }
    printf("fd2_map_load_from_dat: FDOTHER.DAT parsed %d resources (format 2)\n", fdother_count);

    /* Load global palette from FDOTHER.DAT resource 0 */
    {
        u32 pal_size;
        const u8* pal_data = fd2_dat_loader_get_resource(fdother_data, fdother_size, fdother_offsets, fdother_count, 0, &pal_size);
        if (pal_data && pal_size >= FD2_PALETTE_BYTES) {
            memcpy(map->palette, pal_data, FD2_PALETTE_BYTES);
            map->palette_loaded = true;
            printf("fd2_map_load_from_dat: palette loaded from FDOTHER.DAT[0]\n");
        } else {
            fprintf(stderr, "fd2_map_load_from_dat: failed to load palette\n");
            goto cleanup;
        }
    }

    /* Load FDFIELD.DAT resources (format 2 indices, same as Python):
     * map_id * 3 = Layout index
     * map_id * 3 + 1 = Control index
     */
    int layout_idx = map_id * 3;
    int control_idx = map_id * 3 + 1;

    printf("fd2_map_load_from_dat: map %d, requesting layout[%d], control[%d]\n",
           map_id, layout_idx, control_idx);
    printf("fd2_map_load_from_dat: fdfield offsets[0..3]: ");
    for (int i = 0; i < 4 && i < fdfield_count; i++) {
        printf("%u ", fdfield_offsets[i]);
    }
    printf("\n");

    if (layout_idx + 1 >= fdfield_count) {
        fprintf(stderr, "fd2_map_load_from_dat: map %d layout index %d out of range (count=%d)\n",
                map_id, layout_idx, fdfield_count);
        goto cleanup;
    }

    u32 layout_size;
    const u8* layout_data = fd2_dat_loader_get_resource(fdfield_data, fdfield_size, fdfield_offsets, fdfield_count, layout_idx, &layout_size);
    if (!layout_data || layout_size < 4) {
        fprintf(stderr, "fd2_map_load_from_dat: failed to load layout for map %d\n", map_id);
        goto cleanup;
    }

    printf("fd2_map_load_from_dat: layout_data at offset %u, size=%u\n", fdfield_offsets[layout_idx], layout_size);

    /* Load control data to get terrain_set_id and map parameters (IDA sub_1088D lines 1098b-10995) */
    u32 control_size;
    const u8* control_data = fd2_dat_loader_get_resource(fdfield_data, fdfield_size, fdfield_offsets, fdfield_count, control_idx, &control_size);
    if (!control_data || control_size < 3) {
        fprintf(stderr, "fd2_map_load_from_dat: failed to load control for map %d\n", map_id);
        goto cleanup;
    }

    printf("fd2_map_load_from_dat: control_data at offset %u, size=%u\n", fdfield_offsets[control_idx], control_size);

    /* IDA parsing:
     * byte[0] = terrain_set_id
     * byte[1] = max_friendly (::n6)
     * byte[2] = total_units (dword_53BE3)
     */
    int terrain_set_id = control_data[0];
    map->terrain_set_id = terrain_set_id;
    map->scene.map_number = map_id;
    map->scene.max_friendly = control_data[1];
    map->scene.total_units = control_data[2];

    printf("fd2_map_load_from_dat: map %d, control[%d] size=%u, terrain_set_id=%d\n",
           map_id, control_idx, control_size, terrain_set_id);
    printf("  max_friendly (::n6) = %d\n", map->scene.max_friendly);
    printf("  total_units (dword_53BE3) = %d\n", map->scene.total_units);

    /* Load FDSHAP.DAT tileset: terrain_set_id * 2 (tileset at even resources) */
    int tileset_idx = terrain_set_id * 2;

    if (tileset_idx + 1 >= fdshap_count) {
        fprintf(stderr, "fd2_map_load_from_dat: tileset index %d out of range (count=%d)\n",
                tileset_idx, fdshap_count);
        goto cleanup;
    }

    u32 tileset_size;
    const u8* tileset_data = fd2_dat_loader_get_resource(fdshap_data, fdshap_size, fdshap_offsets, fdshap_count, tileset_idx, &tileset_size);
    if (!tileset_data || tileset_size < 6) {
        fprintf(stderr, "fd2_map_load_from_dat: failed to load tileset %d\n", tileset_idx);
        goto cleanup;
    }

    /* Parse tileset header:
     * byte 0-1: tile_width (WORD)
     * byte 2-3: tile_height (WORD)
     * byte 4-5: tile_count (WORD)
     * byte 6+: tile offsets (DWORD array)
     */
    int tile_width = tileset_data[0] | (tileset_data[1] << 8);
    int tile_height = tileset_data[2] | (tileset_data[3] << 8);
    int tile_count = tileset_data[4] | (tileset_data[5] << 8);

    map->tile_size = tile_width;  /* Assuming square tiles */
    map->tileset_count = tile_count;

    printf("fd2_map_load_from_dat: tileset %d: %dx%d, %d tiles, resource size=%u\n",
           tileset_idx, tile_width, tile_height, tile_count, tileset_size);

    /* Parse tile offsets from byte 6 onwards (no "LLLLLL" magic in tileset data) */
    u32* tile_offsets = NULL;
    int tile_offset_count = 0;
    {
        int capacity = tile_count + 16;
        tile_offsets = (u32*)malloc(capacity * sizeof(u32));
        if (!tile_offsets) {
            fprintf(stderr, "fd2_map_load_from_dat: cannot allocate tile_offsets\n");
            goto cleanup;
        }

        u32 pos = 6;
        while (pos + 4 <= tileset_size && tile_offset_count < capacity) {
            u32 offset = tileset_data[pos] | (tileset_data[pos+1] << 8) |
                         (tileset_data[pos+2] << 16) | (tileset_data[pos+3] << 24);
            
            /* Stop if offset is invalid */
            if (offset > tileset_size) {
                break;
            }

            tile_offsets[tile_offset_count] = offset;
            tile_offset_count++;
            pos += 4;
        }
    }

    printf("fd2_map_load_from_dat: parsed %d tile offsets\n", tile_offset_count);

    /* Decode all tiles */
    for (int i = 0; i < tile_count && i < FD2_MAX_TILES; i++) {
        if (i >= tile_offset_count - 1) {
            break;
        }

        u32 tile_start = tile_offsets[i];
        u32 tile_end = tile_offsets[i + 1];

        if (tile_start >= tileset_size || tile_end > tileset_size || tile_end <= tile_start) {
            continue;
        }

        const u8* tile_rle_data = tileset_data + tile_start;
        u32 tile_rle_size = tile_end - tile_start;

        /* Allocate tile pixel buffer */
        int pixel_count = tile_width * tile_height;
        u8* tile_pixels = (u8*)calloc(pixel_count, sizeof(u8));
        if (!tile_pixels) {
            fprintf(stderr, "fd2_map_load_from_dat: cannot allocate tile %d buffer\n", i);
            continue;
        }

        /* Decompress tile - 使用统一 fd2_rle.c 中的 fd2_rle_decompress 接口
         * 注: FDSHAP瓦块数据不包含4字节头,直接调用通用解码器
         */
        if (fd2_rle_decompress(tile_rle_data, tile_rle_size, tile_pixels, tile_width, tile_height) == 0) {
            map->tile_images[i].width = tile_width;
            map->tile_images[i].height = tile_height;
            map->tile_images[i].pixels = tile_pixels;
            map->tile_images[i].valid = true;
        } else {
            fprintf(stderr, "fd2_map_load_from_dat: failed to decompress tile %d\n", i);
            free(tile_pixels);
        }
    }

    printf("fd2_map_load_from_dat: loaded %d/%d tiles\n",
           map->tileset_count, tile_count);

    /* Parse layout data */
    /* Layout format: width(2) + height(2) + tile_data(4 bytes per tile) */
    int map_width = layout_data[0] | (layout_data[1] << 8);
    int map_height = layout_data[2] | (layout_data[3] << 8);

    printf("fd2_map_load_from_dat: layout[%d] size=%u\n", layout_idx, layout_size);
    printf("fd2_map_load_from_dat: layout data[0..9]: ");
    for (int i = 0; i < 10 && i < (int)layout_size; i++) {
        printf("%02x ", layout_data[i]);
    }
    printf("\n");

    printf("fd2_map_load_from_dat: parsed dimensions: width=%d (0x%04x), height=%d (0x%04x)\n",
           map_width, map_width, map_height, map_height);

    if (map_width <= 0 || map_height <= 0 ||
        map_width > FD2_MAP_MAX_WIDTH || map_height > FD2_MAP_MAX_HEIGHT) {
        fprintf(stderr, "fd2_map_load_from_dat: invalid map dimensions %dx%d\n", map_width, map_height);
        goto cleanup;
    }

    map->width = map_width;
    map->height = map_height;
    map->map_id = map_id;

    printf("fd2_map_load_from_dat: map %d is %dx%d tiles\n", map_id, map_width, map_height);

    /* Parse tile data (4 bytes per tile) */
    const u8* tile_data = layout_data + 4;
    u32 tile_data_size = layout_size - 4;

    for (int y = 0; y < map_height; y++) {
        for (int x = 0; x < map_width; x++) {
            u32 pos = (y * map_width + x) * 4;
            if (pos + 4 > tile_data_size) {
                break;
            }

            u8 b0 = tile_data[pos];
            u8 b1 = tile_data[pos + 1];
            u8 b2 = tile_data[pos + 2];
            u8 b3 = tile_data[pos + 3];

            /* Extract terrain ID: byte[0] | ((byte[1] & 0x03) << 8) */
            uint16_t terrain_id = b0 | ((b1 & 0x03) << 8);

            map->tiles[y][x].terrain_id = terrain_id;
            map->tiles[y][x].event_id = b2 | (b3 << 8);
            map->tiles[y][x].terrain_flag = b1 & 0x03;
            map->tiles[y][x].event_type = b2 & 0x1F;
        }
    }

    /* Pre-render the full map image */
    int map_pixel_width = map_width * tile_width;
    int map_pixel_height = map_height * tile_height;

    map->map_image = (u8*)calloc(map_pixel_width * map_pixel_height, sizeof(u8));
    if (map->map_image) {
        map->map_image_width = map_pixel_width;
        map->map_image_height = map_pixel_height;

        /* Render each tile */
        int rendered_count = 0;
        for (int y = 0; y < map_height; y++) {
            for (int x = 0; x < map_width; x++) {
                uint16_t terrain_id = map->tiles[y][x].terrain_id;

                /* Use terrain_id directly as tile index (no mask!) */
                int tile_idx = terrain_id;

                if (tile_idx >= 0 && tile_idx < tile_count && map->tile_images[tile_idx].valid) {
                    /* Copy tile pixels to map image */
                    const u8* tile_pixels = map->tile_images[tile_idx].pixels;
                    int dst_x = x * tile_width;
                    int dst_y = y * tile_height;

                    for (int ty = 0; ty < tile_height; ty++) {
                        if (dst_y + ty >= map_pixel_height) break;
                        for (int tx = 0; tx < tile_width; tx++) {
                            if (dst_x + tx >= map_pixel_width) break;
                            int src_idx = ty * tile_width + tx;
                            int dst_idx = (dst_y + ty) * map_pixel_width + (dst_x + tx);
                            map->map_image[dst_idx] = tile_pixels[src_idx];
                        }
                    }
                    rendered_count++;
                }
            }
        }

        map->map_rendered = true;
        printf("fd2_map_load_from_dat: rendered %d/%d tiles to map image\n",
               rendered_count, map_width * map_height);
    }

    map->loaded = true;

    /* Parse character info from control data (enemy/NPC units, 26 bytes each)
     * Structure starts at offset 0x83 (131 bytes) in control data */
    u32 char_info_offset = 0x83;
    
    if (char_info_offset + 26 <= control_size) {
        int char_info_count = map->scene.total_units;
        map->scene.char_info_count = (char_info_count < FD2_MAX_MAP_CHARS) ? 
                                     char_info_count : FD2_MAX_MAP_CHARS;
        
        printf("fd2_map_load_from_dat: Parsing %d enemy/NPC character info units\n", map->scene.char_info_count);
        
        for (int i = 0; i < map->scene.char_info_count; i++) {
            u32 offset = char_info_offset + i * 26;
            if (offset + 26 > control_size) break;
            
            map->scene.char_info[i].faction = control_data[offset];
            map->scene.char_info[i].portrait_id = control_data[offset + 1];
            map->scene.char_info[i].race_id = control_data[offset + 2];
            map->scene.char_info[i].job_id = control_data[offset + 3];
            map->scene.char_info[i].level = control_data[offset + 4];
            memcpy(map->scene.char_info[i].items, &control_data[offset + 5], 8);
            memcpy(map->scene.char_info[i].spells, &control_data[offset + 13], 4);
            map->scene.char_info[i].spawn_turn = control_data[offset + 17];
            map->scene.char_info[i].drop_type = control_data[offset + 18];
            memcpy(map->scene.char_info[i].drop_content, &control_data[offset + 19], 3);
            memcpy(map->scene.char_info[i].reserved, &control_data[offset + 22], 4);
        }
    }
    
    /* Parse character spawn positions (IDA sub_1088D line 10a6a)
     * IDA reads max_friendly characters starting from: 6 * total_units + 2
     * But for complete map rendering, we need ALL characters:
     *   - First total_units entries: enemy/NPC positions
     *   - Next max_friendly entries: friendly character positions
     */
    int char_pos_idx = map_id * 3 + 2;
    
    if (char_pos_idx < fdfield_count) {
        u32 char_pos_size;
        const u8* char_pos_data = fd2_dat_loader_get_resource(fdfield_data, fdfield_size,
                                               fdfield_offsets, fdfield_count,
                                               char_pos_idx, &char_pos_size);
        
        if (char_pos_data && char_pos_size >= 2) {
            uint16_t total_chars = char_pos_data[0] | (char_pos_data[1] << 8);
            
            printf("fd2_map_load_from_dat: character position data\n");
            printf("  Total characters in file: %d\n", total_chars);
            printf("  total_units (enemies) = %d\n", map->scene.total_units);
            printf("  max_friendly = %d\n", map->scene.max_friendly);
            
            /* Read ALL characters from file */
            map->scene.char_pos_count = 0;
            
            for (int i = 0; i < total_chars && i < FD2_MAX_MAP_CHARS; i++) {
                u32 offset = 2 + i * 6;
                
                if (offset + 6 > char_pos_size) {
                    printf("  Warning: insufficient data for char %d\n", i);
                    break;
                }
                
                /* Parse character position:
                 * byte[0] = X coordinate
                 * byte[2] = Y coordinate
                 * byte[4] = portrait ID
                 */
                u8 byte0 = char_pos_data[offset];
                u8 byte1 = char_pos_data[offset + 1];
                u8 byte2 = char_pos_data[offset + 2];
                u8 byte3 = char_pos_data[offset + 3];
                u8 byte4 = char_pos_data[offset + 4];
                u8 byte5 = char_pos_data[offset + 5];
                
                printf("  char[%d] raw bytes: [%02x %02x %02x %02x %02x %02x]\n",
                       i, byte0, byte1, byte2, byte3, byte4, byte5);
                
                map->scene.char_positions[i].x = byte0;
                map->scene.char_positions[i].y = byte2;
                map->scene.char_positions[i].portrait_id = byte4;
                map->scene.char_pos_count++;
                
                /* Mark character type based on position in file */
                if (i < map->scene.total_units) {
                    printf("  Enemy %d: pos=(%d,%d), portrait=%d\n",
                           i,
                           map->scene.char_positions[i].x,
                           map->scene.char_positions[i].y,
                           map->scene.char_positions[i].portrait_id);
                } else {
                    printf("  Friendly %d: pos=(%d,%d), portrait=%d\n",
                           i - map->scene.total_units,
                           map->scene.char_positions[i].x,
                           map->scene.char_positions[i].y,
                           map->scene.char_positions[i].portrait_id);
                }
            }
            
            map->scene.loaded = true;
        }
    }

cleanup:
    /* Cleanup temporary data */
    free(fdfield_offsets);
    free(fdshap_offsets);
    free(fdother_offsets);
    free(tile_offsets);  /* Free tile offsets if allocated */
    free(fdfield_data);
    free(fdshap_data);
    free(fdother_data);

    return map->loaded ? 0 : -1;
}

void fd2_map_free(fd2_map_t* map) {
    if (!map) return;

    /* Free tile pixel buffers */
    for (int i = 0; i < FD2_MAX_TILES; i++) {
        if (map->tile_images[i].pixels) {
            free(map->tile_images[i].pixels);
            map->tile_images[i].pixels = NULL;
            map->tile_images[i].valid = false;
        }
    }

    /* Free map image */
    if (map->map_image) {
        free(map->map_image);
        map->map_image = NULL;
    }

    map->loaded = false;
}

void fd2_map_render(const fd2_map_t* map,
                    u8* screen, int screen_w, int screen_h,
                    int offset_x, int offset_y) {
    if (!map || !screen || !map->loaded || !map->map_rendered) {
        return;
    }

    /* REMOVED: memset(screen, 0, screen_w * screen_h); - causes sprite flickering */

    /* Copy map image to screen with scroll offset */
    for (int sy = 0; sy < screen_h; sy++) {
        int map_y = offset_y + sy;
        if (map_y < 0 || map_y >= map->map_image_height) continue;

        for (int sx = 0; sx < screen_w; sx++) {
            int map_x = offset_x + sx;
            if (map_x < 0 || map_x >= map->map_image_width) continue;

            int src_idx = map_y * map->map_image_width + map_x;
            int dst_idx = sy * screen_w + sx;
            screen[dst_idx] = map->map_image[src_idx];
        }
    }
}

void fd2_map_render_centered(const fd2_map_t* map,
                              u8* screen, int screen_w, int screen_h) {
    if (!map || !screen || !map->loaded || !map->map_rendered) {
        return;
    }

    /* Calculate offset to center map on screen */
    int offset_x = (map->map_image_width - screen_w) / 2;
    int offset_y = (map->map_image_height - screen_h) / 2;

    /* Clamp to 0 if map is smaller than screen */
    if (offset_x < 0) offset_x = 0;
    if (offset_y < 0) offset_y = 0;

    fd2_map_render(map, screen, screen_w, screen_h, offset_x, offset_y);
}
