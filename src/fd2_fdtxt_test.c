/*
 * FDTXT.DAT 文本渲染测试 - 完整游戏对话逻辑版本
 * 
 * 1:1还原游戏对话框绘制和控制逻辑
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

/* 对话框常量 */
#define DIALOG_X          8
#define DIALOG_Y          8
#define DIALOG_W          304
#define DIALOG_H          128
#define DIALOG_BG_COLOR   0xFF0C0C0C
#define DIALOG_BORDER_COLOR 0xFF808080
#define DIALOG_TEXT_FG    0xFFFFFFFF
#define DIALOG_TEXT_BG    0xFF0C0C0C

#define PORTRAIT_X        (DIALOG_X + 8)
#define PORTRAIT_Y        (DIALOG_Y + 8)
#define PORTRAIT_W        64
#define PORTRAIT_H        64
#define TEXT_START_X      (PORTRAIT_X + PORTRAIT_W + 8)
#define TEXT_START_Y      (DIALOG_Y + 12)
#define TEXT_WRAP_X       (DIALOG_X + DIALOG_W - CHAR_WIDTH - 4)
#define TEXT_MAX_LINES    5

/* 文本状态 (1:1还原sub_15F84) */
typedef enum {
    TEXT_CONTINUE = 0,       /* 继续渲染 */
    TEXT_WAIT_KEY_NEWLINE2 = 1, /* TEXT_NEWLINE2后等待按键 (sub_16C57) */
    TEXT_WAIT_KEY_END = 2,   /* TEXT_END后等待按键 */
    TEXT_DONE = 3            /* 当前子项渲染完成 */
} text_state_t;

