#ifndef FD2_PLATFORM_FILE_H
#define FD2_PLATFORM_FILE_H

#include "fd2/types.h"

#ifdef __cplusplus
extern "C" {
#endif

/* ---- File Interface ---- */

typedef struct {
    int (*init)(fd2_filesys_t** out_fs, const char* base_dir);
    void (*shutdown)(fd2_filesys_t* fs);

    void* (*load_file)(fd2_filesys_t* fs, const char* path, u32* out_size);
    void (*free_file)(fd2_filesys_t* fs, void* data);

    int (*save_file)(fd2_filesys_t* fs, const char* path, const void* data, u32 size);
    bool (*file_exists)(fd2_filesys_t* fs, const char* path);

    const char* (*get_base_dir)(fd2_filesys_t* fs);
    char* (*make_path)(fd2_filesys_t* fs, const char* subdir, const char* filename);

    int (*list_files)(fd2_filesys_t* fs, const char* dir, char*** out_files, int* out_count);
    void (*free_file_list)(fd2_filesys_t* fs, char** files, int count);
} fd2_filesys_iface_t;

/* Get the platform filesystem interface (implemented by platform/sdl_file.c) */
const fd2_filesys_iface_t* fd2_platform_get_filesys(void);

#ifdef __cplusplus
}
#endif

#endif /* FD2_PLATFORM_FILE_H */
