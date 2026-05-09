#ifndef FD2_BATTLE_H
#define FD2_BATTLE_H

#include "fd2_game.h"
#include "fd2_map_loader.h"
#include <stdbool.h>

#define MAP_TILE_SIZE 24
#define TERRAIN_INFO_WIDTH 456
#define TERRAIN_INFO_HEIGHT 24

/* Battle phases based on IDA analysis */
typedef enum {
    BATTLE_PHASE_SELECT_CHAR,      /* 选择角色阶段 */
    BATTLE_PHASE_SHOW_MOVE_RANGE,  /* 显示移动范围阶段 */
    BATTLE_PHASE_ANIM_MOVE,        /* 移动动画阶段 */
    BATTLE_PHASE_SHOW_STATUS       /* 显示状态面板阶段 */
} battle_phase_t;

/* Character data structure based on IDA dword_53A45
 * Each character occupies 80 bytes
 * Key fields from IDA analysis:
 *   offset+0:  tile_x
 *   offset+1:  tile_y
 *   offset+2-3: padding
 *   offset+4:  faction/char_type (0=player, 1=ally, 2+=enemy)
 *   offset+5:  active_byte/death flag
 *   offset+6:  char_type/move_flag (0=未移动)
 *   offset+7:  icon_id
 *   offset+26: active status byte (bit mask for 8 characters per row)
 *   offset+32: icon_id (alternate)
 *   offset+33: direction
 *   offset+39: death flag (non-zero = dead)
 *   offset+59: animation data size
 *   offset+64: animation state
 *   offset+70: level/stats
 */
typedef struct {
    uint8_t tile_x;         /* offset+0: tile X coordinate */
    uint8_t tile_y;         /* offset+1: tile Y coordinate */
    uint8_t padding_2_3[2]; /* offset+2-3: padding */
    uint8_t faction;        /* offset+4: faction/char_type (0=player, 1=ally, 2+=enemy) */
    uint8_t active_byte;    /* offset+5: death flag (bit0=1表示死亡) */
    uint8_t char_type;      /* offset+6: 0=未移动玩家, 其他=已移动/敌方/友军 */
    uint8_t icon_id;        /* offset+7: icon/animation ID */
    uint8_t death_status;   /* offset+8: 0=alive, 28=dead */
    uint8_t moved;          /* offset+9: 0=unmoved, 1=moved */
    uint8_t padding_10_25[16]; /* offset+10-25 */
    uint8_t active_mask;    /* offset+26: active status bit mask */
    uint8_t padding_27_31[5]; /* offset+27-31 */
    uint8_t icon_id_alt;    /* offset+32: alternate icon ID */
    uint8_t direction;      /* offset+33: facing direction */
    uint8_t padding_34_38[5]; /* offset+34-38 */
    uint8_t death_flag;     /* offset+39: 0=alive, non-zero=dead (alias) */
    uint8_t padding_40_58[19]; /* offset+40-58 */
    uint8_t anim_data_size; /* offset+59: animation data size */
    uint8_t padding_60_63[3];  /* offset+60-63 */
    uint8_t anim_state[4];  /* offset+64-67: animation state */
    uint8_t padding_68_69[2];  /* offset+68-69 */
    uint8_t level_stats;    /* offset+70: level/stats */
    uint8_t padding_71_79[9];  /* offset+71-79 */
} battle_char_data_t;

#define MAX_BATTLE_CHARS 64

