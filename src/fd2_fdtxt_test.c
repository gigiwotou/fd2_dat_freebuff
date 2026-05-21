/*
 * FDTXT.DAT 文本渲染测试 - 完整游戏对话逻辑版本
 * 
 * 1:1还原游戏双对话框绘制和控制逻辑
 * 基于sub_15F84和sub_4ED7A函数
 * 
 * 编译: build.bat fdtxttest
 * 运行: bin\fd2_fdtxt_test.exe
 */

#include <SDL2/SDL.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <stdbool.h>

/* 游戏常量 */
#define SCREEN_WIDTH 320
#define SCREEN_HEIGHT 200
#define SCALE_FACTOR 3
#define CHAR_WIDTH 16
#define CHAR_HEIGHT 16

#define FONT_MAX_CHARS 1824

/* 控制码 (sub_15F84) */
#define TEXT_END        -1
#define TEXT_NEWLINE    -2
#define TEXT_NEWLINE2   -3
#define TEXT_RECURSE1   -4
#define TEXT_RECURSE2   -5
#define TEXT_SHOW_NUM   -6
#define TEXT_PORTRAIT_F -17
#define TEXT_PORTRAIT_S -18
#define TEXT_CHAR_F     -19
#define TEXT_CHAR_S     -20

/* 文件路径 */
#define FONT_DAT_PATH "game/FDOTHER.DAT"
#define FDTXT_DAT_PATH "game/FDTXT.DAT"
#define DATO_DAT_PATH "game/DATO.DAT"

/* 对话框常量 - 根据汇编代码0x165AC还原 */
#define DIALOG_X          8
#define DIALOG_W          304
#define DIALOG_H          64
#define DIALOG_BG_COLOR   0xFF0C0C0C
#define DIALOG_BORDER_COLOR 0xFF808080
#define DIALOG_TEXT_FG    0xFFFFFFFF
#define DIALOG_TEXT_BG    0xFF0C0C0C

/* 下方对话框 (角色F) */
#define DIALOG_F_Y        64
#define DIALOG_F_X        DIALOG_X
#define TEXT_F_START_X    (DIALOG_F_X + 8 + 64 + 8)  /* 头像右边 */
#define TEXT_F_START_Y    (DIALOG_F_Y + 8)

/* 上方对话框 (角色S) */
#define DIALOG_S_Y        8
#define DIALOG_S_X        DIALOG_X
#define TEXT_S_START_X    (DIALOG_S_X + 8 + 64 + 8)  /* 头像右边 */
#define TEXT_S_START_Y    (DIALOG_S_Y + 8)

#define PORTRAIT_F_X      (DIALOG_F_X + 8)
#define PORTRAIT_F_Y      (DIALOG_F_Y + 8)
#define PORTRAIT_S_X      (DIALOG_S_X + 8)
#define PORTRAIT_S_Y      (DIALOG_S_Y + 8)
#define PORTRAIT_W        64
#define PORTRAIT_H        48

#define TEXT_WRAP_X       (DIALOG_X + DIALOG_W - CHAR_WIDTH - 4)
#define TEXT_MAX_LINES    3

/* 对话框类型 (1:1还原n1832) */
typedef enum {
    DIALOG_TYPE_F = 1832,   /* 下方对话框 (0x728) */
    DIALOG_TYPE_S = 36887   /* 上方对话框 (0x9017) */
} dialog_type_t;

/* 文本状态 (1:1还原sub_15F84) */
typedef enum {
    TEXT_CONTINUE = 0,       /* 继续渲染 */
    TEXT_WAIT_KEY_NEWLINE2 = 1, /* TEXT_NEWLINE2后等待按键 (sub_16C57) */
    TEXT_WAIT_KEY_END = 2,   /* TEXT_END后等待按键 */
    TEXT_DONE = 3            /* 当前子项渲染完成 */
} text_state_t;

typedef struct {
    int16_t* ptr;           /* 当前文本指针 */
    int x, y;               /* 当前渲染位置（已废弃，保留兼容） */
    int char_index;         /* 当前字符索引（X方向） */
    int line_count;         /* 当前行数（Y方向） */
    text_state_t state;     /* 当前状态 */
    dialog_type_t dialog_type; /* 当前对话框类型 (n1832) */
    int n658255;            /* 当前Y坐标基准 (658255或693535) */
} text_state_t_struct;

/* 全局变量 */
static uint8_t* font_data = NULL;
static uint8_t* fdtxt_data = NULL;
static size_t fdtxt_file_size = 0;
static int fdtxt_count = 0;
static uint32_t fdtxt_offsets[146];

static uint8_t* dato_data = NULL;
static size_t dato_file_size = 0;
static uint32_t dato_palette[256];

