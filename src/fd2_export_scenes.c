/**
 * FD2 Scene Correct Export Tool (Based on IDA sub_15F84 Analysis)
 * 
 * Exports scene data as sequence of 16-bit commands.
 * Scene format:
 *   - Values >= 0xFF00: Special control commands
 *   - Values < 0xFF00: Sprite/tile indices to render in sequence
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* Scene data from fd2_scene.c */
static unsigned char scene_97_raw[] = {
    0x03, 0x01, 0x01, 0x01, 0x00, 0x01, 0x01, 0x01, 0x01, 0x84, 0x02, 0x00,
    0x00, 0x01, 0x02, 0x09, 0x01, 0x03, 0x00, 0x03, 0x03, 0x03, 0x04, 0x03,
    0x01, 0x03, 0x00, 0x00, 0x03, 0x03, 0x04, 0x03, 0x01, 0x03, 0x00, 0x03,
    0x01, 0x03, 0x04, 0x03, 0x01, 0x04, 0x00, 0x03, 0x01, 0x03, 0x03, 0x00,
    0x04, 0x03, 0x01, 0x04, 0x00, 0x03, 0x01, 0x03, 0x03, 0x03, 0x04, 0x00,
    0x01, 0x04, 0x00, 0x00, 0x01, 0x03, 0x03, 0x03, 0x04, 0x03, 0x01, 0x04,
    0x00, 0x03, 0x01, 0x00, 0x03, 0x03, 0x04, 0x03, 0x01, 0x04, 0x00, 0x03,
    0x01, 0x03, 0x03, 0x00, 0x04, 0x03, 0x01, 0x04, 0x00, 0x03, 0x01, 0x03,
    0x03, 0x03, 0x04, 0x00, 0x01, 0x06, 0x01, 0x02, 0x02, 0x01, 0x0A, 0x01,
    0x02, 0x00, 0x01, 0x03, 0x01, 0x04, 0x01, 0x03, 0x02, 0x01, 0x04, 0x01,
    0x01, 0x01, 0x04, 0x02, 0x01, 0x01, 0x04, 0x01, 0x01, 0x80, 0x01, 0x04,
    0x01, 0x01, 0x82, 0x01, 0x03, 0x03, 0x05, 0x02, 0x01, 0x03, 0x03, 0x01,
    0x01, 0x03, 0x00, 0x01, 0x01, 0x03, 0x03, 0x01, 0x02, 0x03, 0x03, 0x04,
    0x00, 0x04, 0x02, 0x03, 0x03, 0x04, 0x03, 0x00, 0x00
};

static unsigned char scene_99_raw[] = {
    0x05, 0x06, 0x04, 0x00, 0x02, 0x01, 0x02, 0x02, 0x02, 0x03, 0x02, 0x88,
    0x01, 0x00, 0x01, 0x88, 0x01, 0x00, 0x03, 0x08, 0x01, 0x00, 0x01, 0x84,
    0x01, 0x00, 0x00
};

static unsigned char scene_100_raw[] = {
    0x01, 0x01, 0x04, 0x04, 0x00, 0x05, 0x00, 0x06, 0x00, 0x07, 0x00, 0x04,
    0x01, 0x04, 0x08, 0x02, 0x09, 0x02, 0x0A, 0x01, 0x0B, 0x03, 0x02, 0x04,
    0x08, 0x03, 0x09, 0x02, 0x0A, 0x02, 0x0B, 0x02, 0x02, 0x04, 0x08, 0x02,
    0x09, 0x03, 0x0A, 0x02, 0x0B, 0x02, 0x84, 0x05, 0x09, 0x02, 0x00, 0x00,
    0x01, 0x00, 0x02, 0x00, 0x03, 0x00, 0x03, 0x02, 0x04, 0x0E, 0x01, 0x0F,
    0x02, 0x10, 0x02, 0x11, 0x02, 0x02, 0x04, 0x0E, 0x01, 0x0F, 0x01, 0x10,
    0x01, 0x11, 0x01, 0x02, 0x04, 0x0E, 0x02, 0x0F, 0x01, 0x10, 0x02, 0x11,
    0x01, 0x02, 0x01, 0x05, 0x12, 0x02, 0x13, 0x02, 0x14, 0x03, 0x15, 0x02,
    0x16, 0x03, 0x01, 0x01, 0x12
};

struct raw_scene {
    int scene_id;
    const unsigned char* raw_data;
    size_t raw_size;
};

static struct raw_scene scenes[] = {
    { 97, scene_97_raw, sizeof(scene_97_raw) },
    { 99, scene_99_raw, sizeof(scene_99_raw) },
    { 100, scene_100_raw, sizeof(scene_100_raw) },
};

const char* get_scene_description(int scene_id) {
    switch (scene_id) {
        case 97:  return "Battlefield map - First story level";
        case 99:  return "Opening animation";
        case 100: return "Intro scene 1";
        default:  return "Unknown scene";
    }
}

