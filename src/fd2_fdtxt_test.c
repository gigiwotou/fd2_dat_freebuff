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
#define TEXT_DELAY      -2
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

/* 对话框常量 - 根据汇编代码sub_165AC和实际游戏截图还原 */
#define DIALOG_W          310
#define DIALOG_H          86
/* 游戏对话框颜色：蓝色 (ARGB: 0xFF3848A0 = RGB 56,72,160) */
/* SDL_PIXELFORMAT_ARGB8888使用0xAARRGGBB格式 */
#define DIALOG_BG_COLOR   0xFF3848A0
#define DIALOG_BORDER_OUT 0xFFFFFFFF
#define DIALOG_BORDER_IN  0xFF808080
#define DIALOG_TEXT_FG    0xFFFFFFFF
#define DIALOG_TEXT_BG    0xFF3848A0

/* 头像常量 - 80x80像素，与DATO原始资源一致，1:1渲染不缩放 */
#define PORTRAIT_W        80
#define PORTRAIT_H        80

/* 下方对话框 (角色F) - 位于屏幕底部，头像在左侧 */
/* 根据游戏截图：对话框底部对齐屏幕底部 */
#define DIALOG_F_Y        (SCREEN_HEIGHT - DIALOG_H)  /* 200-86=114 */
#define DIALOG_F_X        ((SCREEN_WIDTH - DIALOG_W) / 2)  /* (320-310)/2=5 */
#define PORTRAIT_F_X      (DIALOG_F_X + 8)  /* 5+8=13 */
#define PORTRAIT_F_Y      (DIALOG_F_Y + 8)  /* 114+8=122 */
#define TEXT_F_START_X    (DIALOG_F_X + 8 + PORTRAIT_W + 8)  /* 5+8+80+8=101 */
#define TEXT_F_START_Y    (DIALOG_F_Y + 8)  /* 114+8=122 */
#define TEXT_F_END_X      (DIALOG_F_X + DIALOG_W - 8)  /* 5+310-8=307 */

/* 上方对话框 (角色S) - 位于屏幕顶部，头像在右侧 */
#define DIALOG_S_Y        8
#define DIALOG_S_X        ((SCREEN_WIDTH - DIALOG_W) / 2)  /* 5 */
#define PORTRAIT_S_X      (DIALOG_S_X + DIALOG_W - 8 - PORTRAIT_W)  /* 5+310-8-80=227 */
#define PORTRAIT_S_Y      (DIALOG_S_Y + 8)  /* 8+8=16 */
#define TEXT_S_START_X    (DIALOG_S_X + 8)  /* 5+8=13 */
#define TEXT_S_START_Y    (DIALOG_S_Y + 8)  /* 8+8=16 */
#define TEXT_S_END_X      (DIALOG_S_X + DIALOG_W - 8 - PORTRAIT_W - 8)  /* 5+310-8-80-8=219 */

#define TEXT_MAX_LINES    3

/* 对话框类型 (1:1还原n1832) */
typedef enum {
    DIALOG_TYPE_NONE = 0,
    DIALOG_TYPE_F = 1832,   /* 下方对话框 (0x728) */
    DIALOG_TYPE_S = 36887   /* 上方对话框 (0x9017) */
} dialog_type_t;

/* 文本状态 (1:1还原sub_15F84) */
typedef enum {
    TEXT_STATE_CONTINUE = 0,
    TEXT_STATE_WAIT_KEY,
    TEXT_STATE_DONE
} text_state_e;

/* 文本状态结构体 - 1:1还原sub_15F84局部变量 */
typedef struct {
    int16_t* ptr;           /* 当前解析位置 */
    int16_t* text_start;    /* 文本起始位置（用于重放） */
    int16_t* render_end;    /* 渲染终点（用于WAIT_KEY状态下重新渲染） */
    int n658255_1;
    int n658255;
    int n3;
    int n1832;
    int v35;
    int n2;
    text_state_e state;
    int pixel_x;  /* 当前渲染的X坐标 */
    int pixel_y;  /* 当前渲染的Y坐标 */
} text_state_t;

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
 * ============================================================ */
