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
    int tile_size;                      /* Tile size in pixels (typically 64) */
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
