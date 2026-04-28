/**
 * FD2 Map System Implementation
 * 
 * Loads map data from JSON files and renders tile-based maps.
 * Uses a simple JSON parser (no external dependencies).
 */

#include "fd2_map.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>

/* ========================================================================
 * Simple JSON Parser (minimal implementation for map format)
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
    long val = strtol(p->src + p->pos, &end, 0);
    if (end == p->src + p->pos) return false;
    
    *out = (int)val;
    p->pos = (size_t)(end - p->src);
    return true;
}

/* ========================================================================
 * Map Data Implementation
 * ======================================================================== */

int fd2_map_init(fd2_map_data_t* map) {
    if (!map) return -1;
    memset(map, 0, sizeof(fd2_map_data_t));
    map->tile_size = FD2_TILE_SIZE;
    return 0;
}

static bool parse_tile_array(json_parser_t* p, u8* tiles, int width, int height) {
    json_skip_whitespace(p);
    if (!json_expect_char(p, '[')) return false;
    
    int row = 0;
    json_skip_whitespace(p);
    
    while (p->pos < p->len && p->src[p->pos] != ']' && row < height) {
        /* Expect row array [ */
        if (p->src[p->pos] == '[') {
            json_expect_char(p, '[');
            
            int col = 0;
            json_skip_whitespace(p);
            while (p->pos < p->len && p->src[p->pos] != ']' && col < width) {
                int val;
                if (json_parse_int(p, &val)) {
                    tiles[row * width + col] = (u8)(val & 0xFF);
                    col++;
                }
                json_skip_whitespace(p);
                if (p->src[p->pos] == ',') p->pos++;
                json_skip_whitespace(p);
            }
            json_expect_char(p, ']');
            row++;
        }
        
        json_skip_whitespace(p);
        if (p->src[p->pos] == ',') p->pos++;
        json_skip_whitespace(p);
    }
    
    json_expect_char(p, ']');
    return true;
}

static bool parse_map_data(json_parser_t* p, fd2_map_data_t* map) {
    json_skip_whitespace(p);
    if (!json_expect_char(p, '{')) return false;
    
    json_skip_whitespace(p);
    while (p->pos < p->len && p->src[p->pos] != '}') {
        char key[64];
        if (!json_parse_string(p, key, sizeof(key))) break;
        
        json_skip_whitespace(p);
        if (!json_expect_char(p, ':')) break;
        
        if (strcmp(key, "width") == 0) {
            json_parse_int(p, &map->width);
        } else if (strcmp(key, "height") == 0) {
            json_parse_int(p, &map->height);
        } else if (strcmp(key, "tile_size") == 0) {
            json_parse_int(p, &map->tile_size);
        } else if (strcmp(key, "tiles") == 0) {
            if (map->width > 0 && map->height > 0) {
                if (!parse_tile_array(p, &map->tiles[0][0], map->width, map->height)) {
                    return false;
                }
            }
        }
        
        json_skip_whitespace(p);
        if (p->src[p->pos] == ',') p->pos++;
        json_skip_whitespace(p);
    }
    
    json_expect_char(p, '}');
    return true;
}

