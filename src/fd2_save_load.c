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

    /* Verify the byte-sum checksum (sub_4DF09) against the u32 trailer.
     * This used to be skipped, so a corrupt/wrongly-decrypted save was
     * accepted and produced garbage scene + character state.
     * Verified against the real FD2.SAV: computed == stored == 0x412A13. */
    uint32_t computed = (uint32_t)calculate_battle_save_checksum(buffer, BATTLE_SAVE_SIZE);
    uint32_t stored   = (uint32_t)buffer[BATTLE_SAVE_CHECKSUM_OFFSET]
                      | ((uint32_t)buffer[BATTLE_SAVE_CHECKSUM_OFFSET + 1] << 8)
                      | ((uint32_t)buffer[BATTLE_SAVE_CHECKSUM_OFFSET + 2] << 16)
                      | ((uint32_t)buffer[BATTLE_SAVE_CHECKSUM_OFFSET + 3] << 24);

    if (computed != stored) {
        fprintf(stderr, "load_battle_save: checksum mismatch "
                        "(computed=0x%08X stored=0x%08X) - refusing corrupt save\n",
                computed, stored);
        free(buffer);
        return -1;
    }

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

int fd2_save_detect_state(const char* save_path) {
    if (!save_path) return FD2_SAVE_STATE_NONE;

    FILE* f = fopen(save_path, "rb");
    if (!f) return FD2_SAVE_STATE_NONE;

    uint8_t* buf = (uint8_t*)malloc(BATTLE_SAVE_SIZE);
    if (!buf) { fclose(f); return FD2_SAVE_STATE_NONE; }

    size_t got = fread(buf, 1, BATTLE_SAVE_SIZE, f);
    fclose(f);

    if (got != BATTLE_SAVE_SIZE) {
        free(buf);
        return FD2_SAVE_STATE_NONE;
    }

    decrypt_battle_save(buf, BATTLE_SAVE_SIZE);

    uint32_t computed = (uint32_t)calculate_battle_save_checksum(buf, BATTLE_SAVE_SIZE);
    uint32_t stored   = (uint32_t)buf[BATTLE_SAVE_CHECKSUM_OFFSET]
                      | ((uint32_t)buf[BATTLE_SAVE_CHECKSUM_OFFSET + 1] << 8)
                      | ((uint32_t)buf[BATTLE_SAVE_CHECKSUM_OFFSET + 2] << 16)
                      | ((uint32_t)buf[BATTLE_SAVE_CHECKSUM_OFFSET + 3] << 24);

    int state = FD2_SAVE_STATE_NONE;
    if (computed == stored) {
        state = FD2_SAVE_STATE_CAMP;
        if (buf[BATTLE_SAVE_STATE_OFFSET + 34] != 255) {
            state = FD2_SAVE_STATE_BATTLE;
        }
    }

    free(buf);
    return state;
}
