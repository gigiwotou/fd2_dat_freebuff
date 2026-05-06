/**
 * SDL2 File System Platform Implementation
 * File I/O operations using SDL2_RWops and stdio.
 */

#define _GNU_SOURCE
#include "fd2/platform_file.h"
#include "fd2/types.h"
#include <SDL2/SDL.h>
#include <stdlib.h>
#include <string.h>
#include <stdio.h>

#ifdef _WIN32
#include <windows.h>
#include <direct.h>
#define PATH_SEP '\\'
#define MAX_PATH_LEN 512
#else
#include <unistd.h>
#include <limits.h>
#include <dirent.h>
#define PATH_SEP '/'
#define MAX_PATH_LEN PATH_MAX
#endif

struct fd2_filesys {
    char base_dir[MAX_PATH_LEN];
};

static int sdl_filesys_init(fd2_filesys_t** out_fs, const char* base_dir) {
    fd2_filesys_t* fs = (fd2_filesys_t*)calloc(1, sizeof(fd2_filesys_t));
    if (!fs) return -1;

    if (base_dir && base_dir[0]) {
        snprintf(fs->base_dir, sizeof(fs->base_dir), "%s", base_dir);
    } else {
#ifdef _WIN32
        char exe_path[MAX_PATH_LEN];
        DWORD len = GetModuleFileNameA(NULL, exe_path, sizeof(exe_path));
        if (len > 0 && len < sizeof(exe_path)) {
            char* sep = strrchr(exe_path, PATH_SEP);
            if (sep) {
                *(sep + 1) = '\0';
                snprintf(fs->base_dir, sizeof(fs->base_dir), "%s", exe_path);
            } else {
                snprintf(fs->base_dir, sizeof(fs->base_dir), ".");
            }
        } else {
            snprintf(fs->base_dir, sizeof(fs->base_dir), ".");
        }
#else
        ssize_t len = readlink("/proc/self/exe", fs->base_dir, sizeof(fs->base_dir) - 1);
        if (len > 0) {
            fs->base_dir[len] = '\0';
            char* sep = strrchr(fs->base_dir, PATH_SEP);
            if (sep) *(sep + 1) = '\0';
        } else {
            snprintf(fs->base_dir, sizeof(fs->base_dir), ".");
        }
#endif
    }

    *out_fs = fs;
    return 0;
}

static void sdl_filesys_shutdown(fd2_filesys_t* fs) {
    free(fs);
}

static void* sdl_filesys_load_file(fd2_filesys_t* fs, const char* path, u32* out_size) {
    SDL_RWops* rw = SDL_RWFromFile(path, "rb");
    if (!rw) return NULL;

    s64 size = SDL_RWsize(rw);
    if (size <= 0) {
        SDL_RWclose(rw);
        return NULL;
    }

    void* data = malloc((size_t)size + 1);
    if (!data) {
        SDL_RWclose(rw);
        return NULL;
    }

    s64 bytes_read = SDL_RWread(rw, data, 1, (size_t)size);
    SDL_RWclose(rw);

    if (bytes_read != size) {
        free(data);
        return NULL;
    }

    ((u8*)data)[size] = '\0';
    if (out_size) *out_size = (u32)size;
    return data;
}

static void sdl_filesys_free_file(fd2_filesys_t* fs, void* data) {
    (void)fs;
    free(data);
}

static int sdl_filesys_save_file(fd2_filesys_t* fs, const char* path, const void* data, u32 size) {
    (void)fs;
    SDL_RWops* rw = SDL_RWFromFile(path, "wb");
    if (!rw) return -1;

    s64 written = SDL_RWwrite(rw, data, 1, size);
    SDL_RWclose(rw);

    return (written == size) ? 0 : -1;
}

static bool sdl_filesys_file_exists(fd2_filesys_t* fs, const char* path) {
    (void)fs;
    SDL_RWops* rw = SDL_RWFromFile(path, "rb");
    if (rw) {
        SDL_RWclose(rw);
        return true;
    }
    return false;
}

static const char* sdl_filesys_get_base_dir(fd2_filesys_t* fs) {
    return fs->base_dir;
}

static char* sdl_filesys_make_path(fd2_filesys_t* fs, const char* subdir, const char* filename) {
    static char path_buf[1024];

    if (subdir && subdir[0]) {
        snprintf(path_buf, sizeof(path_buf), "%s/%s/%s", fs->base_dir, subdir, filename);
    } else {
        snprintf(path_buf, sizeof(path_buf), "%s/%s", fs->base_dir, filename);
    }

    return path_buf;
}

static int sdl_filesys_list_files(fd2_filesys_t* fs, const char* dir, char*** out_files, int* out_count) {
    (void)fs;
#ifdef _WIN32
    char search_path[512];
    snprintf(search_path, sizeof(search_path), "%s\\*", dir);

    WIN32_FIND_DATAA find_data;
    HANDLE h = FindFirstFileA(search_path, &find_data);
    if (h == INVALID_HANDLE_VALUE) return -1;

    int capacity = 32;
    int count = 0;
    char** files = (char**)malloc(capacity * sizeof(char*));

    do {
        if (find_data.cFileName[0] == '.') continue;
        if (count >= capacity) {
            capacity *= 2;
            files = (char**)realloc(files, capacity * sizeof(char*));
        }
        files[count] = _strdup(find_data.cFileName);
        count++;
    } while (FindNextFileA(h, &find_data));

    FindClose(h);
    *out_files = files;
    *out_count = count;
    return 0;
#else
    DIR* d = opendir(dir);
    if (!d) return -1;

    int capacity = 32;
    int count = 0;
    char** files = (char**)malloc(capacity * sizeof(char*));

    struct dirent* entry;
    while ((entry = readdir(d)) != NULL) {
        if (entry->d_name[0] == '.') continue;
        if (count >= capacity) {
            capacity *= 2;
            files = (char**)realloc(files, capacity * sizeof(char*));
        }
        files[count] = strdup(entry->d_name);
        count++;
    }

    closedir(d);
    *out_files = files;
    *out_count = count;
    return 0;
#endif
}

static void sdl_filesys_free_file_list(fd2_filesys_t* fs, char** files, int count) {
    (void)fs;
    for (int i = 0; i < count; i++) {
        free(files[i]);
    }
    free(files);
}

static const fd2_filesys_iface_t g_sdl_filesys_iface = {
    .init             = sdl_filesys_init,
    .shutdown         = sdl_filesys_shutdown,
    .load_file        = sdl_filesys_load_file,
    .free_file        = sdl_filesys_free_file,
    .save_file        = sdl_filesys_save_file,
    .file_exists      = sdl_filesys_file_exists,
    .get_base_dir     = sdl_filesys_get_base_dir,
    .make_path        = sdl_filesys_make_path,
    .list_files       = sdl_filesys_list_files,
    .free_file_list   = sdl_filesys_free_file_list,
};

const fd2_filesys_iface_t* fd2_platform_get_filesys(void) {
    return &g_sdl_filesys_iface;
}