#define PORTRAIT_MAX_FRAMES 4
static uint8_t* portrait_frames[PORTRAIT_MAX_FRAMES];
static int portrait_width = 0;
static int portrait_height = 0;
static int current_frame = 0;
static uint32_t frame_timer = 0;
static bool portrait_loaded = false;

static SDL_Window* window = NULL;
static SDL_Renderer* renderer = NULL;
static SDL_Texture* texture = NULL;
static uint32_t* screen_buffer = NULL;

/* ============================================================
 * 调色板转换 (6位VGA RGB -> 32位RGBA)
 * 1:1还原VGA DAC格式: 存储顺序为RGB (6位/分量)
 * SDL ARGB8888格式: A(8) R(8) G(8) B(8)
 * ============================================================ */
static void load_palette_6bit(uint8_t* pal, int size)
{
    int count = size / 3;
    for (int i = 0; i < count && i < 256; i++) {
        uint8_t r6 = pal[i * 3] & 0x3F;
        uint8_t g6 = pal[i * 3 + 1] & 0x3F;
        uint8_t b6 = pal[i * 3 + 2] & 0x3F;
        /* 6位转8位: (v << 2) | (v >> 4) */
        uint8_t r8 = (r6 << 2) | (r6 >> 4);
        uint8_t g8 = (g6 << 2) | (g6 >> 4);
        uint8_t b8 = (b6 << 2) | (b6 >> 4);
        /* SDL ARGB8888: (0xFF << 24) | (R << 16) | (G << 8) | B */
        dato_palette[i] = (0xFFu << 24) | (r8 << 16) | (g8 << 8) | b8;
    }
}

/* ============================================================
 * RLE解压缩 (1:1还原游戏逻辑)
 * ============================================================ */
static int rle_decompress(const uint8_t* src, int src_size, uint8_t* dst, int max_pixels)
{
    int i = 0, j = 0;
    while (i < src_size && j < max_pixels) {
        uint8_t byte = src[i++];
        if (byte >= 0xC0) {
            if (i < src_size) {
                int count = byte & 0x3F;
                if (count == 0) count = 64;
                uint8_t val = src[i++];
                for (int k = 0; k < count && j < max_pixels; k++)
                    dst[j++] = val;
            }
        } else {
            dst[j++] = byte;
        }
    }
    return j;
}

/* ============================================================
 * 加载DATO.DAT头像 (4帧动画)
 * ============================================================ */
static int load_portrait(int index)
{
    if (!dato_data || index < 0) return -1;
    
    uint32_t count;
    memcpy(&count, dato_data + 6, 4);
    if ((uint32_t)index >= count - 1) return -1;
    
    uint32_t off_start, off_end;
    memcpy(&off_start, dato_data + 10 + index * 4, 4);
    memcpy(&off_end, dato_data + 10 + (index + 1) * 4, 4);
    if (off_start >= dato_file_size || off_end > dato_file_size) return -1;
    
    uint32_t res_size = off_end - off_start;
    uint8_t* res_data = dato_data + off_start;
    
    if (res_size < 20) return -1;
    
    int16_t w, h;
    memcpy(&w, res_data + 16, 2);
    memcpy(&h, res_data + 18, 2);
    if (w <= 0 || h <= 0 || w > 512 || h > 512) return -1;
    
    int pixel_count = w * h;
    
    for (int i = 0; i < PORTRAIT_MAX_FRAMES; i++) {
        free(portrait_frames[i]);
        portrait_frames[i] = NULL;
    }
    
    uint32_t frame_offs[3];
    memcpy(&frame_offs[0], res_data + 4, 4);
    memcpy(&frame_offs[1], res_data + 8, 4);
    memcpy(&frame_offs[2], res_data + 12, 4);
    
    for (int i = 0; i < 3; i++) {
        if (frame_offs[i] >= res_size || frame_offs[i] < 20) return -1;
    }
    
    struct { int start, end; } regions[4];
    regions[0].start = 20;         regions[0].end = frame_offs[0];
    regions[1].start = frame_offs[0] + 4; regions[1].end = frame_offs[1];
    regions[2].start = frame_offs[1] + 4; regions[2].end = frame_offs[2];
    regions[3].start = frame_offs[2] + 4; regions[3].end = res_size;
    
    for (int i = 0; i < 4; i++) {
        int comp_size = regions[i].end - regions[i].start;
        if (comp_size <= 0) return -1;
        
        portrait_frames[i] = (uint8_t*)malloc(pixel_count);
        if (!portrait_frames[i]) return -1;
        
        int decoded = rle_decompress(res_data + regions[i].start, comp_size, portrait_frames[i], pixel_count);
        if (decoded != pixel_count) {
            for (int j = 0; j <= i; j++) { free(portrait_frames[j]); portrait_frames[j] = NULL; }
            return -1;
        }
    }
    
    portrait_width = w;
    portrait_height = h;
    current_frame = 0;
    frame_timer = 0;
    portrait_loaded = true;
    
    return 0;
}

