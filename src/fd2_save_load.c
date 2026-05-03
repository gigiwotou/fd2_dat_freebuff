/**
 * FD2 Battle Save Loading
 *
 * Based on IDA sub_10010 (save loading) and sub_4DF28 (decryption).
 */

#include "fd2_save_load.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static uint16_t rol16(uint16_t value, int shift) {
    shift &= 15;
    return (value << shift) | (value >> (16 - shift));
}

void decrypt_battle_save(uint8_t* data, int size) {
    uint16_t n165 = 165;
    for (int i = 0; i < size; i++) {
        n165 = (uint16_t)(n165 + 0x9014);
        n165 = rol16(n165, 3);
        data[i] ^= (uint8_t)(n165 & 0xFF);
    }
}

static void debug_print_first_bytes(uint8_t* data, int size, const char* label) {
    fprintf(stderr, "%s (first 20 bytes):\n", label);
    for (int i = 0; i < 20 && i < size; i++) {
        fprintf(stderr, "  [%d] = %d (0x%02X)\n", i, data[i], data[i]);
    }
}

int calculate_battle_save_checksum(uint8_t* data, int size) {
    int checksum = 0;
    int count = size - 4;
    for (int i = 0; i < count; i++) {
        checksum += data[i];
    }
    return checksum;
}

int load_battle_save(const char* save_path, battle_save_data_t* save) {
    if (!save_path || !save) return -1;

    FILE* f = fopen(save_path, "rb");
    if (!f) {
        fprintf(stderr, "load_battle_save: cannot open %s\n", save_path);
        return -1;
    }

    uint8_t* buffer = (uint8_t*)malloc(BATTLE_SAVE_SIZE);
    if (!buffer) {
        fclose(f);
        return -1;
    }

    size_t bytes_read = fread(buffer, 1, BATTLE_SAVE_SIZE, f);
    fclose(f);

    if (bytes_read != BATTLE_SAVE_SIZE) {
        fprintf(stderr, "load_battle_save: invalid save size (%zu bytes)\n", bytes_read);
        free(buffer);
        return -1;
    }

    decrypt_battle_save(buffer, BATTLE_SAVE_SIZE);

    fprintf(stderr, "DEBUG: first 20 bytes AFTER decrypt:\n");
    for (int i = 0; i < 20; i++) {
        fprintf(stderr, "  [%d] = 0x%02X (%d)\n", i, buffer[i], buffer[i]);
    }
    fprintf(stderr, "DEBUG: checksum bytes [22983..22986] AFTER decrypt:\n");
    fprintf(stderr, "  [22983] = 0x%02X, [22984] = 0x%02X, [22985] = 0x%02X, [22986] = 0x%02X\n",
            buffer[22983], buffer[22984], buffer[22985], buffer[22986]);
    fprintf(stderr, "DEBUG: skipping checksum verification for now\n");

    fprintf(stderr, "DEBUG: decrypted offsets:\n");
    fprintf(stderr, "  [22983-22986] checksum: %02X %02X %02X %02X\n",
            buffer[22983], buffer[22984], buffer[22985], buffer[22986]);
    fprintf(stderr, "  [12483] n999: %d (0x%02X)\n", buffer[12483], buffer[12483]);
    fprintf(stderr, "  [12484] n6_0 (char count): %d (0x%02X)\n", buffer[12484], buffer[12484]);
    fprintf(stderr, "  [12485] n17 (scene idx): %d (0x%02X)\n", buffer[12485], buffer[12485]);
    fprintf(stderr, "  [12486] qword_53AA9 low: %d (0x%02X)\n", buffer[12486], buffer[12486]);
    fprintf(stderr, "  [12487] qword_53AA9 high: %d (0x%02X)\n", buffer[12487], buffer[12487]);
    fprintf(stderr, "  [0] first byte: %d (0x%02X)\n", buffer[0], buffer[0]);
    fprintf(stderr, "  [1] second byte: %d (0x%02X)\n", buffer[1], buffer[1]);

    memcpy(save->map_data, buffer + BATTLE_SAVE_MAP_DATA_OFFSET, BATTLE_SAVE_MAP_DATA_SIZE);
    memcpy(save->temp_map_data, buffer + BATTLE_SAVE_TEMP_MAP_OFFSET, BATTLE_SAVE_TEMP_MAP_SIZE);

    save->n6_0 = buffer[BATTLE_SAVE_STATE_OFFSET + 33];

    if (save->n6_0 > 0 && save->n6_0 <= 64) {
        memcpy(save->char_data, buffer + BATTLE_SAVE_CHAR_DATA_OFFSET,
               save->n6_0 * BATTLE_SAVE_CHAR_DATA_SIZE);
    }

    memcpy(save->state_data, buffer + BATTLE_SAVE_STATE_OFFSET, 32);

    save->n999 = buffer[BATTLE_SAVE_STATE_OFFSET + 32];
    save->n17 = buffer[BATTLE_SAVE_STATE_OFFSET + 34];
    save->qword_53AA9 = buffer[BATTLE_SAVE_STATE_OFFSET + 35] |
                       (buffer[BATTLE_SAVE_STATE_OFFSET + 36] << 8);
    save->qword_53AB1 = buffer[BATTLE_SAVE_STATE_OFFSET + 37] |
                       (buffer[BATTLE_SAVE_STATE_OFFSET + 38] << 8);
    save->n10 = buffer[BATTLE_SAVE_STATE_OFFSET + 39];
    save->n2 = buffer[BATTLE_SAVE_STATE_OFFSET + 40];
    save->n16_1 = buffer[BATTLE_SAVE_STATE_OFFSET + 41];
    save->n999_0 = buffer[BATTLE_SAVE_STATE_OFFSET + 42] |
                  (buffer[BATTLE_SAVE_STATE_OFFSET + 43] << 8) |
                  (buffer[BATTLE_SAVE_STATE_OFFSET + 44] << 16) |
                  (buffer[BATTLE_SAVE_STATE_OFFSET + 45] << 24);
    save->byte_53AF9 = buffer[BATTLE_SAVE_STATE_OFFSET + 46];
    save->byte_51AAB = buffer[BATTLE_SAVE_STATE_OFFSET + 47];
    save->n127 = buffer[BATTLE_SAVE_STATE_OFFSET + 48];
    save->byte_51E62 = buffer[BATTLE_SAVE_STATE_OFFSET + 49];

    free(buffer);

    printf("load_battle_save: loaded successfully (scene=%d, chars=%d)\n",
           save->n17, save->n6_0);

    return 0;
}
