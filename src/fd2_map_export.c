/**
 * FD2 Map Export Tool
 * 
 * Exports scene binary data to editable JSON format.
 * Parses scene commands and extracts map tile data.
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* Scene 97 raw data */
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

/* Scene 99 raw data */
static unsigned char scene_99_raw[] = {
    0x05, 0x06, 0x04, 0x00, 0x02, 0x01, 0x02, 0x02, 0x02, 0x03, 0x02, 0x88,
    0x01, 0x00, 0x01, 0x88, 0x01, 0x00, 0x03, 0x08, 0x01, 0x00, 0x01, 0x84,
    0x01, 0x00, 0x00
};

/* Scene 100 raw data */
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

static const char* get_command_name(unsigned char type) {
    int base = type & 0x7F;
    int is_special = (type & 0x80) != 0;
    
    if (is_special) {
        switch (base) {
            case 0x00: return "Display";
            case 0x01: return "Animate/Move";
            case 0x02: return "Wait/Fade";
            case 0x03: return "Show/Hide";
            case 0x04: return "InitCharacters";
            case 0x05: return "Wait/FadeLong";
            case 0x80: return "Special_0x80";
            case 0x82: return "Special_0x82";
            case 0x84: return "Special_0x84";
            case 0x88: return "Special_0x88";
            default: return "Special";
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

const char* get_scene_description(int scene_id) {
    switch (scene_id) {
        case 97:  return "Battlefield map - First story level";
        case 99:  return "Opening animation";
        case 100: return "Intro scene 1";
        default:  return "Unknown scene";
    }
}

/* Export scene to JSON with map tile extraction */
int export_scene_to_json(int scene_id, const unsigned char* data, size_t size, const char* output_path) {
    if (!data || !output_path || size < 1) return -1;
    
    FILE* f = fopen(output_path, "w");
    if (!f) {
        printf("Cannot create file: %s\n", output_path);
        return -1;
    }
    
    /* Parse commands from raw data */
    size_t offset = 0;
    unsigned char cmd_count = data[offset++];
    
    fprintf(f, "{\n");
    fprintf(f, "  \"scene_id\": %d,\n", scene_id);
    fprintf(f, "  \"description\": \"%s\",\n", get_scene_description(scene_id));
    fprintf(f, "  \"raw_size\": %zu,\n", size);
    fprintf(f, "  \"command_count\": %d,\n", cmd_count);
    
    /* Export commands */
    fprintf(f, "  \"commands\": [\n");
    
    int cmd_idx = 0;
    size_t cmd_end_offset = offset;
    
    while (offset < size && cmd_idx < cmd_count) {
        if (cmd_idx > 0) fprintf(f, ",\n");
        
        unsigned char cmd_type = data[offset++];
        unsigned char param_count = data[offset++];
        
        fprintf(f, "    {\n");
        fprintf(f, "      \"type\": 0x%02X,\n", cmd_type);
        fprintf(f, "      \"name\": \"%s\",\n", get_command_name(cmd_type));
        fprintf(f, "      \"params\": [");
        
        for (int i = 0; i < param_count && offset + 1 < size; i++) {
            unsigned short param = (unsigned short)(data[offset] | (data[offset + 1] << 8));
            offset += 2;
            
            if (i > 0) fprintf(f, ", ");
            fprintf(f, "%d", param);
        }
        
        fprintf(f, "]\n");
        fprintf(f, "    }");
        cmd_idx++;
        cmd_end_offset = offset;
    }
    
    fprintf(f, "\n  ],\n");
    
    /* Export remaining bytes as map tile data */
    size_t remaining = size - cmd_end_offset;
    fprintf(f, "  \"raw_bytes_after_commands\": %zu,\n", remaining);
    
    if (remaining > 0) {
        fprintf(f, "  \"map_data\": {\n");
        fprintf(f, "    \"tile_format\": \"raw_bytes\",\n");
        fprintf(f, "    \"byte_count\": %zu,\n", remaining);
        fprintf(f, "    \"bytes\": [");
        
        for (size_t i = 0; i < remaining; i++) {
            if (i > 0) fprintf(f, ", ");
            if (i % 20 == 0) fprintf(f, "\n      ");
            fprintf(f, "%d", data[cmd_end_offset + i]);
        }
        
        fprintf(f, "\n    ]\n");
        fprintf(f, "  }\n");
    }
    
    fprintf(f, "}\n");
    fclose(f);
    
    printf("Exported scene %d to %s (%d commands, %zu bytes remaining)\n",
           scene_id, output_path, cmd_idx, remaining);
    
    return 0;
}

int main(int argc, char* argv[]) {
    const char* output_dir = "scenes";
    
    printf("FD2 Map Export Tool\n");
    printf("===================\n\n");
    
    for (size_t i = 0; i < sizeof(scenes) / sizeof(scenes[0]); i++) {
        char output_path[512];
        snprintf(output_path, sizeof(output_path), "%s/scene_%d.json", 
                 output_dir, scenes[i].scene_id);
        
        export_scene_to_json(scenes[i].scene_id, scenes[i].raw_data, 
                             scenes[i].raw_size, output_path);
    }
    
    printf("\nDone! Edit the JSON files to modify map data.\n");
    return 0;
}
