/**
 * FD2 Scene Data Loader/Exporter
 * 
 * Loads scene data from JSON files and exports to JSON format.
 * Uses a simple JSON parser (no external dependencies).
 */

#include "fd2_scene_loader.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>

/* ========================================================================
 * Simple JSON Parser (minimal implementation for scene format)
 * ======================================================================== */

typedef struct {
    const char* src;
    size_t pos;
    size_t len;
} json_parser_t;

static void json_skip_whitespace(json_parser_t* p) {
    while (p->pos < p->len && isspace(p->src[p->pos])) {
        p->pos++;
    }
}

static bool json_expect_char(json_parser_t* p, char c) {
    json_skip_whitespace(p);
    if (p->pos < p->len && p->src[p->pos] == c) {
        p->pos++;
        return true;
    }
    return false;
}

static bool json_parse_string(json_parser_t* p, char* out, size_t out_size) {
    json_skip_whitespace(p);
    if (!json_expect_char(p, '"')) return false;
    
    size_t i = 0;
    while (p->pos < p->len && i < out_size - 1) {
        char c = p->src[p->pos];
        if (c == '"') {
            p->pos++;
            out[i] = '\0';
            return true;
        }
        if (c == '\\') {
            p->pos++;
            if (p->pos < p->len) {
                char esc = p->src[p->pos];
                switch (esc) {
                    case '"': out[i++] = '"'; break;
                    case '\\': out[i++] = '\\'; break;
                    case 'n': out[i++] = '\n'; break;
                    case 't': out[i++] = '\t'; break;
                    default: out[i++] = esc; break;
                }
            }
        } else {
            out[i++] = c;
        }
        p->pos++;
    }
    out[i] = '\0';
    return false;
}

static bool json_parse_int(json_parser_t* p, int* out) {
    json_skip_whitespace(p);
    if (p->pos >= p->len) return false;
    
    char* end;
    long val = strtol(p->src + p->pos, &end, 0);  /* Base 0 for hex support */
    if (end == p->src + p->pos) return false;
    
    *out = (int)val;
    p->pos = (size_t)(end - p->src);
    return true;
}

/* ========================================================================
 * Scene Loader Implementation
 * ======================================================================== */

int scene_loader_init(scene_loader_t* loader) {
    if (!loader) return -1;
    memset(loader, 0, sizeof(scene_loader_t));
    return 0;
}

static bool parse_command_array(json_parser_t* p, scene_file_data_t* scene) {
    /* Skip opening [ */
    json_skip_whitespace(p);
    if (!json_expect_char(p, '[')) return false;
    
    int cmd_idx = 0;
    json_skip_whitespace(p);
    
    while (p->pos < p->len && p->src[p->pos] != ']') {
        if (cmd_idx >= SCENE_LOADER_MAX_COMMANDS) {
            printf("[SCENE_LOADER] WARNING: too many commands (max %d)\n", 
                   SCENE_LOADER_MAX_COMMANDS);
            break;
        }
        
        /* Expect { */
        json_skip_whitespace(p);
        if (!json_expect_char(p, '{')) break;
        
        scene_cmd_entry_t* cmd = &scene->commands[cmd_idx];
        memset(cmd, 0, sizeof(*cmd));
        
        /* Parse command fields */
        json_skip_whitespace(p);
        while (p->pos < p->len && p->src[p->pos] != '}') {
            char key[64];
            if (!json_parse_string(p, key, sizeof(key))) break;
            
            json_skip_whitespace(p);
            if (!json_expect_char(p, ':')) break;
            
            if (strcmp(key, "type") == 0) {
                int val;
                if (json_parse_int(p, &val)) {
                    cmd->type = (u8)val;
                }
            } else if (strcmp(key, "params") == 0) {
                /* Parse array */
                json_skip_whitespace(p);
                if (json_expect_char(p, '[')) {
                    int param_idx = 0;
                    json_skip_whitespace(p);
                    while (p->pos < p->len && p->src[p->pos] != ']') {
                        int val;
                        if (json_parse_int(p, &val) && param_idx < SCENE_LOADER_MAX_PARAMS) {
                            cmd->params[param_idx] = (u16)val;
                            param_idx++;
                        }
                        json_skip_whitespace(p);
                        if (p->src[p->pos] == ',') p->pos++;
                        json_skip_whitespace(p);
                    }
                    cmd->param_count = (u8)param_idx;
                    json_expect_char(p, ']');
                }
            } else if (strcmp(key, "comment") == 0) {
                /* Skip comment field */
                char dummy[256];
                json_parse_string(p, dummy, sizeof(dummy));
            }
            
            json_skip_whitespace(p);
            if (p->src[p->pos] == ',') p->pos++;
            json_skip_whitespace(p);
        }
        
        json_expect_char(p, '}');
        cmd_idx++;
        
        json_skip_whitespace(p);
        if (p->src[p->pos] == ',') p->pos++;
        json_skip_whitespace(p);
    }
    
    scene->cmd_count = cmd_idx;
    json_expect_char(p, ']');
    return true;
}

