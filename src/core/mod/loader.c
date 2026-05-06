/**
 * MOD Loader Implementation
 * Scans MOD directories, parses metadata, manages lifecycle.
 * Simple JSON-like parsing (no external dependency).
 */

#define _GNU_SOURCE
#include "fd2/mod/loader.h"
#include "fd2/platform_file.h"
#include <stdlib.h>
#include <string.h>
#include <stdio.h>

static int parse_json_string(const char* json, const char* key, char* out, int out_size) {
    if (!json || !key || !out) return -1;

    char search_key[128];
    snprintf(search_key, sizeof(search_key), "\"%s\"", key);

    const char* pos = strstr(json, search_key);
    if (!pos) return -1;

    pos += strlen(search_key);
    while (*pos && (*pos == ' ' || *pos == ':' || *pos == '\t')) pos++;

    if (*pos != '"') return -1;
    pos++;

    int i = 0;
    while (*pos && *pos != '"' && i < out_size - 1) {
        out[i++] = *pos++;
    }
    out[i] = '\0';

    return 0;
}

static int load_mod_json(fd2_mod_t* mod, const char* mod_dir) {
    const fd2_filesys_iface_t* fs = fd2_platform_get_filesys();
    if (!fs) return -1;

    fd2_filesys_t* f = NULL;
    if (fs->init(&f, ".") < 0) return -1;

    char path[FD2_MOD_PATH_MAX];
    snprintf(path, sizeof(path), "%s/mod.json", mod_dir);

    u32 size = 0;
    char* json = (char*)fs->load_file(f, path, &size);
    fs->shutdown(f);

    if (!json || size == 0) {
        fprintf(stderr, "mod_loader: cannot load mod.json from %s\n", mod_dir);
        return -1;
    }

    parse_json_string(json, "id", mod->id, sizeof(mod->id));
    parse_json_string(json, "name", mod->name, sizeof(mod->name));
    parse_json_string(json, "version", mod->version, sizeof(mod->version));
    parse_json_string(json, "author", mod->author, sizeof(mod->author));

    free(json);
    return 0;
}

int fd2_mod_mgr_init(fd2_mod_mgr_t* mgr, const char* mods_dir) {
    if (!mgr) return -1;

    memset(mgr, 0, sizeof(*mgr));

    if (mods_dir && mods_dir[0]) {
        snprintf(mgr->mods_dir, sizeof(mgr->mods_dir), "%s", mods_dir);
    } else {
        snprintf(mgr->mods_dir, sizeof(mgr->mods_dir), "mods");
    }

    mgr->mod_count = 0;
    mgr->base_dat_count = 0;
    mgr->data_override_count = 0;

    return 0;
}

void fd2_mod_mgr_shutdown(fd2_mod_mgr_t* mgr) {
    if (!mgr) return;

    for (int i = 0; i < mgr->mod_count; i++) {
        if (mgr->mods[i] && mgr->mods[i]->shutdown) {
            mgr->mods[i]->shutdown();
        }
        if (mgr->mods[i]) {
            free(mgr->mods[i]);
        }
    }

    for (int i = 0; i < mgr->base_dat_count; i++) {
        fd2_dat_free(&mgr->base_dat[i]);
    }

    memset(mgr, 0, sizeof(*mgr));
}

int fd2_mod_mgr_load_mod(fd2_mod_mgr_t* mgr, const char* mod_dir) {
    if (!mgr || !mod_dir || mgr->mod_count >= FD2_MAX_MODS) return -1;

    fd2_mod_t* mod = (fd2_mod_t*)calloc(1, sizeof(fd2_mod_t));
    if (!mod) return -1;

    if (load_mod_json(mod, mod_dir) < 0) {
        free(mod);
        return -1;
    }

    if (mod->id[0] == '\0') {
        snprintf(mod->id, sizeof(mod->id), "mod_%d", mgr->mod_count);
    }
    if (mod->name[0] == '\0') {
        snprintf(mod->name, sizeof(mod->name), "%s", mod->id);
    }

    fprintf(stderr, "mod_loader: loaded MOD '%s' (%s) by %s\n",
            mod->name, mod->version, mod->author);

    mgr->mods[mgr->mod_count] = mod;
    mgr->mod_count++;

    if (mod->init) {
        if (mod->init() < 0) {
            fprintf(stderr, "mod_loader: MOD '%s' init failed\n", mod->name);
            mgr->mod_count--;
            mgr->mods[mgr->mod_count] = NULL;
            free(mod);
            return -1;
        }
    }

    return 0;
}

void fd2_mod_mgr_update(fd2_mod_mgr_t* mgr) {
    if (!mgr) return;

    for (int i = 0; i < mgr->mod_count; i++) {
        if (mgr->mods[i] && mgr->mods[i]->update) {
            mgr->mods[i]->update();
        }
    }
}

int fd2_mod_mgr_override_data(fd2_mod_mgr_t* mgr,
                              const char* dat_name,
                              int resource_index,
                              const u8* data,
                              u32 size) {
    if (!mgr || !dat_name || !data || size == 0) return -1;
    if (mgr->data_override_count >= FD2_MOD_DATA_OVERRIDE_MAX) return -1;

    fd2_mod_data_override_t* ov = &mgr->data_overrides[mgr->data_override_count];
    snprintf(ov->dat_name, sizeof(ov->dat_name), "%s", dat_name);
    ov->resource_index = resource_index;
    ov->override_data = data;
    ov->override_size = size;

    mgr->data_override_count++;
    return mgr->data_override_count - 1;
}

const u8* fd2_mod_mgr_get_override(const fd2_mod_mgr_t* mgr,
                                   const char* dat_name,
                                   int resource_index,
                                   u32* out_size) {
    if (!mgr || !dat_name) return NULL;

    for (int i = mgr->data_override_count - 1; i >= 0; i--) {
        const fd2_mod_data_override_t* ov = &mgr->data_overrides[i];
        if (strcmp(ov->dat_name, dat_name) == 0 && ov->resource_index == resource_index) {
            if (out_size) *out_size = ov->override_size;
            return ov->override_data;
        }
    }

    return NULL;
}