static void update_portrait_frame(uint32_t delta_ms)
{
    if (!portrait_loaded) return;
    frame_timer += delta_ms;
    if (frame_timer >= 150) {
        frame_timer = 0;
        current_frame = (current_frame + 1) % PORTRAIT_MAX_FRAMES;
    }
}

/* ============================================================
 * 渲染头像到对话框内 (带缩放)
 * ============================================================ */
static void render_portrait(int dialog_type)
{
    if (!portrait_loaded || !portrait_frames[current_frame]) return;
    
    uint8_t* frame = portrait_frames[current_frame];
    
    int px_start, py_start;
    if (dialog_type == DIALOG_TYPE_F) {
        px_start = PORTRAIT_F_X;
        py_start = PORTRAIT_F_Y;
    } else {
        px_start = PORTRAIT_S_X;
        py_start = PORTRAIT_S_Y;
    }
    
    for (int y = 0; y < PORTRAIT_H; y++) {
        for (int x = 0; x < PORTRAIT_W; x++) {
            int px = px_start + x;
            int py = py_start + y;
            if (px < 0 || px >= SCREEN_WIDTH || py < 0 || py >= SCREEN_HEIGHT) continue;
            
            int src_x = x * portrait_width / PORTRAIT_W;
            int src_y = y * portrait_height / PORTRAIT_H;
            
            if (src_x < portrait_width && src_y < portrait_height) {
                uint8_t idx = frame[src_y * portrait_width + src_x];
                if (idx != 0) {
                    screen_buffer[py * SCREEN_WIDTH + px] = dato_palette[idx];
                }
            }
        }
    }
}

/* ============================================================
 * 绘制对话框 (背景+边框)
 * ============================================================ */
static void draw_dialog_box(int dialog_type)
{
    int dy, dh;
    if (dialog_type == DIALOG_TYPE_F) {
        dy = DIALOG_F_Y;
        dh = DIALOG_H;
    } else {
        dy = DIALOG_S_Y;
        dh = DIALOG_H;
    }
    
    /* 背景填充 */
    for (int y = dy; y < dy + dh; y++) {
        for (int x = DIALOG_X; x < DIALOG_X + DIALOG_W; x++) {
            screen_buffer[y * SCREEN_WIDTH + x] = DIALOG_BG_COLOR;
        }
    }
    
    /* 外边框 (亮色) */
    for (int x = DIALOG_X; x < DIALOG_X + DIALOG_W; x++) {
        screen_buffer[dy * SCREEN_WIDTH + x] = DIALOG_BORDER_COLOR;
        screen_buffer[(dy + dh - 1) * SCREEN_WIDTH + x] = DIALOG_BORDER_COLOR;
    }
    for (int y = dy; y < dy + dh; y++) {
        screen_buffer[y * SCREEN_WIDTH + DIALOG_X] = DIALOG_BORDER_COLOR;
        screen_buffer[y * SCREEN_WIDTH + DIALOG_X + DIALOG_W - 1] = DIALOG_BORDER_COLOR;
    }
    
    /* 内边框 (暗色) */
    int ix = DIALOG_X + 1, iy = dy + 1;
    int iw = DIALOG_W - 2, ih = dh - 2;
    uint32_t inner_color = 0xFF404040;
    for (int x = ix; x < ix + iw; x++) {
        screen_buffer[iy * SCREEN_WIDTH + x] = inner_color;
        screen_buffer[(iy + ih - 1) * SCREEN_WIDTH + x] = inner_color;
    }
    for (int y = iy; y < iy + ih; y++) {
        screen_buffer[y * SCREEN_WIDTH + ix] = inner_color;
        screen_buffer[y * SCREEN_WIDTH + ix + iw - 1] = inner_color;
    }
}

/* ============================================================
 * 文件加载
 * ============================================================ */
static uint8_t* load_file(const char* filename, size_t* out_size)
{
    FILE* fp = fopen(filename, "rb");
    if (!fp) { fprintf(stderr, "无法打开: %s\n", filename); return NULL; }
    fseek(fp, 0, SEEK_END);
    size_t size = ftell(fp);
    fseek(fp, 0, SEEK_SET);
    uint8_t* data = (uint8_t*)malloc(size);
    if (data) fread(data, 1, size, fp);
    fclose(fp);
    if (out_size) *out_size = size;
    return data;
}