int scene_loader_load_from_json(scene_loader_t* loader, const char* file_path) {
    if (!loader || !file_path) return -1;
    
    FILE* f = fopen(file_path, "r");
    if (!f) {
        printf("[SCENE_LOADER] Cannot open file: %s\n", file_path);
        return -1;
    }
    
    /* Get file size */
    fseek(f, 0, SEEK_END);
    long fsize = ftell(f);
    fseek(f, 0, SEEK_SET);
    
    if (fsize <= 0 || fsize > 1024 * 1024) {
        printf("[SCENE_LOADER] Invalid file size: %ld\n", fsize);
        fclose(f);
        return -1;
    }
    
    /* Read file */
    char* content = (char*)malloc(fsize + 1);
    if (!content) {
        fclose(f);
        return -1;
    }
    
    size_t read = fread(content, 1, fsize, f);
    content[read] = '\0';
    fclose(f);
    
    /* Parse JSON */
    json_parser_t parser;
    parser.src = content;
    parser.pos = 0;
    parser.len = read;
    
    scene_file_data_t* scene = &loader->scene_data;
    memset(scene, 0, sizeof(*scene));
    
    /* Parse opening { */
    json_skip_whitespace(&parser);
    if (!json_expect_char(&parser, '{')) {
        printf("[SCENE_LOADER] Invalid JSON format\n");
        free(content);
        return -1;
    }
    
    /* Parse fields */
    json_skip_whitespace(&parser);
    while (parser.pos < parser.len && parser.src[parser.pos] != '}') {
        char key[64];
        if (!json_parse_string(&parser, key, sizeof(key))) break;
        
        json_skip_whitespace(&parser);
        if (!json_expect_char(&parser, ':')) break;
        
        if (strcmp(key, "scene_id") == 0) {
            int val;
            json_parse_int(&parser, &val);
            scene->scene_id = val;
        } else if (strcmp(key, "description") == 0) {
            json_parse_string(&parser, scene->description, sizeof(scene->description));
        } else if (strcmp(key, "commands") == 0) {
            if (!parse_command_array(&parser, scene)) {
                printf("[SCENE_LOADER] Failed to parse commands\n");
                free(content);
                return -1;
            }
        }
        
        json_skip_whitespace(&parser);
        if (parser.src[parser.pos] == ',') parser.pos++;
        json_skip_whitespace(&parser);
    }
    
    free(content);
    
    if (scene->cmd_count == 0) {
        printf("[SCENE_LOADER] No commands loaded\n");
        return -1;
    }
    
    strncpy(loader->file_path, file_path, sizeof(loader->file_path) - 1);
    loader->loaded = true;
    
    printf("[SCENE_LOADER] Loaded scene %d from %s (%d commands)\n",
           scene->scene_id, file_path, scene->cmd_count);
    
    return 0;
}

int scene_loader_load_by_id(scene_loader_t* loader, int scene_id) {
    if (!loader) return -1;
    
    char path[512];
    snprintf(path, sizeof(path), "scenes/scene_%d.json", scene_id);
    
    return scene_loader_load_from_json(loader, path);
}

