#ifndef FD2_MAP_H
#define FD2_MAP_H

#include "fd2_decoder.h"
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

/* ========================================================================
 * FD2 Map System
 * 
 * Supports loading map data from JSON files and rendering tile-based maps.
 * Map files are stored in the "scenes/" directory as scene_XX.json.
 * ======================================================================== */

/* Maximum map dimensions */
#define FD2_MAP_MAX_WIDTH 64
#define FD2_MAP_MAX_HEIGHT 64

/* Default tile size in pixels */
#define FD2_TILE_SIZE 16

/* ---- Tile Types ---- */
typedef enum {
    TILE_EMPTY = 0,       /* Empty/transparent */
    TILE_GRASS = 1,       /* Grass terrain */
    TILE_WATER = 2,       /* Water */
    TILE_MOUNTAIN = 3,    /* Mountain/rock */
    TILE_FOREST = 4,      /* Forest/trees */
    TILE_PATH = 5,        /* Path/road */
    TILE_BUILDING = 6,    /* Building/structure */
    TILE_BRIDGE = 7,      /* Bridge */
    TILE_SPECIAL_8 = 8,   /* Special tile 8 */
    TILE_SPECIAL_9 = 9,   /* Special tile 9 */
    TILE_SPECIAL_10 = 10, /* Special tile 10 */
    TILE_FLAG_128 = 128,  /* Flag/marker (0x80) */
    TILE_FLAG_130 = 130,  /* Flag/marker (0x82) */
} tile_type_t;

/* ---- Map Data ---- */
typedef struct {
    int width;                    /* Map width in tiles */
    int height;                   /* Map height in tiles */
    int tile_size;                /* Tile size in pixels */
    u8 tiles[FD2_MAP_MAX_HEIGHT][FD2_MAP_MAX_WIDTH]; /* Tile grid */
    bool loaded;                  /* Whether map data is loaded */
} fd2_map_data_t;

/* ---- Map Renderer ---- */
typedef struct {
    fd2_map_data_t map;          /* Map data */
    int scroll_x;                /* Horizontal scroll offset */
    int scroll_y;                /* Vertical scroll offset */
    bool use_custom_palette;     /* Whether to use custom palette */
    u8 tile_colors[256];         /* Color index for each tile type */
} fd2_map_renderer_t;

/* ---- Map Loader ---- */

/*
 * Initialize map data structure.
 */
int fd2_map_init(fd2_map_data_t* map);

/*
 * Load map from JSON file.
 * Returns 0 on success, -1 on failure.
 */
int fd2_map_load_from_json(fd2_map_data_t* map, const char* file_path);

/*
 * Load map by scene ID (searches in scenes/ directory).
 * Returns 0 on success, -1 if file not found.
 */
int fd2_map_load_by_scene_id(fd2_map_data_t* map, int scene_id);

/*
 * Export map data to JSON file.
 * Returns 0 on success, -1 on failure.
 */
int fd2_map_export_to_json(const fd2_map_data_t* map, int scene_id, 
                            const char* description, const char* output_path);

/* ---- Map Renderer ---- */

/*
 * Initialize map renderer.
 */
int fd2_map_renderer_init(fd2_map_renderer_t* renderer);

/*
 * Set map data for renderer.
 */
void fd2_map_renderer_set_map(fd2_map_renderer_t* renderer, const fd2_map_data_t* map);

/*
 * Render map to screen buffer.
 * screen: screen buffer (width * height bytes)
 * screen_w, screen_h: screen dimensions
 */
void fd2_map_renderer_render(const fd2_map_renderer_t* renderer, 
                              u8* screen, int screen_w, int screen_h);

/*
 * Set tile color mapping.
 * tile_type: tile type index (0-255)
 * color_index: color index in palette (0-255)
 */
void fd2_map_renderer_set_tile_color(fd2_map_renderer_t* renderer, 
                                      u8 tile_type, u8 color_index);

/*
 * Setup default tile colors for battlefield map.
 */
void fd2_map_renderer_setup_default_colors(fd2_map_renderer_t* renderer);

/* ---- Utility ---- */

/*
 * Get tile type name for display.
 */
const char* fd2_map_get_tile_type_name(u8 tile_type);

#ifdef __cplusplus
}
#endif

#endif /* FD2_MAP_H */
