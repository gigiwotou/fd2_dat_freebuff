#ifndef FD2_MAP_LOADER_H
#define FD2_MAP_LOADER_H

#include "fd2_decoder.h"
#include <stdbool.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

/* Maximum map dimensions (from original game) */
#define FD2_MAP_MAX_WIDTH 64
#define FD2_MAP_MAX_HEIGHT 64

/* Maximum tiles in a tileset */
#define FD2_MAX_TILES 512

/* Maximum characters on map */
#define FD2_MAX_MAP_CHARS 64

/* Character spawn position data (from FDFIELD.DAT)
 * Based on IDA sub_1088D analysis and actual data verification:
 * - 角色位置数据以2字节总数开头
 * - 每个角色6字节（IDA使用6字节步进）
 * - IDA只使用其中3字节：byte[0]=X, byte[2]=Y, byte[4]=portrait
 * 注意：IDA中X和Y是uint8_t（1字节），不是uint16_t
 * 注意：实际数据分析显示portrait在byte[4]，不是byte[3]
 */
typedef struct {
    uint8_t  x;           /* X coordinate (map tile) - byte[0] */
    uint8_t  y;           /* Y coordinate (map tile) - byte[2] */
    uint8_t  portrait_id; /* Portrait ID (0 = player character) - byte[4] */
} fd2_map_char_pos_t;

/* Character info from map control data (26 bytes per unit)
 * Structure:
 *   faction(1) + portrait(1) + race(1) + job(1) + level(1) = 5 bytes
 *   items(8) = 8 bytes
 *   spells(4) = 4 bytes
 *   spawn_turn(1) = 1 byte
 *   drop_item(4) = type(1) + content(3) = 4 bytes
 *   reserved(4) = 4 bytes
 * Total: 5 + 8 + 4 + 1 + 4 + 4 = 26 bytes
 */
typedef struct {
    uint8_t  faction;     /* 0=enemy, 1=NPC, 2=friendly */
    uint8_t  portrait_id; /* Portrait/portrait number */
    uint8_t  race_id;     /* Race ID */
    uint8_t  job_id;      /* Job/class ID */
    uint8_t  level;       /* Character level */
    uint8_t  items[8];    /* Item IDs (first 2 are weapon/armor, 0xFF=none) */
    uint8_t  spells[4];   /* Spell IDs (4 spells) */
    uint8_t  spawn_turn;  /* Turn to appear (255=reinforcement) */
    uint8_t  drop_type;   /* Drop item type: 0=item, 1=gold */
    uint8_t  drop_content[3]; /* Drop item content (3 bytes) */
    uint8_t  reserved[4]; /* Reserved bytes */
} fd2_map_char_info_t;

/* Map scene data parsed from FDFIELD.DAT */
typedef struct {
    uint8_t  map_number;
    uint8_t  max_friendly;
    uint8_t  total_units;
    uint8_t  total_chars;      /* max_friendly + total_units */
    
    /* Character spawn positions */
    int char_pos_count;
    fd2_map_char_pos_t char_positions[FD2_MAX_MAP_CHARS];
    
    /* Character info (enemy/friendly units) */
    int char_info_count;
    fd2_map_char_info_t char_info[FD2_MAX_MAP_CHARS];
    
    bool loaded;
} fd2_map_scene_t;

/* Tile data structure (4 bytes per tile from layout) */
typedef struct {
    uint16_t terrain_id;    /* Terrain ID (10 bits: 0-1023) */
    uint16_t event_id;      /* Event/treasure chest ID */
    uint8_t  terrain_flag;  /* Terrain variant flag (byte[1] & 0x03) */
    uint8_t  event_type;    /* Event type (byte[2] & 0x1F) */
} fd2_map_tile_t;

/* Tile image data */
typedef struct {
    int width;              /* Tile width in pixels */
    int height;             /* Tile height in pixels */
    u8* pixels;             /* Pixel data (width * height bytes, palette indices) */
    bool valid;             /* True if tile was successfully decoded */
} fd2_tile_image_t;

/* Loaded map data */
typedef struct {
    int width;                          /* Map width in tiles */
    int height;                         /* Map height in tiles */
    int tile_size;                      /* Tile size in pixels (24x24 per tile) */
    fd2_map_tile_t tiles[FD2_MAP_MAX_HEIGHT][FD2_MAP_MAX_WIDTH];
    
    /* Tileset */
    int tileset_count;                  /* Number of tiles in tileset */
    fd2_tile_image_t tile_images[FD2_MAX_TILES];
    
    /* Palette (768 bytes, 6-bit RGB) */
    u8 palette[FD2_PALETTE_BYTES];
    bool palette_loaded;
    
    /* Rendering buffer (pre-rendered map image) */
    u8* map_image;                      /* width*tile_size * height*tile_size bytes */
    int map_image_width;
    int map_image_height;
    bool map_rendered;
    
    /* Map ID and terrain set ID */
    int map_id;
    int terrain_set_id;
    
    /* Scene data (characters, events) */
    fd2_map_scene_t scene;
    
    bool loaded;
} fd2_map_t;

/* ---- Map Loading ---- */

/*
 * Initialize map structure.
 */
int fd2_map_init(fd2_map_t* map);

/*
 * Load map from FDFIELD.DAT and FDSHAP.DAT files.
 * 
 * map_id: which map to load (0-32)
 * fdfield_path: path to FDFIELD.DAT
 * fdshap_path: path to FDSHAP.DAT
 * fdother_path: path to FDOTHER.DAT (for global palette)
 * 
 * Returns 0 on success, -1 on failure.
 */
int fd2_map_load_from_dat(fd2_map_t* map, int map_id,
                          const char* fdfield_path,
                          const char* fdshap_path,
                          const char* fdother_path);

/*
 * Free map resources.
 */
void fd2_map_free(fd2_map_t* map);

/* ---- Map Rendering ---- */

/*
 * Render the loaded map to screen buffer.
 * 
 * screen: screen buffer (screen_w * screen_h bytes)
 * screen_w, screen_h: screen dimensions (320x200)
 * offset_x, offset_y: scroll offset in pixels
 * 
 * This function renders the map with the correct palette,
 * using the tile images loaded from FDSHAP.DAT.
 */
void fd2_map_render(const fd2_map_t* map,
                    u8* screen, int screen_w, int screen_h,
                    int offset_x, int offset_y);

/*
 * Render map without scroll (fit to screen).
 * Centers the map on screen.
 */
void fd2_map_render_centered(const fd2_map_t* map,
                              u8* screen, int screen_w, int screen_h);

#ifdef __cplusplus
}
#endif

#endif /* FD2_MAP_LOADER_H */