int fd2_map_load_from_json(fd2_map_data_t* map, const char* file_path) {
    if (!map || !file_path) return -1;
    
    FILE* f = fopen(file_path, "r");
    if (!f) {
        printf("[MAP] Cannot open file: %s\n", file_path);
        return -1;
    }
    
    fseek(f, 0, SEEK_END);
    long fsize = ftell(f);
    fseek(f, 0, SEEK_SET);
    
    if (fsize <= 0 || fsize > 1024 * 1024) {
        printf("[MAP] Invalid file size: %ld\n", fsize);
        fclose(f);
        return -1;
    }
    
    char* content = (char*)malloc(fsize + 1);
    if (!content) {
        fclose(f);
        return -1;
    }
    
    size_t read = fread(content, 1, fsize, f);
    content[read] = '\0';
    fclose(f);
    
    json_parser_t parser;
    parser.src = content;
    parser.pos = 0;
    parser.len = read;
    
    json_skip_whitespace(&parser);
    if (!json_expect_char(&parser, '{')) {
        printf("[MAP] Invalid JSON format\n");
        free(content);
        return -1;
    }
    
    while (parser.pos < parser.len && parser.src[parser.pos] != '}') {
        char key[64];
        if (!json_parse_string(&parser, key, sizeof(key))) break;
        
        json_skip_whitespace(&parser);
        if (!json_expect_char(&parser, ':')) break;
        
        if (strcmp(key, "map_data") == 0) {
            if (!parse_map_data(&parser, map)) {
                printf("[MAP] Failed to parse map_data\n");
                free(content);
                return -1;
            }
            map->loaded = true;
            break;
        } else {
            /* Skip other fields (scene_id, description, etc.) */
            json_skip_whitespace(&parser);
            if (parser.src[parser.pos] == '{') {
                int depth = 1;
                parser.pos++;
                while (parser.pos < parser.len && depth > 0) {
                    if (parser.src[parser.pos] == '{') depth++;
                    if (parser.src[parser.pos] == '}') depth--;
                    parser.pos++;
                }
            } else if (parser.src[parser.pos] == '[') {
                int depth = 1;
                parser.pos++;
                while (parser.pos < parser.len && depth > 0) {
                    if (parser.src[parser.pos] == '[') depth++;
                    if (parser.src[parser.pos] == ']') depth--;
                    parser.pos++;
                }
            } else {
                /* Skip string/number */
                while (parser.pos < parser.len && parser.src[parser.pos] != ',' && parser.src[parser.pos] != '}') {
                    parser.pos++;
                }
            }
        }
        
        json_skip_whitespace(&parser);
        if (parser.src[parser.pos] == ',') parser.pos++;
        json_skip_whitespace(&parser);
    }
    
    free(content);
    
    if (!map->loaded || map->width <= 0 || map->height <= 0) {
        printf("[MAP] No valid map data loaded\n");
        return -1;
    }
    
    printf("[MAP] Loaded map from %s (%dx%d tiles)\n", file_path, map->width, map->height);
    return 0;
}

int fd2_map_load_by_scene_id(fd2_map_data_t* map, int scene_id) {
    if (!map) return -1;
    
    char path[512];
    snprintf(path, sizeof(path), "scenes/scene_%d.json", scene_id);
    
    return fd2_map_load_from_json(map, path);
}

int fd2_map_export_to_json(const fd2_map_data_t* map, int scene_id, 
                            const char* description, const char* output_path) {
    if (!map || !output_path || !map->loaded) return -1;
    
    FILE* f = fopen(output_path, "w");
    if (!f) {
        printf("[MAP] Cannot create file: %s\n", output_path);
        return -1;
    }
    
    fprintf(f, "{\n");
    fprintf(f, "  \"scene_id\": %d,\n", scene_id);
    fprintf(f, "  \"description\": \"%s\",\n", description ? description : "Map");
    fprintf(f, "  \"map_data\": {\n");
    fprintf(f, "    \"width\": %d,\n", map->width);
    fprintf(f, "    \"height\": %d,\n", map->height);
    fprintf(f, "    \"tile_size\": %d,\n", map->tile_size);
    fprintf(f, "    \"tiles\": [\n");
    
    for (int y = 0; y < map->height; y++) {
        fprintf(f, "      [");
        for (int x = 0; x < map->width; x++) {
            if (x > 0) fprintf(f, ", ");
            fprintf(f, "%d", map->tiles[y][x]);
        }
        fprintf(f, "]");
        if (y < map->height - 1) fprintf(f, ",");
        fprintf(f, "\n");
    }
    
    fprintf(f, "    ]\n");
    fprintf(f, "  }\n");
    fprintf(f, "}\n");
    
    fclose(f);
    
    printf("[MAP] Exported map %d to %s (%dx%d tiles)\n",
           scene_id, output_path, map->width, map->height);
    
    return 0;
}

/* ========================================================================
 * Map Renderer Implementation
 * ======================================================================== */

int fd2_map_renderer_init(fd2_map_renderer_t* renderer) {
    if (!renderer) return -1;
    memset(renderer, 0, sizeof(fd2_map_renderer_t));
    fd2_map_init(&renderer->map);
    return 0;
}

void fd2_map_renderer_set_map(fd2_map_renderer_t* renderer, const fd2_map_data_t* map) {
    if (renderer && map) {
        memcpy(&renderer->map, map, sizeof(fd2_map_data_t));
    }
}