static void load_palette_6bit(uint8_t* pal, int size)
{
    int count = size / 3;
    for (int i = 0; i < count && i < 256; i++) {
        uint8_t r6 = pal[i * 3] & 0x3F;
        uint8_t g6 = pal[i * 3 + 1] & 0x3F;
        uint8_t b6 = pal[i * 3 + 2] & 0x3F;
        uint8_t r8 = (r6 << 2) | (r6 >> 4);
        uint8_t g8 = (g6 << 2) | (g6 >> 4);
        uint8_t b8 = (b6 << 2) | (b6 >> 4);
        dato_palette[i] = (0xFFu << 24) | (r8 << 16) | (g8 << 8) | b8;
    }
}

/* ============================================================
 * RLE解压缩
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
    if ((uint32_t)index >= count - 1) {
        printf("   [load_portrait] 警告: 索引%d超出范围 (count=%u)\n", index, count);
        return -1;
    }
    
    uint32_t off_start, off_end;
    uint32_t offset_pos = 10 + index * 4;
    memcpy(&off_start, dato_data + offset_pos, 4);
    memcpy(&off_end, dato_data + offset_pos + 4, 4);
    
    printf("   [load_portrait] 加载索引%d, 偏移表位置=%u, start=%u, end=%u, 文件大小=%zu\n",
           index, offset_pos, off_start, off_end, dato_file_size);
    
    /* 检查偏移是否有效（必须在文件大小内） */
    if (off_start >= dato_file_size || off_end > dato_file_size) {
        printf("   [load_portrait] 警告: 索引%d的偏移无效 (start=%u, end=%u, size=%zu)\n", 
               index, off_start, off_end, dato_file_size);
        return -1;
    }
    
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
    regions[0].start = 20;
    regions[0].end = frame_offs[0];
    regions[1].start = frame_offs[0] + 4;
    regions[1].end = frame_offs[1];
    regions[2].start = frame_offs[1] + 4;
    regions[2].end = frame_offs[2];
    regions[3].start = frame_offs[2] + 4;
    regions[3].end = res_size;
    
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
    
    printf("   加载头像[%d]: 原始尺寸=%dx%d\n", index, w, h);
    
    return 0;
}

/* ============================================================
 * 渲染头像到对话框内 (按比例缩放，保持原始纵横比)
 * ============================================================ */