const char* get_command_name(unsigned short cmd) {
    switch (cmd) {
        case 0xFFFF: return "END_OF_SCENE";
        case 0xFFFE: return "CONTROL_A";
        case 0xFFFD: return "CONTROL_B";
        case 0xFFFC: return "RECURSIVE_A";
        case 0xFFFB: return "RECURSIVE_B";
        case 0xFFFA: return "DISPLAY_NUMBER";
        case 0xFFEF: return "LOAD_SPRITE_TYPE1";
        case 0xFFEE: return "LOAD_SPRITE_TYPE2";
        case 0xFFED: return "LOAD_SPRITE_80X";
        case 0xFFEC: return "LOAD_SPRITE_80X_TYPE4";
        default:     return "SPRITE_INDEX";
    }
}

int export_scene_correct(int scene_id, const unsigned char* data, size_t size, const char* output_path) {
    if (!data || !output_path || size < 2) return -1;
    
    FILE* f = fopen(output_path, "w");
    if (!f) {
        printf("Cannot create file: %s\n", output_path);
        return -1;
    }
    
    fprintf(f, "{\n");
    fprintf(f, "  \"scene_id\": %d,\n", scene_id);
    fprintf(f, "  \"description\": \"%s\",\n", get_scene_description(scene_id));
    fprintf(f, "  \"format\": \"ida_sub_15F84\",\n");
    fprintf(f, "  \"raw_size\": %zu,\n", size);
    fprintf(f, "  \"format_note\": \"Scene data is a sequence of 16-bit values. Values >= 0xFF00 are special commands, others are sprite/tile indices.\\n\",\n");
    
    /* Parse and export commands */
    fprintf(f, "  \"commands\": [\n");
    
    size_t offset = 0;
    int cmd_idx = 0;
    
    while (offset + 1 < size) {
        if (cmd_idx > 0) fprintf(f, ",\n");
        
        unsigned short cmd = (unsigned short)(data[offset] | (data[offset + 1] << 8));
        offset += 2;
        
        int is_special = (cmd >= 0xFF00);
        
        fprintf(f, "    {\n");
        fprintf(f, "      \"index\": %d,\n", cmd_idx);
        fprintf(f, "      \"offset\": %zu,\n", offset - 2);
        fprintf(f, "      \"value\": 0x%04X,\n", cmd);
        fprintf(f, "      \"signed_value\": %d,\n", (short)cmd);
        fprintf(f, "      \"type\": \"%s\",\n", is_special ? "special" : "sprite");
        fprintf(f, "      \"name\": \"%s\"", get_command_name(cmd));
        
        if (is_special) {
            fprintf(f, ",\n");
            fprintf(f, "      \"description\": \"");
            
            switch (cmd) {
                case 0xFFFF:
                    fprintf(f, "End of scene");
                    break;
                case 0xFFFE:
                case 0xFFFD:
                    fprintf(f, "Control command, increments n3 counter");
                    break;
                case 0xFFFC:
                case 0xFFFB:
                    fprintf(f, "Recursive scene call");
                    break;
                case 0xFFFA:
                    fprintf(f, "Display number on screen");
                    break;
                case 0xFFEF:
                case 0xFFEE:
                    fprintf(f, "Load sprite with fixed offset");
                    break;
                case 0xFFED:
                case 0xFFEC:
                    fprintf(f, "Load sprite at 80*index offset");
                    break;
                default:
                    fprintf(f, "Unknown special command");
                    break;
            }
            fprintf(f, "\"\n");
        } else {
            fprintf(f, ",\n");
            fprintf(f, "      \"description\": \"Sprite/tile index to render at current position\",\n");
            fprintf(f, "      \"render_x\": %d\n", cmd_idx * 16);
        }
        
        fprintf(f, "    }");
        cmd_idx++;
    }
    
    fprintf(f, "\n  ],\n");
    fprintf(f, "  \"total_commands\": %d,\n", cmd_idx);
    fprintf(f, "  \"render_width_pixels\": %d\n", cmd_idx * 16);
    fprintf(f, "}\n");
    
    fclose(f);
    
    printf("Exported scene %d: %d commands -> %s\n", scene_id, cmd_idx, output_path);
    return 0;
}

int main() {
    const char* output_dir = "scenes";
    
    printf("=== FD2 Scene Export Tool (IDA Analysis Based) ===\n");
    printf("Format: 16-bit command sequence (sub_15F84)\n\n");
    
    for (size_t i = 0; i < sizeof(scenes) / sizeof(scenes[0]); i++) {
        char output_path[512];
        snprintf(output_path, sizeof(output_path), "%s/scene_%d.json", 
                 output_dir, scenes[i].scene_id);
        
        export_scene_correct(scenes[i].scene_id, scenes[i].raw_data, 
                            scenes[i].raw_size, output_path);
    }
    
    printf("\nDone! Scene files exported to %s/\n", output_dir);
    return 0;
}
