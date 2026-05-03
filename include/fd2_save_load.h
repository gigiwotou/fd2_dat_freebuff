#ifndef FD2_SAVE_LOAD_H
#define FD2_SAVE_LOAD_H

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define BATTLE_SAVE_SIZE 22987
#define BATTLE_SAVE_MAP_DATA_OFFSET 0
#define BATTLE_SAVE_MAP_DATA_SIZE 2211
#define BATTLE_SAVE_TEMP_MAP_OFFSET 2211
#define BATTLE_SAVE_TEMP_MAP_SIZE 2560
#define BATTLE_SAVE_CHAR_DATA_OFFSET 4771
#define BATTLE_SAVE_CHAR_DATA_SIZE 80
#define BATTLE_SAVE_STATE_OFFSET 12451
#define BATTLE_SAVE_CHECKSUM_OFFSET 22983

typedef struct {
    uint8_t map_data[BATTLE_SAVE_MAP_DATA_SIZE];
    uint8_t temp_map_data[BATTLE_SAVE_TEMP_MAP_SIZE];
    uint8_t char_data[64 * BATTLE_SAVE_CHAR_DATA_SIZE];
    uint8_t state_data[32];
    uint8_t n999;
    uint8_t n6_0;
    uint8_t n17;
    uint16_t qword_53AA9;
    uint16_t qword_53AB1;
    uint8_t n10;
    uint8_t n2;
    uint8_t n16_1;
    uint32_t n999_0;
    uint8_t byte_53AF9;
    uint8_t byte_51AAB;
    uint8_t n127;
    uint8_t byte_51E62;
    uint32_t checksum;
} battle_save_data_t;

void decrypt_battle_save(uint8_t* data, int size);
int calculate_battle_save_checksum(uint8_t* data, int size);
int load_battle_save(const char* save_path, battle_save_data_t* save);

#ifdef __cplusplus
}
#endif

#endif /* FD2_SAVE_LOAD_H */