typedef struct {
    int16_t* ptr;      /* 当前文本指针 */
    int x, y;          /* 当前渲染位置 */
    int line_count;    /* 当前行数 */
    text_state_t state; /* 当前状态 */
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
static void render_portrait(void)
{
    if (!portrait_loaded || !portrait_frames[current_frame]) return;
    
    uint8_t* frame = portrait_frames[current_frame];
    
    for (int y = 0; y < PORTRAIT_H; y++) {
        for (int x = 0; x < PORTRAIT_W; x++) {
            int px = PORTRAIT_X + x;
            int py = PORTRAIT_Y + y;
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
static void draw_dialog_box(void)
{
    /* 背景填充 */
    for (int y = DIALOG_Y; y < DIALOG_Y + DIALOG_H; y++) {
        for (int x = DIALOG_X; x < DIALOG_X + DIALOG_W; x++) {
            screen_buffer[y * SCREEN_WIDTH + x] = DIALOG_BG_COLOR;
        }
    }
    
    /* 外边框 (亮色) */
    for (int x = DIALOG_X; x < DIALOG_X + DIALOG_W; x++) {
        screen_buffer[DIALOG_Y * SCREEN_WIDTH + x] = DIALOG_BORDER_COLOR;
        screen_buffer[(DIALOG_Y + DIALOG_H - 1) * SCREEN_WIDTH + x] = DIALOG_BORDER_COLOR;
    }
    for (int y = DIALOG_Y; y < DIALOG_Y + DIALOG_H; y++) {
        screen_buffer[y * SCREEN_WIDTH + DIALOG_X] = DIALOG_BORDER_COLOR;
        screen_buffer[y * SCREEN_WIDTH + DIALOG_X + DIALOG_W - 1] = DIALOG_BORDER_COLOR;
    }
    
    /* 内边框 (暗色) */
    int ix = DIALOG_X + 1, iy = DIALOG_Y + 1;
    int iw = DIALOG_W - 2, ih = DIALOG_H - 2;
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

/* 文本渲染 (1:1还原sub_15F84核心循环)
 * 
 * 游戏逻辑 (按汇编顺序):
 * - TEXT_END(-1): 文本结束，退出循环 (L70-L80)
 * - TEXT_NEWLINE(-2): 换行，n3++, 计算n658255_1, goto LABEL_50 (L81-L89)
 * - TEXT_NEWLINE2(-3): 换行，n3++, 计算n658255_1, v15++, sub_16C57(1), arg20=1 (L91-L103)
 * - TEXT_RECURSE1(-4): 递归调用sub_15F84 (L107-L110)
 * - TEXT_RECURSE2(-5): 递归调用sub_15F84 (L112-L115)
 * - TEXT_SHOW_NUM(-6): 显示数字 (L119-L131)
 * - TEXT_PORTRAIT_F(-17): 加载头像 (L135-L166)
 * - TEXT_PORTRAIT_S(-18): 加载头像 (L167-L194)
 * - TEXT_CHAR_F(-19): 加载角色 (L195-L211)
 * - TEXT_CHAR_S(-20): 加载角色 (L212-L228)
 * - 默认: sub_4ED7A渲染字符, n658255_1+=16, if(sub_10620())arg20=0, if(arg20)sub_164E8() (L229-L235)
 * 
 * 注意：sub_16C57(1)在函数内部阻塞等待按键，不return到主循环
 * ============================================================ */
static void render_text_item(text_state_t_struct* state, int start_x, int start_y, bool wait_for_key)
{
    if (!state->ptr) return;
    
    (void)start_y;  /* 未使用，保留参数签名 */
    
    /* 1:1还原sub_15F84主循环 - 连续的while循环 */
    while (1) {
        int16_t word = *state->ptr++;
        
        /* L70: if (v18 == -1) - TEXT_END */
        if (word == TEXT_END) {
            /* L72-L78: if (v35) { sub_16559(0); sub_16C57(0); sub_16B43(v35, n2); n1832 = 0; } */
            /* L79: JUMPOUT(0x15309) - 跳出循环 */
            /* 游戏原版：sub_16C57(0)等待按键，然后退出 */
            if (wait_for_key) {
                /* 阻塞等待按键 */
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
            state->state = TEXT_DONE;
            return;  /* 退出文本渲染 */
        }
        
        /* L81: if (v18 == -2) - TEXT_NEWLINE */
        if (word == TEXT_NEWLINE) {
            /* L83-L84: if ((n1832 == 1832 || n1832 == 36887) && n3 == 3) { sub_16E24(); --n3; } */
            /* 简化: 不处理n1832检查 */
            
            /* L88: n658255_1 = ++n3 * arg1C * argC + n658255 */
            /* 在我们的实现中，n3对应line_count */
            state->x = start_x;
            state->y += CHAR_HEIGHT;
            state->line_count++;
            
            /* L89: goto LABEL_50 */
            /* LABEL_50: ++v15; - 继续循环 */
            continue;
        }
        
        /* L91: if (v18 != -3) - TEXT_NEWLINE2 */
        if (word != TEXT_NEWLINE2) {
            /* 跳转到下一个检查 */
            goto CHECK_RECURSE1;
        }
        
        /* TEXT_NEWLINE2处理 */
        /* L93-L94: if ((n1832 == 1832 || n1832 == 36887) && n3 == 3) { sub_16E24(); --n3; } */
        /* L98: n658255_1 = ++n3 * arg1C * argC + n658255 */
        state->x = start_x;
        state->y += CHAR_HEIGHT;
        state->line_count++;
        
        /* L99: ++v15 */
        /* 已经在上面*state->ptr++中完成了 */
        
        /* L100-L101: if (n1832 == 1832 || n1832 == 36887) sub_16559(0); */
        /* L102: sub_16C57(1); */
        /* L103: arg20 = 1; */
        /* 游戏原版：sub_16C57(1)在函数内部阻塞等待按键 */
        if (wait_for_key) {
            /* 阻塞等待按键，不return到主循环 */
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
        /* 按键后继续渲染后面的文字 */
        goto LABEL_50;
        
    CHECK_RECURSE1:
        /* L105-L106: v16 = (int)(v15 + 1); v32 = v15 + 1; */
        /* L107: if (v18 == -4) - TEXT_RECURSE1 */
        if (word == TEXT_RECURSE1) {
            /* L109: sub_15F84(a1, dword_53A7D, dword_53AD9, n658255_1, argC, 205, 76, 74, 19, 1); */
            /* L110: goto LABEL_13; */
            /* 递归调用 - 暂时跳过 */
            goto LABEL_50;
        }
        
        /* L112: if (v18 != -5) - TEXT_RECURSE2 */
        if (word == TEXT_RECURSE2) {
            /* L114: sub_15F84(a1, dword_53A7D, dword_53ADD, n658255_1, argC, 205, 76, 74, 19, 1); */
            /* L115: LABEL_13: n658255_1 = n658255_2; v15 = v32; */
            /* 递归调用 - 暂时跳过 */
            goto LABEL_50;
        }
        
        /* L119: if (v18 != -6) - TEXT_SHOW_NUM */
        if (word != TEXT_SHOW_NUM) {
            /* 跳转到下一个检查 */
            goto CHECK_PORTRAIT_F;
        }
        
        /* TEXT_SHOW_NUM处理 */
        /* L121-L122: sprintf(v31, "%d", dword_53AE1); v37 = strlen(v31); */
        /* L123-L131: for (i = 0; v37 > i; ++i) { sub_4ED7A(...); if(sub_10620()) arg20=0; if(arg20) sub_164E8(); n658255_1+=16; } */
        /* L132: LABEL_50: ++v15; */
        /* 暂时显示占位符 */
        render_char(0, state->x, state->y, DIALOG_TEXT_FG, DIALOG_TEXT_BG, true);
        state->x += CHAR_WIDTH;
        goto LABEL_50;
        
    CHECK_PORTRAIT_F:
        /* L135: if (v18 == -17) - TEXT_PORTRAIT_F */
        if (word == TEXT_PORTRAIT_F) {
            /* L137-L142: if (v35) { sub_16559(0); sub_16C57(0); v18 = sub_16B43(v35, n2); } */
            /* L143: n1832 = 1832; */
            /* L144: n39 = (unsigned __int16)v15[1]; */
            int16_t pid = *state->ptr++;
            
            /* L145-L149: v20 = sub_12C60(...); if (v20 == -1) n2 = 0; else n2 = 2; */
            /* L150-L154: if (n39 != 39) { ... } */
            /* L155: DATO_DAT = sub_111BA(...); */
            /* L156: v21 = sub_165AC(...); */
            if (load_portrait(pid) == 0) {
                state->x = TEXT_START_X;
                state->y = TEXT_START_Y;
                state->line_count = 0;
            }
            
            /* L160: sub_4EBFF(n1832 + 655360, a1, 320); */
            /* L161: arg20 = 1; */
            /* L162: n3 = 0; */
            /* L163-L164: n658255 = 658255; n658255_1 = 658255; */
            /* L165: goto LABEL_42; */
            /* L193: LABEL_42: v15 += 2; - 继续循环 */
            state->state = TEXT_CONTINUE;
            goto LABEL_50;
        }
        
        /* L167: if (v18 != -18) - TEXT_PORTRAIT_S */
        if (word == TEXT_PORTRAIT_S) {
            /* L169-L174: if (v35) { sub_16559(0); sub_16C57(0); v18 = sub_16B43(v35, n2); } */
            /* L175: n1832 = 36887; */
            int16_t pid = *state->ptr++;
            
            /* L176-L180: v22 = sub_12C60(...); if (v22 == -1) n2 = 0; else n2 = 112; */
            /* L182-L183: DATO_DAT = sub_111BA(...); v24 = sub_165AC(...); */
            if (load_portrait(pid) == 0) {
                state->x = TEXT_START_X;
                state->y = TEXT_START_Y;
                state->line_count = 0;
            }
            
            /* L187: sub_4EC31(n1832 + 655360, a1, 320); */
            /* L188: arg20 = 1; */
            /* L189: n3 = 0; */
            /* L190-L191: n658255 = 693535; n658255_1 = 693535; */
            /* L192: LABEL_42: */
            /* L193: v15 += 2; - 继续循环 */
            state->state = TEXT_CONTINUE;
            goto LABEL_50;
        }
        
        /* L195: if (v18 == -19) - TEXT_CHAR_F */
        if (word == TEXT_CHAR_F) {
            /* L197-L201: if (v35) { sub_16559(0); sub_16C57(0); sub_16B43(v35, n2); } */
            /* L203: n1832 = 1832; */
            /* L204: v25 = 80 * (unsigned __int16)v15[1]; */
            int16_t pid = *state->ptr++;
            
            /* L205-L208: v26 = (unsigned __int8 *)(v25 + dword_53A45); v27 = *(unsigned __int8 *)(v25 + dword_53A45 + 7); n2 = 2; */
            /* L209-L210: DATO_DAT = sub_111BA(...); v21 = sub_165AC(...); */
            /* L211: goto LABEL_33; */
            if (load_portrait(pid) == 0) {
                state->x = TEXT_START_X;
                state->y = TEXT_START_Y;
                state->line_count = 0;
            }
            state->state = TEXT_CONTINUE;
            goto LABEL_50;
        }
        
        /* L212: if (v18 == -20) - TEXT_CHAR_S */
        if (word == TEXT_CHAR_S) {
            /* L214-L219: if (v35) { sub_16559(0); sub_16C57(0); sub_16B43(v35, n2); } */
            /* L220: n1832 = 36887; */
            /* L221: v28 = 80 * (unsigned __int16)v15[1]; */
            int16_t pid = *state->ptr++;
            
            /* L222-L227: v29 = (unsigned __int8 *)(v28 + dword_53A45); v30 = *(unsigned __int8 *)(v28 + dword_53A45 + 7); n2 = 112; */
            /* L225-L226: DATO_DAT = sub_111BA(...); v24 = sub_165AC(...); */
            /* L228: goto LABEL_41; */
            if (load_portrait(pid) == 0) {
                state->x = TEXT_START_X;
                state->y = TEXT_START_Y;
                state->line_count = 0;
            }
            state->state = TEXT_CONTINUE;
            goto LABEL_50;
        }
        
        /* L229: sub_4ED7A(dword_53A75, v18, n658255_1, argC, arg10, arg14, arg18); */
        /* L230: n658255_1 += 16; */
        /* L231: v15 = v32; */
        if (word >= 0 && word < FONT_MAX_CHARS) {
            /* 检查换行 */
            if (state->x > TEXT_WRAP_X) {
                state->x = start_x;
                state->y += CHAR_HEIGHT;
                state->line_count++;
            }
            
            render_char(word, state->x, state->y, DIALOG_TEXT_FG, DIALOG_TEXT_BG, true);
            state->x += CHAR_WIDTH;
        }
        
    LABEL_50:
        /* L133: ++v15; */
        /* 已经在上面*state->ptr++中完成了 */
        /* 继续循环处理下一个词 */
    }
}

/* ============================================================
 * 获取文本项
 * ============================================================ */
static int16_t* get_sub_text(int res_idx, int sub_idx)
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
    if (sub_idx < 0 || sub_idx >= sc) return NULL;
    
    int16_t* offs = (int16_t*)(rd + 2);
    return (int16_t*)(rd + offs[sub_idx]);
}

static int get_sub_count(int res_idx)
{
    uint32_t rs = fdtxt_offsets[res_idx];
    if (rs >= fdtxt_file_size) return 0;
    int16_t c;
    memcpy(&c, fdtxt_data + rs, 2);
    return (c > 0) ? c : 0;
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
    
    printf("=== FDTXT 对话框测试 (完整游戏逻辑) ===\n\n");
    
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
    text_state.x = TEXT_START_X;
    text_state.y = TEXT_START_Y;
    text_state.line_count = 0;
    text_state.state = TEXT_CONTINUE;
    
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
            draw_dialog_box();
            render_portrait();
            
            /* 初始化文本状态 */
            if (!text_initialized) {
                text_state.x = TEXT_START_X;
                text_state.y = TEXT_START_Y;
                text_state.line_count = 0;
                text_state.state = TEXT_CONTINUE;
                
                int16_t* txt = get_sub_text(cur_res, cur_sub);
                if (txt) {
                    text_state.ptr = txt;
                }
                text_initialized = true;
            }
            
            /* 渲染文本 - wait_for_key=true让函数内部阻塞等待按键 */
            if (text_state.ptr && text_state.state != TEXT_DONE) {
                render_text_item(&text_state, TEXT_START_X, TEXT_START_Y, true);
            }
            
            render_frame();
            
            int sc = get_sub_count(cur_res);
            printf("\r资源集: %d/%d  子项: %d/%d  ", cur_res, fdtxt_count-1, cur_sub, sc > 0 ? sc-1 : 0);
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