static uint8_t* load_dat_resource(uint8_t* dat, size_t dat_size, int index, int* out_size)
{
    if (dat_size < 10) return NULL;
    uint32_t count;
    memcpy(&count, dat + 6, 4);
    if (index < 0 || (uint32_t)index >= count - 1) return NULL;
    
    uint32_t s, e;
    memcpy(&s, dat + 10 + index * 4, 4);
    memcpy(&e, dat + 10 + (index + 1) * 4, 4);
    if (s >= dat_size || e > dat_size) return NULL;
    
    size_t sz = e - s;
    uint8_t* buf = (uint8_t*)malloc(sz);
    if (buf) memcpy(buf, dat + s, sz);
    if (out_size) *out_size = (int)sz;
    return buf;
}

/* 角色数据库条目（每项80字节）- 从汇编代码dword_53A45还原 */
typedef struct {
    uint8_t name[8];    /* 偏移 0-7: 角色名称 */
    uint8_t id;          /* 偏移 8: 角色ID */
    uint8_t dato_idx;    /* 偏移 7: DATO头像索引 */
    /* 其他字段... */
} char_db_entry_t;

/* 从角色数据库获取DATO头像索引 */
static int get_dato_idx_from_char_id(int char_id) {
    if (!dato_data) return -1;
    
    /* 加载角色数据库 */
    int db_size = 0;
    uint8_t* db = load_dat_resource(dato_data, dato_file_size, 0, &db_size);
    if (!db) return -1;
    
    int entry_count = db_size / 80;
    int dato_idx = -1;
    
    /* 在角色数据库中查找匹配的ID */
    for (int i = 0; i < entry_count; i++) {
        if (db[i * 80 + 8] == (uint8_t)char_id) {
            dato_idx = db[i * 80 + 7];
            break;
        }
    }
    
    free(db);
    return dato_idx;
}

/* 直接从角色数据库获取DATO索引（TEXT_CHAR_F/S使用）*/
static int get_dato_idx_from_char_db_index(int char_db_index) {
    if (!dato_data) return -1;
    
    int db_size = 0;
    uint8_t* db = load_dat_resource(dato_data, dato_file_size, 0, &db_size);
    if (!db) return -1;
    
    int entry_count = db_size / 80;
    int dato_idx = -1;
    
    if (char_db_index >= 0 && char_db_index < entry_count) {
        dato_idx = db[char_db_index * 80 + 7];
    }
    
    free(db);
    return dato_idx;
}

/* ============================================================
 * 字体渲染 (1:1还原sub_4ED7A)
 * ============================================================ */
static void render_char(int16_t word, int x, int y, uint32_t fg, uint32_t bg, bool draw_bg)
{
    if (!font_data || word < 0 || word >= FONT_MAX_CHARS) return;
    
    uint8_t* cdata = font_data + word * 32;
    
    for (int row = 0; row < 16; row++) {
        uint16_t bits;
        memcpy(&bits, cdata + row * 2, 2);
        bits = ((bits & 0xFF) << 8) | ((bits >> 8) & 0xFF);
        
        for (int col = 0; col < 16; col++) {
            int px = x + col, py = y + row;
            if (px < 0 || px >= SCREEN_WIDTH || py < 0 || py >= SCREEN_HEIGHT) continue;
            if (bits & (1 << (15 - col))) {
                screen_buffer[py * SCREEN_WIDTH + px] = fg;
            } else if (draw_bg) {
                screen_buffer[py * SCREEN_WIDTH + px] = bg;
            }
        }
    }
}

/* 切换对话框类型 (1:1还原sub_15F84)
 * 
 * 根据汇编代码:
 * - TEXT_PORTRAIT_F(-17) / TEXT_CHAR_F(-19): 设置 n1832=1832, n658255=658255
 * - TEXT_PORTRAIT_S(-18) / TEXT_CHAR_S(-20): 设置 n1832=36887, n658255=693535
 * - 重置: x, y, line_count, n3=0
 */
static void switch_dialog_type(text_state_t_struct* state, dialog_type_t new_type)
{
    if (state->dialog_type != new_type) {
        state->dialog_type = new_type;
        state->n658255 = (new_type == DIALOG_TYPE_F) ? 658255 : 693535;
        state->line_count = 0;
        
        /* 根据对话框类型设置起始位置 */
        if (new_type == DIALOG_TYPE_F) {
            state->x = TEXT_F_START_X;
            state->y = TEXT_F_START_Y;
        } else {
            state->x = TEXT_S_START_X;
            state->y = TEXT_S_START_Y;
        }
    }
}