static void render_portrait(dialog_type_t dialog_type)
{
    if (!portrait_loaded || !portrait_frames[current_frame]) return;
    
    uint8_t* frame = portrait_frames[current_frame];
    
    int px_start, py_start;
    if (dialog_type == DIALOG_TYPE_F) {
        px_start = PORTRAIT_F_X;
        py_start = PORTRAIT_F_Y;
    } else if (dialog_type == DIALOG_TYPE_S) {
        px_start = PORTRAIT_S_X;
        py_start = PORTRAIT_S_Y;
    } else {
        return;
    }
    
    /* 计算缩放比例，适应PORTRAIT_W x PORTRAIT_H显示区域，保持纵横比 */
    float scale_x = (float)PORTRAIT_W / portrait_width;
    float scale_y = (float)PORTRAIT_H / portrait_height;
    float scale = (scale_x < scale_y) ? scale_x : scale_y;
    
    int disp_w = (int)(portrait_width * scale);
    int disp_h = (int)(portrait_height * scale);
    
    /* 在显示区域内居中 */
    int offset_x = (PORTRAIT_W - disp_w) / 2;
    int offset_y = (PORTRAIT_H - disp_h) / 2;
    
    for (int y = 0; y < disp_h; y++) {
        for (int x = 0; x < disp_w; x++) {
            int px = px_start + offset_x + x;
            int py = py_start + offset_y + y;
            if (px < 0 || px >= SCREEN_WIDTH || py < 0 || py >= SCREEN_HEIGHT) continue;
            
            /* 映射显示像素回源像素 */
            int src_x = (int)(x / scale);
            int src_y = (int)(y / scale);
            
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
 * 绘制对话框
 * ============================================================ */
static void draw_dialog_box(dialog_type_t dialog_type)
{
    int dx, dy;
    if (dialog_type == DIALOG_TYPE_F) {
        dx = DIALOG_F_X;
        dy = DIALOG_F_Y;
    } else if (dialog_type == DIALOG_TYPE_S) {
        dx = DIALOG_S_X;
        dy = DIALOG_S_Y;
    } else {
        return;
    }
    
    /* 背景填充 */
    for (int y = dy; y < dy + DIALOG_H; y++) {
        for (int x = dx; x < dx + DIALOG_W; x++) {
            screen_buffer[y * SCREEN_WIDTH + x] = DIALOG_BG_COLOR;
        }
    }
    
    /* 外边框 */
    for (int x = dx; x < dx + DIALOG_W; x++) {
        screen_buffer[dy * SCREEN_WIDTH + x] = DIALOG_BORDER_OUT;
        screen_buffer[(dy + DIALOG_H - 1) * SCREEN_WIDTH + x] = DIALOG_BORDER_OUT;
    }
    for (int y = dy; y < dy + DIALOG_H; y++) {
        screen_buffer[y * SCREEN_WIDTH + dx] = DIALOG_BORDER_OUT;
        screen_buffer[y * SCREEN_WIDTH + dx + DIALOG_W - 1] = DIALOG_BORDER_OUT;
    }
    
    /* 内边框 */
    int ix = dx + 1, iy = dy + 1;
    int iw = DIALOG_W - 2, ih = DIALOG_H - 2;
    for (int x = ix; x < ix + iw; x++) {
        screen_buffer[iy * SCREEN_WIDTH + x] = DIALOG_BORDER_IN;
        screen_buffer[(iy + ih - 1) * SCREEN_WIDTH + x] = DIALOG_BORDER_IN;
    }
    for (int y = iy; y < iy + ih; y++) {
        screen_buffer[y * SCREEN_WIDTH + ix] = DIALOG_BORDER_IN;
        screen_buffer[y * SCREEN_WIDTH + ix + iw - 1] = DIALOG_BORDER_IN;
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

static int get_dato_idx_from_char_id(int char_id) {
    if (!dato_data) return -1;
    
    int db_size = 0;
    uint8_t* db = load_dat_resource(dato_data, dato_file_size, 0, &db_size);
    if (!db) return -1;
    
    int entry_count = db_size / 80;
    int dato_idx = -1;
    
    for (int i = 0; i < entry_count; i++) {
        if (db[i * 80 + 8] == (uint8_t)char_id) {
            dato_idx = db[i * 80 + 7];
            break;
        }
    }
    
    free(db);
    return dato_idx;
}

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
    
    int32_t byte_offset = offs[sub_idx];
    if (byte_offset < 0 || byte_offset >= (int32_t)rsz) return NULL;
    
    int16_t* text_start = (int16_t*)(rd + byte_offset);
    
    if (out_end) {
        int16_t* p = text_start;
        int16_t* max_p = (int16_t*)(rd + rsz);
        
        while (p < max_p) {
            if (*p == -1) {
                *out_end = p;
                goto done;
            }
            p++;
        }
        
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

/* ============================================================
 * 屏幕滚动 - 1:1还原sub_16E24
 * 当n3==3时调用，将屏幕内容上移，清空最后一行
 * ============================================================ */
static void scroll_screen(dialog_type_t dialog_type)
{
    int dialog_x, dialog_y;
    if (dialog_type == DIALOG_TYPE_F) {
        dialog_x = DIALOG_F_X;
        dialog_y = DIALOG_F_Y;
    } else if (dialog_type == DIALOG_TYPE_S) {
        dialog_x = DIALOG_S_X;
        dialog_y = DIALOG_S_Y;
    } else {
        return;
    }
    
    int text_area_x = dialog_x + 2;
    int text_area_y = dialog_y + 2;
    int text_width = 208;
    int text_height = DIALOG_H - 4;
    
    for (int y = text_area_y; y < text_area_y + text_height - 16; y++) {
        for (int x = text_area_x; x < text_area_x + text_width; x++) {
            int src_y = y + 16;
            if (src_y < SCREEN_HEIGHT) {
                screen_buffer[y * SCREEN_WIDTH + x] = screen_buffer[src_y * SCREEN_WIDTH + x];
            }
        }
    }
    
    for (int y = text_area_y + text_height - 16; y < text_area_y + text_height; y++) {
        for (int x = text_area_x; x < text_area_x + text_width; x++) {
            screen_buffer[y * SCREEN_WIDTH + x] = DIALOG_BG_COLOR;
        }
    }
}

static void cleanup(void)
{
    free(screen_buffer);
    if (texture) SDL_DestroyTexture(texture);
    if (renderer) SDL_DestroyRenderer(renderer);
    if (window) SDL_DestroyWindow(window);
    SDL_Quit();
}

/* ============================================================
 * 文本渲染 - 1:1还原sub_15F84核心循环
 * 一次性从头渲染到结束，遇到TEXT_NEWLINE2时暂停
 * 1:1还原IDA逻辑：遇到控制码时立即绘制对话框和头像，然后继续渲染文字
 * ============================================================ */
static void render_text_full(text_state_t* state, int16_t* text_end)
{
    if (!state->ptr || !text_end) return;
    
    /* 保存初始文本指针 */
    if (state->text_start == NULL) {
        state->text_start = state->ptr;
    }
    
    /* 如果状态是DONE，需要从头重新渲染 */
    if (state->state == TEXT_STATE_DONE) {
        /* 从头重放控制码，不渲染 */
        int16_t* replay = state->text_start;
        int r_n3 = 0;
        int r_n1832 = DIALOG_TYPE_F;
        int r_pixel_x = TEXT_F_START_X;
        int r_pixel_y = TEXT_F_START_Y;
        int r_n2 = 0;
        
        while (replay < text_end) {
            int16_t word = *replay;
            
            if (word == TEXT_END) {
                replay++;
                r_n1832 = DIALOG_TYPE_NONE;
                break;
            }
            
            if (word == TEXT_NEWLINE) {
                replay++;
                if ((r_n1832 == DIALOG_TYPE_F || r_n1832 == DIALOG_TYPE_S) && r_n3 == 3) {
                    r_n3--;
                }
                r_n3++;
                r_pixel_y += CHAR_HEIGHT;
                r_pixel_x = (r_n1832 == DIALOG_TYPE_F) ? TEXT_F_START_X : TEXT_S_START_X;
                continue;
            }
            
            if (word == TEXT_RECURSE1 || word == TEXT_RECURSE2) {
                replay++;
                continue;
            }
            
            if (word == TEXT_SHOW_NUM) {
                replay++;
                replay++;
                continue;
            }
            
            if (word == TEXT_PORTRAIT_F) {
                replay++;
                replay++;
                r_n1832 = DIALOG_TYPE_F;
                r_n2 = 2;
                r_n3 = 0;
                r_pixel_x = TEXT_F_START_X;
                r_pixel_y = TEXT_F_START_Y;
                continue;
            }
            
            if (word == TEXT_PORTRAIT_S) {
                replay++;
                replay++;
                r_n1832 = DIALOG_TYPE_S;
                r_n2 = 112;
                r_n3 = 0;
                r_pixel_x = TEXT_S_START_X;
                r_pixel_y = TEXT_S_START_Y;
                continue;
            }
            
            if (word == TEXT_CHAR_F) {
                replay++;
                replay++;
                r_n1832 = DIALOG_TYPE_F;
                r_n2 = 2;
                r_n3 = 0;
                r_pixel_x = TEXT_F_START_X;
                r_pixel_y = TEXT_F_START_Y;
                continue;
            }
            
            if (word == TEXT_CHAR_S) {
                replay++;
                replay++;
                r_n1832 = DIALOG_TYPE_S;
                r_n2 = 112;
                r_n3 = 0;
                r_pixel_x = TEXT_S_START_X;
                r_pixel_y = TEXT_S_START_Y;
                continue;
            }
            
            if (word >= 0 && word < FONT_MAX_CHARS) {
                r_pixel_x += CHAR_WIDTH;
            }
            
            replay++;
        }
        
        /* 恢复重放后的状态 */
        state->n3 = r_n3;
        state->n1832 = r_n1832;
        state->pixel_x = r_pixel_x;
        state->pixel_y = r_pixel_y;
        state->n2 = r_n2;
        state->ptr = state->text_start;
    }
    
    /* 从当前ptr渲染到结束 */
    while (state->ptr < text_end) {
        int16_t word = *state->ptr;
        
        if (word == TEXT_END) {
            state->ptr++;
            state->state = TEXT_STATE_DONE;
            state->n1832 = DIALOG_TYPE_NONE;
            return;
        }
        
        if (word == TEXT_NEWLINE) {
            state->ptr++;
            if ((state->n1832 == DIALOG_TYPE_F || state->n1832 == DIALOG_TYPE_S) && state->n3 == 3) {
                scroll_screen(state->n1832);
                state->n3--;
            }
            state->n3++;
            state->pixel_y += CHAR_HEIGHT;
            state->pixel_x = (state->n1832 == DIALOG_TYPE_F) ? TEXT_F_START_X : TEXT_S_START_X;
            continue;  /* IDA: goto LABEL_50; 继续循环 */
        }
        
        if (word == TEXT_RECURSE1 || word == TEXT_RECURSE2) {
            state->ptr++;
            continue;
        }
        
        if (word == TEXT_SHOW_NUM) {
            state->ptr++;
            state->ptr++;
            continue;
        }
        
        if (word == TEXT_PORTRAIT_F) {
            state->ptr++;
            int16_t pid = *state->ptr++;
            state->n1832 = DIALOG_TYPE_F;
            state->n2 = 2;
            int dato_idx = get_dato_idx_from_char_id(pid);
            if (dato_idx >= 0 && dato_idx < 135) {
                load_portrait(dato_idx);
                render_portrait(state->n1832);
            }
            state->n3 = 0;
            state->pixel_x = TEXT_F_START_X;
            state->pixel_y = TEXT_F_START_Y;
            continue;  /* IDA: goto LABEL_33 */
        }
        
        if (word == TEXT_PORTRAIT_S) {
            state->ptr++;
            int16_t pid = *state->ptr++;
            state->n1832 = DIALOG_TYPE_S;
            state->n2 = 112;
            int dato_idx = get_dato_idx_from_char_id(pid);
            if (dato_idx >= 0 && dato_idx < 135) {
                load_portrait(dato_idx);
                render_portrait(state->n1832);
            }
            state->n3 = 0;
            state->pixel_x = TEXT_S_START_X;
            state->pixel_y = TEXT_S_START_Y;
            continue;  /* IDA: goto LABEL_42 */
        }
        
        if (word == TEXT_CHAR_F) {
            state->ptr++;
            int16_t cid = *state->ptr++;
            state->n1832 = DIALOG_TYPE_F;
            state->n2 = 2;
            int dato_idx = get_dato_idx_from_char_db_index(cid);
            if (dato_idx >= 0 && dato_idx < 135) {
                load_portrait(dato_idx);
                render_portrait(state->n1832);
            }
            state->n3 = 0;
            state->pixel_x = TEXT_F_START_X;
            state->pixel_y = TEXT_F_START_Y;
            continue;  /* IDA: goto LABEL_33 */
        }
        
        if (word == TEXT_CHAR_S) {
            state->ptr++;
            int16_t cid = *state->ptr++;
            state->n1832 = DIALOG_TYPE_S;
            state->n2 = 112;
            int dato_idx = get_dato_idx_from_char_db_index(cid);
            if (dato_idx >= 0 && dato_idx < 135) {
                load_portrait(dato_idx);
                render_portrait(state->n1832);
            }
            state->n3 = 0;
            state->pixel_x = TEXT_S_START_X;
            state->pixel_y = TEXT_S_START_Y;
            continue;  /* IDA: goto LABEL_42 */
        }
        
        /* 默认：渲染字符 (IDA: sub_4ED7A(..., n658255_1, ...); n658255_1+=16;) */
        if (word >= 0 && word < FONT_MAX_CHARS) {
            render_char(word, state->pixel_x, state->pixel_y, DIALOG_TEXT_FG, DIALOG_TEXT_BG, true);
            state->pixel_x += CHAR_WIDTH;
        }
        
        state->ptr++;
    }
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
    bool text_done = false;
    
    text_state_t text_state;
    memset(&text_state, 0, sizeof(text_state));
    text_state.n1832 = DIALOG_TYPE_F;
    text_state.n658255 = 658255;
    text_state.n658255_1 = 658255;
    text_state.n3 = 0;
    text_state.state = TEXT_STATE_CONTINUE;
    
    printf("控制:\n");
    printf("  上/下: 切换资源集 (0-%d)\n", fdtxt_count - 1);
    printf("  左/右: 切换子文本项\n");
    printf("  空格/回车/Z/X: 继续/切换\n");
    printf("  ESC: 退出\n\n");
    
    bool running = true;
    
    while (running) {
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
                            portrait_loaded = false;
                            need_render = true;
                        }
                        break;
                    case SDLK_DOWN:
                        if (cur_res < fdtxt_count - 1) {
                            cur_res++; cur_sub = 0;
                            text_initialized = false;
                            text_done = false;
                            portrait_loaded = false;
                            need_render = true;
                        }
                        break;
                    case SDLK_LEFT:
                        if (cur_sub > 0) {
                            cur_sub--;
                            text_initialized = false;
                            text_done = false;
                            portrait_loaded = false;
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
                                portrait_loaded = false;
                                need_render = true;
                            }
                        }
                        break;
                    case SDLK_SPACE:
                    case SDLK_RETURN:
                    case SDLK_z:
                    case SDLK_x:
                        if (text_state.state == TEXT_STATE_WAIT_KEY) {
                            text_state.state = TEXT_STATE_CONTINUE;
                            need_render = true;
                        } else if (text_done) {
                            int sc = get_sub_count(cur_res);
                            if (cur_sub < sc - 1) {
                                cur_sub++;
                                text_initialized = false;
                                text_done = false;
                                portrait_loaded = false;
                                need_render = true;
                            }
                        } else {
                            need_render = true;
                        }
                        break;
                }
            }
        }
        
        if (need_render) {
            clear_screen();
            
            if (!text_initialized) {
                printf("\n=== 初始化文本状态 ===\n");
                printf("   对话框类型: F (下方)\n");
                printf("   DIALOG_F_X=%d, DIALOG_F_Y=%d\n", DIALOG_F_X, DIALOG_F_Y);
                printf("   DIALOG_S_X=%d, DIALOG_S_Y=%d\n", DIALOG_S_X, DIALOG_S_Y);
                printf("   PORTRAIT_F_X=%d, PORTRAIT_F_Y=%d\n", PORTRAIT_F_X, PORTRAIT_F_Y);
                text_state.n1832 = DIALOG_TYPE_F;
                text_state.n658255 = 658255;
                text_state.n658255_1 = 658255;
                text_state.n3 = 0;
                text_state.state = TEXT_STATE_CONTINUE;
                text_state.v35 = 0;
                text_state.n2 = 0;
                text_state.text_start = NULL;
                text_state.render_end = NULL;
                text_state.pixel_x = TEXT_F_START_X;
                text_state.pixel_y = TEXT_F_START_Y;
                
                int16_t* txt_end = NULL;
                int16_t* txt = get_sub_text(cur_res, cur_sub, &txt_end);
                if (txt) {
                    text_state.ptr = txt;
                    printf("   文本指针: %p, 结束指针: %p\n", (void*)txt, (void*)txt_end);
                } else {
                    printf("   警告: 未找到文本数据\n");
                    text_state.ptr = NULL;
                }
                text_initialized = true;
                text_done = false;
            }
            
            /* 渲染对话框 */
            if (text_state.n1832 == DIALOG_TYPE_F || text_state.n1832 == DIALOG_TYPE_S) {
                draw_dialog_box(text_state.n1832);
            }
            
            /* 渲染文本和头像 */
            if (text_state.ptr && text_state.state != TEXT_STATE_DONE) {
                int16_t* txt_end = NULL;
                get_sub_text(cur_res, cur_sub, &txt_end);
                
                render_text_full(&text_state, txt_end);
                
                if (text_state.state == TEXT_STATE_DONE) {
                    text_done = true;
                }
            }
            
            /* 渲染头像 - 1:1还原IDA: 头像在控制码处理时已立即渲染，这里不再重复渲染 */
            /* 主循环只在首次初始化时绘制对话框，头像由render_text_full在控制码处理时立即渲染 */
            
            render_frame();
            
            int sc = get_sub_count(cur_res);
            printf("\r资源集: %d/%d  子项: %d/%d  对话框: %s  行: %d", 
                   cur_res, fdtxt_count-1, cur_sub, sc > 0 ? sc-1 : 0,
                   text_state.n1832 == DIALOG_TYPE_F ? "下方(F)" : 
                   (text_state.n1832 == DIALOG_TYPE_S ? "上方(S)" : "无"),
                   text_state.n3);
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