const u8* scene_loader_get_raw_data(scene_loader_t* loader, size_t* out_size) {
    if (!loader || !loader->loaded || !out_size) return NULL;
    
    static u8 raw_buffer[4096];
    size_t offset = 0;
    
    scene_file_data_t* scene = &loader->scene_data;
    
    /* Write command count */
    raw_buffer[offset++] = (u8)scene->cmd_count;
    
    /* Write each command */
    for (int i = 0; i < scene->cmd_count && offset < sizeof(raw_buffer) - 4; i++) {
        scene_cmd_entry_t* cmd = &scene->commands[i];
        
        raw_buffer[offset++] = cmd->type;
        raw_buffer[offset++] = cmd->param_count;
        
        for (int j = 0; j < cmd->param_count && offset < sizeof(raw_buffer) - 2; j++) {
            raw_buffer[offset++] = (u8)(cmd->params[j] & 0xFF);
            raw_buffer[offset++] = (u8)((cmd->params[j] >> 8) & 0xFF);
        }
    }
    
    *out_size = offset;
    return raw_buffer;
}

bool scene_loader_is_loaded(const scene_loader_t* loader) {
    return loader && loader->loaded;
}

int scene_loader_get_scene_id(const scene_loader_t* loader) {
    if (!loader || !loader->loaded) return -1;
    return loader->scene_data.scene_id;
}

void scene_loader_clear(scene_loader_t* loader) {
    if (loader) {
        memset(loader, 0, sizeof(scene_loader_t));
    }
}

/* ========================================================================
 * JSON Export Functions
 * ======================================================================== */

static const char* get_command_comment(u8 type) {
    int cmd_base = type & 0x7F;
    bool is_special = (type & 0x80) != 0;
    
    if (is_special) {
        switch (cmd_base) {
            case 0x00: return "Display";
            case 0x01: return "Animate/Move";
            case 0x02: return "Wait";
            case 0x03: return "Show/Hide";
            case 0x04: return "Initialize characters";
            case 0x05: return "Wait/Fade";
            case 0x80: return "Special 0x80";
            case 0x82: return "Special 0x82";
            case 0x84: return "Special 0x84";
            case 0x88: return "Special 0x88";
            default: return "Unknown special";
        }
    } else {
        switch (type) {
            case 0x00: return "Move";
            case 0x01: return "Wait/Delay";
            case 0x02: return "Fade";
            case 0x03: return "Show";
            case 0x04: return "Effect";
            case 0x05: return "Position";
            case 0x06: return "Unknown";
            default: return "Regular";
        }
    }
}

int scene_loader_export_to_json(const u8* raw_data, size_t raw_size,
                                 int scene_id, const char* description,
                                 const char* output_path) {
    if (!raw_data || !output_path || raw_size < 1) return -1;
    
    FILE* f = fopen(output_path, "w");
    if (!f) {
        printf("[SCENE_LOADER] Cannot create file: %s\n", output_path);
        return -1;
    }
    
    size_t offset = 0;
    u8 cmd_count = raw_data[offset++];
    
    fprintf(f, "{\n");
    fprintf(f, "  \"scene_id\": %d,\n", scene_id);
    fprintf(f, "  \"description\": \"%s\",\n", description ? description : "Scene");
    fprintf(f, "  \"command_count\": %d,\n", cmd_count);
    fprintf(f, "  \"commands\": [\n");
    
    int written = 0;
    while (offset < raw_size && written < cmd_count) {
        if (written > 0) fprintf(f, ",\n");
        
        u8 cmd_type = raw_data[offset++];
        u8 param_count = raw_data[offset++];
        
        fprintf(f, "    {\n");
        fprintf(f, "      \"type\": 0x%02X,\n", cmd_type);
        fprintf(f, "      \"comment\": \"%s\",\n", get_command_comment(cmd_type));
        fprintf(f, "      \"params\": [");
        
        for (int i = 0; i < param_count && offset + 1 < raw_size; i++) {
            u16 param = (u16)(raw_data[offset] | (raw_data[offset + 1] << 8));
            offset += 2;
            
            if (i > 0) fprintf(f, ", ");
            fprintf(f, "%d", param);
        }
        
        fprintf(f, "]\n");
        fprintf(f, "    }");
        
        written++;
    }
    
    fprintf(f, "\n  ]\n");
    fprintf(f, "}\n");
    
    fclose(f);
    
    printf("[SCENE_LOADER] Exported scene %d to %s (%d commands)\n",
           scene_id, output_path, written);
    
    return 0;
}
