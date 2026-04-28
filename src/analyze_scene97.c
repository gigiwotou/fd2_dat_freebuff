/**
 * FD2 Scene 97 Proper Binary Analyzer (based on IDA sub_15F84 analysis)
 * 
 * Scene data format (16-bit values):
 * - Special markers (>= 0xFF00): Control commands
 * - Regular values: Sprite/tile indices to render at current position
 */

#include <stdio.h>
#include <stdlib.h>

int main() {
    unsigned char scene_97_raw[] = {
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
    
    size_t total_size = sizeof(scene_97_raw);
    
    printf("=== Scene 97 Analysis (IDA sub_15F84 format) ===\n");
    printf("Total bytes: %zu\n", total_size);
    printf("Data interpreted as sequence of 16-bit values\n\n");
    
    size_t offset = 0;
    int cmd_idx = 0;
    int x_pos = 0;  /* Tracks rendering position */
    
    while (offset + 1 < total_size) {
        unsigned short val = (unsigned short)(scene_97_raw[offset] | (scene_97_raw[offset + 1] << 8));
        offset += 2;
        
        int is_special = (val >= 0xFF00);
        
        if (is_special) {
            short signed_val = (short)val;
            printf("[%3d] offset %4zu: 0x%04X (%5d) SPECIAL", cmd_idx, offset - 2, val, signed_val);
            
            switch (val) {
                case 0xFFFF:  /* -1 */
                    printf(" -> END OF SCENE\n");
                    goto end;
                case 0xFFFE:  /* -2 */
                case 0xFFFD:  /* -3 */
                    printf(" -> Control command (n3++)\n");
                    break;
                case 0xFFFC:  /* -4 */
                    printf(" -> Recursive call (dword_53A7D)\n");
                    break;
                case 0xFFFB:  /* -5 */
                    printf(" -> Recursive call (dword_53ADD)\n");
                    break;
                case 0xFFFA:  /* -6 */
                    printf(" -> Display number\n");
                    break;
                case 0xFFEF:  /* -17 */
                    printf(" -> Load sprite (n1832=1832), param:");
                    if (offset + 1 < total_size) {
                        unsigned short p = (unsigned short)(scene_97_raw[offset] | (scene_97_raw[offset + 1] << 8));
                        offset += 2;
                        printf(" %u\n", p);
                    }
                    break;
                case 0xFFEE:  /* -18 */
                    printf(" -> Load sprite (n1832=36887), param:");
                    if (offset + 1 < total_size) {
                        unsigned short p = (unsigned short)(scene_97_raw[offset] | (scene_97_raw[offset + 1] << 8));
                        offset += 2;
                        printf(" %u\n", p);
                    }
                    break;
                case 0xFFED:  /* -19 */
                    printf(" -> Load sprite (80*index), param:");
                    if (offset + 1 < total_size) {
                        unsigned short p = (unsigned short)(scene_97_raw[offset] | (scene_97_raw[offset + 1] << 8));
                        offset += 2;
                        printf(" %u\n", p);
                    }
                    break;
                case 0xFFEC:  /* -20 */
                    printf(" -> Load sprite (80*index), param:");
                    if (offset + 1 < total_size) {
                        unsigned short p = (unsigned short)(scene_97_raw[offset] | (scene_97_raw[offset + 1] << 8));
                        offset += 2;
                        printf(" %u\n", p);
                    }
                    break;
                default:
                    printf(" -> Unknown special\n");
                    break;
            }
        } else {
            /* Regular sprite/tile index - renders at current position */
            printf("[%3d] offset %4zu: 0x%04X (%5u) REGULAR -> sprite/tile index %u at x=%d\n",
                   cmd_idx, offset - 2, val, val, val, x_pos);
            x_pos += 16;  /* Each sprite is 16 pixels wide */
        }
        
        cmd_idx++;
    }
    
end:
    printf("\n=== Summary ===\n");
    printf("Total commands: %d\n", cmd_idx);
    printf("Bytes consumed: %zu / %zu\n", offset, total_size);
    printf("Total render width: %d pixels\n", x_pos);
    
    /* Try to interpret as tile map */
    printf("\n=== Possible Tile Map Interpretation ===\n");
    int sprite_count = x_pos / 16;
    printf("If interpreted as tile map:\n");
    printf("  Total sprites/tiles: %d\n", sprite_count);
    
    /* Try different map dimensions */
    int dims[][2] = {
        {20, 3}, {15, 4}, {12, 5}, {10, 6}, {6, 10}, {5, 12}, {4, 15}, {3, 20}
    };
    
    for (size_t d = 0; d < sizeof(dims) / sizeof(dims[0]); d++) {
        if (dims[d][0] * dims[d][1] == sprite_count) {
            printf("  Possible layout: %d x %d (width x height)\n", dims[d][0], dims[d][1]);
        }
    }
    
    return 0;
}