/* 文本渲染 (1:1还原sub_15F84核心循环)
 * 
 * 游戏逻辑 (按汇编顺序):
 * - TEXT_END(-1): 文本结束，退出循环
 * - TEXT_NEWLINE(-2): 换行，n3++, 计算n658255_1
 * - TEXT_NEWLINE2(-3): 换行，n3++, 计算n658255_1, 等待按键
 * - TEXT_RECURSE1(-4): 递归调用sub_15F84
 * - TEXT_RECURSE2(-5): 递归调用sub_15F84
 * - TEXT_SHOW_NUM(-6): 显示数字
 * - TEXT_PORTRAIT_F(-17): 切换对话框F, 重置n3=0
 * - TEXT_PORTRAIT_S(-18): 切换对话框S, 重置n3=0
 * - TEXT_CHAR_F(-19): 切换对话框F, 重置n3=0
 * - TEXT_CHAR_S(-20): 切换对话框S, 重置n3=0
 * - 默认: 渲染字符, n658255_1 += 16 (a9=205, 但X方向增量是CHAR_WIDTH=16)
 * 
 * Y坐标计算: actual_y = dialog_base_y + line_count * CHAR_HEIGHT
 * X坐标计算: actual_x = dialog_text_start_x + char_index * CHAR_WIDTH
 * ============================================================ */
static void render_text_item(text_state_t_struct* state, int start_x, int start_y, bool wait_for_key, int16_t* text_end)
{
    if (!state->ptr || !text_end) return;
    
    (void)start_x;
    (void)start_y;
    
    /* 1:1还原sub_15F84主循环 */
    while (1) {
        if (state->ptr >= text_end) {
            state->state = TEXT_DONE;
            return;
        }
        
        int16_t word = *state->ptr;
        
        if (word == TEXT_END) {
            state->ptr++;
            state->state = TEXT_DONE;
            if (wait_for_key) {
                SDL_Event ev;
                bool waiting = true;
                while (waiting) {
                    while (SDL_PollEvent(&ev)) {
                        if (ev.type == SDL_KEYDOWN || ev.type == SDL_QUIT) {
                            waiting = false;
                            break;
                        }
                    }
                    SDL_Delay(16);
                }
            }
            return;
        }
        
        /* TEXT_NEWLINE (-2) */
        if (word == TEXT_NEWLINE) {
            state->ptr++;
            state->char_index = 0;
            state->line_count++;
            continue;
        }
        
        /* TEXT_NEWLINE2 (-3) */
        if (word == TEXT_NEWLINE2) {
            state->ptr++;
            state->char_index = 0;
            state->line_count++;
            
            if (wait_for_key) {
                SDL_Event ev;
                bool waiting = true;
                while (waiting) {
                    while (SDL_PollEvent(&ev)) {
                        if (ev.type == SDL_KEYDOWN || ev.type == SDL_QUIT) {
                            waiting = false;
                            break;
                        }
                    }
                    SDL_Delay(16);
                }
            }
            continue;
        }
        
        /* TEXT_RECURSE1 (-4) */
        if (word == TEXT_RECURSE1) {
            state->ptr++;
            continue;
        }
        
        /* TEXT_RECURSE2 (-5) */
        if (word == TEXT_RECURSE2) {
            state->ptr++;
            continue;
        }
        
        /* TEXT_SHOW_NUM (-6) */
        if (word == TEXT_SHOW_NUM) {
            state->ptr++;
            int dy = (state->dialog_type == DIALOG_TYPE_F) ? DIALOG_F_Y : DIALOG_S_Y;
            int dx = (state->dialog_type == DIALOG_TYPE_F) ? TEXT_F_START_X : TEXT_S_START_X;
            int actual_x = dx + state->char_index * CHAR_WIDTH;
            int actual_y = dy + 8 + state->line_count * CHAR_HEIGHT;
            render_char(0, actual_x, actual_y, DIALOG_TEXT_FG, DIALOG_TEXT_BG, true);
            state->char_index++;
            continue;
        }
        
        /* TEXT_PORTRAIT_F (-17) */
        if (word == TEXT_PORTRAIT_F) {
            state->ptr++;
            int16_t pid = *state->ptr++;
            
            /* 切换到下方对话框，重置行计数 */
            switch_dialog_type(state, DIALOG_TYPE_F);
            
            int dato_idx = get_dato_idx_from_char_id(pid);
            if (dato_idx >= 0) {
                load_portrait(dato_idx);
            }
            continue;
        }
        
        /* TEXT_PORTRAIT_S (-18) */
        if (word == TEXT_PORTRAIT_S) {
            state->ptr++;
            int16_t pid = *state->ptr++;
            
            /* 切换到上方对话框，重置行计数 */
            switch_dialog_type(state, DIALOG_TYPE_S);
            
            int dato_idx = get_dato_idx_from_char_id(pid);
            if (dato_idx >= 0) {
                load_portrait(dato_idx);
            }
            continue;
        }
        
        /* TEXT_CHAR_F (-19) */
        if (word == TEXT_CHAR_F) {
            state->ptr++;
            int16_t cid = *state->ptr++;
            
            /* 切换到下方对话框，重置行计数 */
            switch_dialog_type(state, DIALOG_TYPE_F);
            
            int dato_idx = get_dato_idx_from_char_db_index(cid);
            if (dato_idx >= 0) {
                load_portrait(dato_idx);
            }
            continue;
        }
        
        /* TEXT_CHAR_S (-20) */
        if (word == TEXT_CHAR_S) {
            state->ptr++;
            int16_t cid = *state->ptr++;
            
            /* 切换到上方对话框，重置行计数 */
            switch_dialog_type(state, DIALOG_TYPE_S);
            
            int dato_idx = get_dato_idx_from_char_db_index(cid);
            if (dato_idx >= 0) {
                load_portrait(dato_idx);
            }
            continue;
        }
        
        /* 默认：渲染字符 */
        if (word >= 0 && word < FONT_MAX_CHARS) {
            int dy = (state->dialog_type == DIALOG_TYPE_F) ? DIALOG_F_Y : DIALOG_S_Y;
            int dx = (state->dialog_type == DIALOG_TYPE_F) ? TEXT_F_START_X : TEXT_S_START_X;
            
            /* 检查是否超出对话框行数限制 */
            int max_lines = (DIALOG_H - 16) / CHAR_HEIGHT;  /* 对话框高度减去上下边距，除以行高 */
            if (state->line_count >= max_lines) {
                /* 超出当前对话框，停止渲染 */
                state->state = TEXT_DONE;
                return;
            }
            
            /* 自动换行检测 */
            if (state->char_index * CHAR_WIDTH > TEXT_WRAP_X - dx) {
                state->char_index = 0;
                state->line_count++;
                
                /* 换行后再次检查行数限制 */
                if (state->line_count >= max_lines) {
                    state->state = TEXT_DONE;
                    return;
                }
            }
            
            int actual_x = dx + state->char_index * CHAR_WIDTH;
            int actual_y = dy + 8 + state->line_count * CHAR_HEIGHT;
            
            /* 确保只在当前对话框内渲染 */
            if (actual_y >= dy + 8 && actual_y < dy + DIALOG_H - 8) {
                render_char(word, actual_x, actual_y, DIALOG_TEXT_FG, DIALOG_TEXT_BG, true);
            }
            state->char_index++;
        }
        
        state->ptr++;
    }
}

