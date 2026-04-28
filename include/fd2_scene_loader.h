#ifndef FD2_SCENE_LOADER_H
#define FD2_SCENE_LOADER_H

#include "fd2_decoder.h"
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

/* ========================================================================
 * FD2 Scene Data Loader/Exporter
 * 
 * Supports loading scene data from JSON files and exporting to JSON.
 * Scene files are stored in the "scenes/" directory.
 * ======================================================================== */

/* Maximum parameters per command */
#define SCENE_LOADER_MAX_PARAMS 16

/* Maximum commands per scene */
#define SCENE_LOADER_MAX_COMMANDS 256

/* ---- Scene Command (parsed from JSON) ---- */
typedef struct {
    u8 type;                        /* Command type (0x80 = special) */
    u8 param_count;                 /* Number of parameters */
    u16 params[SCENE_LOADER_MAX_PARAMS]; /* Parameters */
} scene_cmd_entry_t;

/* ---- Scene Data (loaded from JSON) ---- */
typedef struct {
    int scene_id;                   /* Scene ID */
    char description[256];          /* Scene description */
    int cmd_count;                  /* Number of commands */
    scene_cmd_entry_t commands[SCENE_LOADER_MAX_COMMANDS]; /* Commands */
} scene_file_data_t;

/* ---- Scene Loader State ---- */
typedef struct {
    scene_file_data_t scene_data;   /* Loaded scene data */
    bool loaded;                    /* Whether data is loaded */
    char file_path[512];            /* Path to loaded file */
} scene_loader_t;

/* ---- Lifecycle ---- */

/*
 * Initialize scene loader.
 */
int scene_loader_init(scene_loader_t* loader);

/*
 * Load scene from JSON file.
 * Returns 0 on success, -1 on failure.
 */
int scene_loader_load_from_json(scene_loader_t* loader, const char* file_path);

/*
 * Load scene by scene_id (searches in scenes/ directory).
 * Returns 0 on success, -1 if file not found.
 */
int scene_loader_load_by_id(scene_loader_t* loader, int scene_id);

/*
 * Export raw scene data to JSON file.
 * Returns 0 on success, -1 on failure.
 */
int scene_loader_export_to_json(const u8* raw_data, size_t raw_size, 
                                 int scene_id, const char* description,
                                 const char* output_path);

/*
 * Convert loaded scene data to raw binary format.
 * Returns pointer to static buffer containing raw data.
 */
const u8* scene_loader_get_raw_data(scene_loader_t* loader, size_t* out_size);

/*
 * Check if loader has valid data.
 */
bool scene_loader_is_loaded(const scene_loader_t* loader);

/*
 * Get loaded scene ID.
 */
int scene_loader_get_scene_id(const scene_loader_t* loader);

/*
 * Clear loaded data.
 */
void scene_loader_clear(scene_loader_t* loader);

#ifdef __cplusplus
}
#endif

#endif /* FD2_SCENE_LOADER_H */
