#ifndef FD2_MOD_LOADER_H
#define FD2_MOD_LOADER_H

#include "fd2/types.h"
#include "fd2/data/dat_parser.h"

#ifdef __cplusplus
extern "C" {
#endif

/* ---- MOD Loader ----
 * Scans MOD directories, parses mod.json metadata,
 * and manages MOD lifecycle.
 */

#define FD2_MOD_PATH_MAX 512
#define FD2_MOD_DATA_OVERRIDE_MAX 256

typedef struct {
    char dat_name[64];
    int  resource_index;
    const u8* override_data;
    u32  override_size;
} fd2_mod_data_override_t;

struct fd2_mod_mgr {
    fd2_mod_t*         mods[FD2_MAX_MODS];
    int                mod_count;
    char               mods_dir[FD2_MOD_PATH_MAX];

    fd2_dat_file_t     base_dat[16];
    int                base_dat_count;

    fd2_mod_data_override_t data_overrides[FD2_MOD_DATA_OVERRIDE_MAX];
    int                     data_override_count;
};

/* Initialize MOD manager */
int  fd2_mod_mgr_init(fd2_mod_mgr_t* mgr, const char* mods_dir);
void fd2_mod_mgr_shutdown(fd2_mod_mgr_t* mgr);

/* Load a single MOD from directory */
int  fd2_mod_mgr_load_mod(fd2_mod_mgr_t* mgr, const char* mod_dir);

/* Update all active MODs */
void fd2_mod_mgr_update(fd2_mod_mgr_t* mgr);

/* Register data override */
int  fd2_mod_mgr_override_data(fd2_mod_mgr_t* mgr,
                               const char* dat_name,
                               int resource_index,
                               const u8* data,
                               u32 size);

/* Get overridden data (returns NULL if not overridden) */
const u8* fd2_mod_mgr_get_override(const fd2_mod_mgr_t* mgr,
                                   const char* dat_name,
                                   int resource_index,
                                   u32* out_size);

#ifdef __cplusplus
}
#endif

#endif /* FD2_MOD_LOADER_H */