/* ============================================================
 * 获取文本项
 * ============================================================ */
static int16_t* get_sub_text(int res_idx, int sub_idx, int16_t** out_end)
{
    uint32_t rs = fdtxt_offsets[res_idx];
    uint32_t re = (res_idx + 1 < fdtxt_count && fdtxt_offsets[res_idx + 1] < fdtxt_file_size)
                  ? fdtxt_offsets[res_idx + 1] : fdtxt_file_size;
    if (rs >= fdtxt_file_size) return NULL;
    
    uint8_t* rd = fdtxt_data + rs;
    size_t rsz = re - rs;
    if (rsz < 2) return NULL;
    
    int16_t sc;
    memcpy(&sc, rd, 2);
    
    int16_t* offs = (int16_t*)(rd + 2);
    
    if (sub_idx < 0 || sub_idx >= sc) return NULL;
    
    /* 获取当前子项的字节偏移（直接是字节偏移，不是word索引）*/
    int32_t byte_offset = offs[sub_idx];
    if (byte_offset < 0 || byte_offset >= (int32_t)rsz) return NULL;
    
    int16_t* text_start = (int16_t*)(rd + byte_offset);
    
    if (out_end) {
        /* 计算text_end：从当前子项开始搜索TEXT_END(-1)标记 */
        int16_t* p = text_start;
        int16_t* max_p = (int16_t*)(rd + rsz);
        
        while (p < max_p) {
            if (*p == -1) {
                /* 游戏原版: TEXT_END不消耗，返回指针仍然指向TEXT_END */
                *out_end = p;
                goto done;
            }
            p++;
        }
        
        /* 没找到TEXT_END，使用下一个子项的偏移或资源结尾 */
        if (sub_idx + 1 < sc && offs[sub_idx + 1] >= 0 && offs[sub_idx + 1] < (int32_t)rsz) {
            *out_end = (int16_t*)(rd + offs[sub_idx + 1]);
        } else {
            *out_end = max_p;
        }
    done:;
    }
    
    return text_start;
}