#ifdef __cplusplus
extern "C" {
#endif

typedef struct {
    int tile_x;
    int tile_y;
    int icon_id;
    int cache_idx;
    int direction;
    int anim_frame;
    int anim_timer;
    u8* pixels;
    int width;
    int height;
    bool loaded;
} map_sprite_t;

typedef struct {
    fd2_map_t map;
    int camera_x;
    int camera_y;

    int cursor_x;
    int cursor_y;
    int scroll_x;
    int scroll_y;
    int move_counter_x;
    int move_counter_y;
    int cursor_blink;
    int cursor_frame_id;

    bool debug_grid_enabled;

    /* Resources loaded via fd2_dat_load_resource (sub_111BA) - must be freed */
    u8* fdother_resource_5;      /* FDOTHER.DAT resource index 5 */
    u32 fdother_resource_5_size;
    u8* fdother_resource_3;      /* FDOTHER.DAT resource index 3 (terrain info) */
    u32 fdother_resource_3_size;

    const u8* fdother_data;
    u32 fdother_data_size;
    const u8* cursor_image_data;
    u32 cursor_image_width;
    u32 cursor_image_height;

    map_sprite_t* sprites;
    int sprite_count;
    int max_sprites;

    int character_icon_id;
    int character_icon_cache_idx;
    int character_segment;
    int character_direction;
    int character_frame;
    fd2_sprite_frame_t character_icon_frame;
    bool character_icon_loaded;
    int character_tile_x;
    int character_tile_y;

    bool from_save;
    int saved_num_fighters;
    u8 saved_char_positions[64][2];

    /* Character selection state - based on IDA sub_12C0D */
    int selected_char_idx;
    int cursor_char_frame_id;

    /* Terraininfo display - based on IDA sub_126F7 */
    const u8* terrain_info_data;
    u32 terrain_info_data_size;
    u8 terrain_info_buffer[TERRAIN_INFO_WIDTH * TERRAIN_INFO_HEIGHT];

    /* Player turn state - based on IDA sub_1CFF0, sub_1D51D */
    battle_char_data_t char_data[MAX_BATTLE_CHARS]; /* 角色数据 (80字节/角色) */
    int total_char_count;          /* 总角色数 */
    int current_char_idx;          /* n2_3: 当前选择的角色索引 */
    int active_char_count;         /* 活跃角色数量 */
    int active_char_ids[40];       /* 活跃角色ID列表 (5行x8列=40) */
    bool char_moved[64];          /* 角色是否已移动标记 */

    /* Movement range state - based on IDA sub_14818 */
    int move_range;                /* 移动力 */
    int move_start_x;              /* 移动起始x */
    int move_start_y;              /* 移动起始y */
    u8* move_range_data;           /* 移动范围标记数据 */

    /* Menu state - based on IDA sub_18D8C, sub_177FC */
    int menu_selected;             /* 当前菜单选择 (0=攻击,1=道具,2=休息,3=魔法) */
    bool menu_visible;             /* 菜单是否可见 */
    int menu_options[4];           /* 菜单选项可用性 */

    /* Turn phase - 回合阶段 */
    int turn_phase;                /* 0=选择角色,1=显示移动范围,2=选择移动目标,3=显示菜单,4=执行功能 */
    battle_phase_t battle_phase;   /* 当前战斗阶段 */
    int showing_move_range;        /* 是否显示移动范围 */
    int move_range_tile_x;         /* 移动范围中心X */
    int move_range_tile_y;         /* 移动范围中心Y */
    int animating_move;            /* 是否正在移动动画 */
    int anim_move_progress;        /* 移动动画进度 (0-7) */

    /* FDFIELD.DAT raw data for info panel rendering */
    const u8* fdfield_layout;      /* dword_53A51: 字符布局表 */
    const u8* fdshap_data;         /* FDSHAP_DAT: 瓦片精灵数据 */
    const u8* fdshap_flags;        /* dword_53A69: 瓦片标志表 */
    const u8* fdother_palette_map; /* dword_53A6D: 调色板映射表 */
    int layout_width;              /* dword_53AC1: 布局表宽度 */
    int layout_height;             /* dword_53AC5: 布局表高度 */
    int palette_anim_frame;        /* dword_53A40: 调色板动画帧 */
    int n3_1;                      /* n3_1: 调色板偏移参数 */
    u8* backbuffer;                /* dword_53A49: 后备缓冲区 */
} state_battle_data_t;

/* Character query - based on IDA sub_12C0D */
int battle_find_char_at_cursor(state_battle_data_t* data);
int battle_check_char_valid(state_battle_data_t* data, int char_idx);

/* Terrain info display - based on IDA sub_126F7, sub_122DC */
int load_terrain_info_data(fd2_game_t* game, state_battle_data_t* data);
void battle_render_terrain_info(state_battle_data_t* data, u8* screen, int screen_w, int screen_h);

/* Sprite system */
void battle_render_sprites(map_sprite_t* sprites, int sprite_count,
                           int camera_x, int camera_y,
                           u8* screen, int screen_w, int screen_h);
void battle_free_sprites(map_sprite_t* sprites, int sprite_count);
int battle_load_sprites(fd2_game_t* game, map_sprite_t** out_sprites,
                        int num_sprites, bool from_save,
                        u8 char_positions[64][2], u8 char_icons[64],
                        fd2_map_t* map_data);
void battle_update_sprite_animations(map_sprite_t* sprites, int sprite_count);

/* Cursor system */
void cursor_move_up(state_battle_data_t* data, int map_height);
void cursor_move_down(state_battle_data_t* data, int map_height);
void cursor_move_left(state_battle_data_t* data, int map_width);
void cursor_move_right(state_battle_data_t* data, int map_width);
void update_camera_from_cursor(state_battle_data_t* data);
int decode_rle_image(const u8* src, u8* dst, int dst_stride, int width, int height);
int load_cursor_image(fd2_game_t* game, state_battle_data_t* data);
void battle_render_cursor(state_battle_data_t* data, u8* screen, int screen_w, int screen_h);
void battle_render_debug_grid(state_battle_data_t* data, u8* screen, int screen_w, int screen_h);

/* Battle entry and main loop - based on IDA sub_18D8C, sub_1CFF0 */
int battle_entry(fd2_game_t* game, int n17, int* dst, int a6);
int battle_main_loop(fd2_game_t* game, int n19, int n17);
int battle_attack_handler(fd2_game_t* game, int n6, int n6_3, u8* a7);

/* Active character list - based on IDA sub_1C269 */
int battle_get_active_char_ids(state_battle_data_t* data, int* out_ids, int max_ids);

/* Movement range and display list - based on IDA sub_14818 */
int battle_build_display_list(state_battle_data_t* data, int n16, int n19, int n2, u8* out_list);

/* 战场UI渲染 (fd2_battle_ui.c) */
void battle_draw_cursor(void);
void battle_draw_terrain_info(void);
void battle_draw_character_info(int selected_char_index);
void battle_clear_info_panel(void);

/* 战场角色信息面板 (fd2_battle_info.c) - 基于IDA分析 */
/* sub_12D7B -> sub_12CEA -> sub_11CAC -> sub_11EEE */
void battle_render_info_panel(
    int char_index,
    const u8* char_data,
    const u8* layout_table,
    const u8* tile_flags,
    const u8* palette_map,
    const u8* fdshap_data,
    u8* backbuffer,
    int layout_width,
    int palette_anim_frame,
    int n3_1
);
void render_char_name(int char_index, const u8* char_data, int dst_x, int dst_y);

/* Player turn logic - based on IDA analysis */
void battle_turn_init(state_battle_data_t* data);
void battle_turn_cleanup(state_battle_data_t* data);
int battle_get_active_chars(state_battle_data_t* data, int* out_ids, int max_ids);
int battle_char_selection(state_battle_data_t* data, fd2_game_t* game);
int battle_calc_move_range(state_battle_data_t* data, int start_x, int start_y, int move_power);
int battle_select_move_target(state_battle_data_t* data, fd2_game_t* game, int mode, int* out_x, int* out_y);
int battle_menu_selection(state_battle_data_t* data, fd2_game_t* game, int* menu_state);
int battle_action_menu(state_battle_data_t* data, fd2_game_t* game);
void battle_render_char_list(state_battle_data_t* data, fd2_game_t* game);
void battle_render_menu(state_battle_data_t* data, fd2_game_t* game, int* menu_state);
void battle_highlight_menu_option(state_battle_data_t* data, int option_idx);

/* Battle state */
void state_battle_enter(fd2_game_t* game);
fd2_state_t state_battle_update(fd2_game_t* game);
void state_battle_exit(fd2_game_t* game);

#ifdef __cplusplus
}
#endif

#endif /* FD2_BATTLE_H */