const char* fd2_map_get_tile_type_name(u8 tile_type) {
    switch (tile_type) {
        case TILE_EMPTY: return "Empty";
        case TILE_GRASS: return "Grass";
        case TILE_WATER: return "Water";
        case TILE_MOUNTAIN: return "Mountain";
        case TILE_FOREST: return "Forest";
        case TILE_PATH: return "Path";
        case TILE_BUILDING: return "Building";
        case TILE_BRIDGE: return "Bridge";
        case TILE_SPECIAL_8: return "Special 8";
        case TILE_SPECIAL_9: return "Special 9";
        case TILE_SPECIAL_10: return "Special 10";
        case TILE_FLAG_128: return "Flag 128";
        case TILE_FLAG_130: return "Flag 130";
        default: return "Unknown";
    }
}

void fd2_map_renderer_set_tile_color(fd2_map_renderer_t* renderer, 
                                      u8 tile_type, u8 color_index) {
    if (renderer) {
        renderer->tile_colors[tile_type] = color_index;
        renderer->use_custom_palette = true;
    }
}

void fd2_map_renderer_setup_default_colors(fd2_map_renderer_t* renderer) {
    if (!renderer) return;
    
    renderer->use_custom_palette = true;
    
    renderer->tile_colors[TILE_EMPTY] = 0;       /* Black */
    renderer->tile_colors[TILE_GRASS] = 30;      /* Green */
    renderer->tile_colors[TILE_WATER] = 80;      /* Blue */
    renderer->tile_colors[TILE_MOUNTAIN] = 60;   /* Gray */
    renderer->tile_colors[TILE_FOREST] = 40;     /* Dark green */
    renderer->tile_colors[TILE_PATH] = 90;       /* Brown */
    renderer->tile_colors[TILE_BUILDING] = 100;  /* Red-brown */
    renderer->tile_colors[TILE_BRIDGE] = 110;    /* Light brown */
    renderer->tile_colors[TILE_SPECIAL_8] = 120; /* Yellow */
    renderer->tile_colors[TILE_SPECIAL_9] = 130; /* Orange */
    renderer->tile_colors[TILE_SPECIAL_10] = 140;/* Pink */
    renderer->tile_colors[TILE_FLAG_128] = 200;  /* Bright marker */
    renderer->tile_colors[TILE_FLAG_130] = 210;  /* Bright marker */
}

void fd2_map_renderer_render(const fd2_map_renderer_t* renderer, 
                              u8* screen, int screen_w, int screen_h) {
    if (!renderer || !screen || !renderer->map.loaded) return;
    
    const fd2_map_data_t* map = &renderer->map;
    int tile_size = map->tile_size;
    
    /* Clear screen */
    for (int i = 0; i < screen_w * screen_h; i++) {
        screen[i] = 0;
    }
    
    /* Calculate visible tile range */
    int start_x = renderer->scroll_x / tile_size;
    int start_y = renderer->scroll_y / tile_size;
    int end_x = (renderer->scroll_x + screen_w) / tile_size + 1;
    int end_y = (renderer->scroll_y + screen_h) / tile_size + 1;
    
    /* Clamp to map bounds */
    if (start_x < 0) start_x = 0;
    if (start_y < 0) start_y = 0;
    if (end_x > map->width) end_x = map->width;
    if (end_y > map->height) end_y = map->height;
    
    /* Render visible tiles */
    for (int ty = start_y; ty < end_y; ty++) {
        for (int tx = start_x; tx < end_x; tx++) {
            u8 tile = map->tiles[ty][tx];
            if (tile == TILE_EMPTY) continue;
            
            /* Calculate screen position */
            int sx = tx * tile_size - renderer->scroll_x;
            int sy = ty * tile_size - renderer->scroll_y;
            
            /* Get tile color */
            u8 color;
            if (renderer->use_custom_palette) {
                color = renderer->tile_colors[tile];
            } else {
                /* Default: use tile value as color index */
                color = tile;
            }
            
            /* Draw tile */
            for (int dy = 0; dy < tile_size && sy + dy < screen_h; dy++) {
                for (int dx = 0; dx < tile_size && sx + dx < screen_w; dx++) {
                    if (sx + dx >= 0 && sy + dy >= 0) {
                        screen[(sy + dy) * screen_w + (sx + dx)] = color;
                    }
                }
            }
        }
    }
}