static int get_sub_count(int res_idx)
{
    uint32_t rs = fdtxt_offsets[res_idx];
    if (rs >= fdtxt_file_size) return 0;
    
    uint8_t* rd = fdtxt_data + rs;
    size_t rsz;
    uint32_t re = (res_idx + 1 < fdtxt_count && fdtxt_offsets[res_idx + 1] < fdtxt_file_size)
                  ? fdtxt_offsets[res_idx + 1] : fdtxt_file_size;
    rsz = re - rs;
    if (rsz < 2) return 0;
    
    int16_t sc;
    memcpy(&sc, rd, 2);
    
    return sc;
}

/* ============================================================
 * SDL
 * ============================================================ */
static int sdl_init(void)
{
    if (SDL_Init(SDL_INIT_VIDEO) < 0) { fprintf(stderr, "SDL失败: %s\n", SDL_GetError()); return -1; }
    window = SDL_CreateWindow("FDTXT 对话框测试", SDL_WINDOWPOS_CENTERED, SDL_WINDOWPOS_CENTERED,
                              SCREEN_WIDTH * SCALE_FACTOR, SCREEN_HEIGHT * SCALE_FACTOR, SDL_WINDOW_SHOWN);
    if (!window) return -1;
    renderer = SDL_CreateRenderer(window, -1, SDL_RENDERER_ACCELERATED);
    if (!renderer) return -1;
    texture = SDL_CreateTexture(renderer, SDL_PIXELFORMAT_ARGB8888, SDL_TEXTUREACCESS_STREAMING,
                                SCREEN_WIDTH, SCREEN_HEIGHT);
    if (!texture) return -1;
    screen_buffer = (uint32_t*)malloc(SCREEN_WIDTH * SCREEN_HEIGHT * 4);
    return screen_buffer ? 0 : -1;
}

static void render_frame(void)
{
    SDL_UpdateTexture(texture, NULL, screen_buffer, SCREEN_WIDTH * 4);
    SDL_RenderClear(renderer);
    SDL_Rect dst = {0, 0, SCREEN_WIDTH * SCALE_FACTOR, SCREEN_HEIGHT * SCALE_FACTOR};
    SDL_RenderCopy(renderer, texture, NULL, &dst);
    SDL_RenderPresent(renderer);
}

static void clear_screen(void) { memset(screen_buffer, 0, SCREEN_WIDTH * SCREEN_HEIGHT * 4); }

static void cleanup(void)
{
    free(screen_buffer);
    if (texture) SDL_DestroyTexture(texture);
    if (renderer) SDL_DestroyRenderer(renderer);
    if (window) SDL_DestroyWindow(window);
    SDL_Quit();
}

/* ============================================================
 * 主函数 - 游戏对话逻辑循环
 * ============================================================ */
int main(int argc, char* argv[])
{
    (void)argc; (void)argv;
    
    printf("=== FDTXT 对话框测试 (双对话框系统) ===\n\n");
    
    /* 加载字体 */
    printf("1. 加载字体...\n");
    size_t osz;
    uint8_t* od = load_file(FONT_DAT_PATH, &osz);
    if (!od) return 1;
    
    int fsz = 0;
    font_data = load_dat_resource(od, osz, 3, &fsz);
    
    /* 使用索引98的调色板 (暖色调, 53个肤色色调, 适合对话场景) */
    int psz;
    uint8_t* pd = load_dat_resource(od, osz, 98, &psz);
    if (pd && psz == 768) {
        load_palette_6bit(pd, psz);
        printf("   调色板: 索引98 (暖色调)\n");
    }
    free(pd); free(od);
    if (!font_data) { fprintf(stderr, "字体加载失败\n"); return 1; }
    printf("   字体: %d 字符\n\n", fsz / 32);
    
    /* 加载DATO */
    printf("2. 加载DATO.DAT...\n");
    dato_data = load_file(DATO_DAT_PATH, &dato_file_size);
    if (!dato_data) { free(font_data); return 1; }
    {
        uint32_t dc;
        memcpy(&dc, dato_data + 6, 4);
        printf("   头像数量: %d\n\n", dc);
    }
    
    /* 加载FDTXT */
    printf("3. 加载FDTXT.DAT...\n");
    fdtxt_data = load_file(FDTXT_DAT_PATH, &fdtxt_file_size);
    if (!fdtxt_data) { free(font_data); return 1; }
    
    memcpy(&fdtxt_count, fdtxt_data + 6, 4);
    for (int i = 0; i < fdtxt_count && i < 146; i++)
        memcpy(&fdtxt_offsets[i], fdtxt_data + 10 + i * 4, 4);
    printf("   资源集: %d\n\n", fdtxt_count);
    
    /* SDL */
    if (sdl_init() < 0) { free(font_data); free(fdtxt_data); return 1; }
    
    int cur_res = 0, cur_sub = 0;
    bool need_render = true;
    bool text_initialized = false;
    bool text_done = false;  /* 标记文本是否渲染完成 */
    
    /* 文本状态机 (1:1还原sub_15F84) */
    text_state_t_struct text_state;
    text_state.ptr = NULL;
    text_state.x = TEXT_F_START_X;
    text_state.y = TEXT_F_START_Y;
    text_state.line_count = 0;
    text_state.state = TEXT_CONTINUE;
    text_state.dialog_type = DIALOG_TYPE_F;  /* 默认下方对话框 */
    text_state.n658255 = 658255;
    
    printf("控制:\n");
    printf("  上/下: 切换资源集 (0-%d)\n", fdtxt_count - 1);
    printf("  左/右: 切换子文本项\n");
    printf("  空格/回车/Z/X: 继续/切换\n");
    printf("  ESC: 退出\n\n");
    
    bool running = true;
    
    while (running) {
        /* 处理事件 */
        SDL_Event ev;
        while (SDL_PollEvent(&ev)) {
            if (ev.type == SDL_QUIT) { running = false; break; }
            if (ev.type == SDL_KEYDOWN) {
                switch (ev.key.keysym.sym) {
                    case SDLK_ESCAPE: running = false; break;
                    case SDLK_UP:
                        if (cur_res > 0) {
                            cur_res--; cur_sub = 0;
                            text_initialized = false;
                            text_done = false;
                            need_render = true;
                        }
                        break;
                    case SDLK_DOWN:
                        if (cur_res < fdtxt_count - 1) {
                            cur_res++; cur_sub = 0;
                            text_initialized = false;
                            text_done = false;
                            need_render = true;
                        }
                        break;
                    case SDLK_LEFT:
                        if (cur_sub > 0) {
                            cur_sub--;
                            text_initialized = false;
                            text_done = false;
                            need_render = true;
                        }
                        break;
                    case SDLK_RIGHT:
                        {
                            int sc = get_sub_count(cur_res);
                            if (cur_sub < sc - 1) {
                                cur_sub++;
                                text_initialized = false;
                                text_done = false;
                                need_render = true;
                            }
                        }
                        break;
                    case SDLK_SPACE:
                    case SDLK_RETURN:
                    case SDLK_z:
                    case SDLK_x:
                        if (!text_done) {
                            /* 继续渲染 */
                            if (text_state.state == TEXT_WAIT_KEY_NEWLINE2 || text_state.state == TEXT_WAIT_KEY_END) {
                                text_state.state = TEXT_CONTINUE;
                            }
                            need_render = true;
                        } else {
                            /* 切换到下一项 */
                            int sc = get_sub_count(cur_res);
                            if (cur_sub < sc - 1) {
                                cur_sub++;
                                text_initialized = false;
                                text_done = false;
                                need_render = true;
                            }
                        }
                        break;
                }
            }
        }
        
        /* 渲染 */
        if (need_render) {
            clear_screen();
            
            /* 绘制双对话框 */
            draw_dialog_box(DIALOG_TYPE_F);
            draw_dialog_box(DIALOG_TYPE_S);
            
            /* 渲染当前对话框的头像 */
            render_portrait(text_state.dialog_type);
            
            /* 初始化文本状态 */
            if (!text_initialized) {
                text_state.dialog_type = DIALOG_TYPE_F;
                text_state.n658255 = 658255;
                text_state.x = TEXT_F_START_X;
                text_state.y = TEXT_F_START_Y;
                text_state.line_count = 0;
                text_state.state = TEXT_CONTINUE;
                
                int16_t* txt_end = NULL;
                int16_t* txt = get_sub_text(cur_res, cur_sub, &txt_end);
                if (txt) {
                    text_state.ptr = txt;
                }
                text_initialized = true;
            }
            
            /* 渲染文本 */
            if (text_state.ptr && text_state.state != TEXT_DONE) {
                int16_t* txt_end = NULL;
                get_sub_text(cur_res, cur_sub, &txt_end);
                render_text_item(&text_state, TEXT_F_START_X, TEXT_F_START_Y, true, txt_end);
            }
            
            render_frame();
            
            int sc = get_sub_count(cur_res);
            printf("\r资源集: %d/%d  子项: %d/%d  对话框: %s ", 
                   cur_res, fdtxt_count-1, cur_sub, sc > 0 ? sc-1 : 0,
                   text_state.dialog_type == DIALOG_TYPE_F ? "下方(F)" : "上方(S)");
            fflush(stdout);
            
            need_render = false;
        }
        
        SDL_Delay(16);
    }
    
    cleanup();
    for (int i = 0; i < PORTRAIT_MAX_FRAMES; i++) free(portrait_frames[i]);
    free(dato_data); free(font_data); free(fdtxt_data);
    printf("\n完成\n");
    return 0;
}
