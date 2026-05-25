/*
 * FDTXT.DAT 文本渲染测试 - 基于IDA MCP汇编分析1:1还原
 * 
 * 核心逻辑 (1:1还原sub_15F84):
 * 1. 逐字符渲染，每渲染一个字符后调用sub_164E8 (头像动画+延迟)
 * 2. TEXT_NEWLINE(-2): 换行，不等待，继续渲染
 * 3. TEXT_NEWLINE2(-3): 换行+等待按键 (sub_16C57)
 * 4. n3==3时滚动 (sub_16E24)
 * 5. 头像动画: 每2个字符切换一帧，帧循环0->1->2->3->1->2->3...
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

#define SCREEN_WIDTH 320
#define SCREEN_HEIGHT 200
#define SCALE_FACTOR 3
#define CHAR_WIDTH 16
#define CHAR_HEIGHT 16

#define FONT_MAX_CHARS 1824

/* 控制码 (1:1还原sub_15F84中的v17比较) */
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

#define FONT_DAT_PATH "game/FDOTHER.DAT"
#define FDTXT_DAT_PATH "game/FDTXT.DAT"
#define DATO_DAT_PATH "game/DATO.DAT"

/* 对话框尺寸 - 1:1还原sub_165AC */
#define DIALOG_W          310
#define DIALOG_H          86

/* 下方对话框 (DIALOG_TYPE_F=1832) */
#define DIALOG_F_Y        114
#define DIALOG_F_X        5
#define PORTRAIT_F_X      13
#define PORTRAIT_F_Y      122
#define TEXT_F_START_X    101
#define TEXT_F_START_Y    122

/* 上方对话框 (DIALOG_TYPE_S=36887) */
#define DIALOG_S_Y        8
#define DIALOG_S_X        5
#define PORTRAIT_S_X      227
#define PORTRAIT_S_Y      16
#define TEXT_S_START_X    13
#define TEXT_S_START_Y    16

#define TILE_W 16
#define TILE_H 16
#define TILE_COUNT 20
#define PORTRAIT_W 80
#define PORTRAIT_H 80

typedef enum {
    DIALOG_TYPE_NONE = 0,
    DIALOG_TYPE_F = 1832,
    DIALOG_TYPE_S = 36887
} dialog_type_t;

typedef enum {
    STATE_CONTINUE = 0,
    STATE_WAIT_KEY,
    STATE_WAIT_END,
    STATE_DONE
} dialog_state_e;

typedef struct {
    int16_t* ptr;
    int n3;           /* 当前行号 (0-3) */
    int n1832;        /* 当前对话框类型 */
    int pixel_x;
    int pixel_y;
    int dado_idx;     /* 当前头像DATO索引 */
    dialog_state_e state;
} dialog_ctx_t;

/* 全局变量 */
static uint8_t* font_data = NULL;
static uint8_t* fdtxt_data = NULL;
static size_t fdtxt_file_size = 0;
static int fdtxt_count = 0;
static uint32_t fdtxt_offsets[146];
static uint8_t* dato_data = NULL;
static size_t dato_file_size = 0;
static uint32_t dato_palette[256];
static uint8_t* dialog_tile_data = NULL;
static bool dialog_tile_loaded = false;

/* 头像动画状态 - 1:1还原sub_164E8 */
static uint8_t* portrait_frames[4];
static int portrait_w = 0, portrait_h = 0;
static int portrait_anim_counter = 0;  /* dword_53A14: 计数到2切换帧 */
static int portrait_frame_cycle = 0;   /* n3_3: 0->1->2->3->1->2->3... */
static int portrait_current_frame = 0;
static bool portrait_loaded = false;

static SDL_Window* window = NULL;
static SDL_Renderer* renderer = NULL;
static SDL_Texture* texture = NULL;
static uint32_t* screen_buffer = NULL;

static void load_palette_6bit(uint8_t* pal, int size)
{
    int count = size / 3;
    for (int i = 0; i < count && i < 256; i++) {
        uint8_t r6 = pal[i * 3] & 0x3F;
        uint8_t g6 = pal[i * 3 + 1] & 0x3F;
        uint8_t b6 = pal[i * 3 + 2] & 0x3F;
        dato_palette[i] = (0xFFu << 24) | ((r6 << 2) | (r6 >> 4)) << 16 | ((g6 << 2) | (g6 >> 4)) << 8 | ((b6 << 2) | (b6 >> 4));
    }
}

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
                for (int k = 0; k < count && j < max_pixels; k++) dst[j++] = val;
            }
        } else {
            dst[j++] = byte;
        }
    }
    return j;
}

static uint8_t* load_file(const char* filename, size_t* out_size)
{
    FILE* fp = fopen(filename, "rb");
    if (!fp) return NULL;
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

static int load_dialog_tiles(void)
{
    size_t osz;
    uint8_t* od = load_file(FONT_DAT_PATH, &osz);
    if (!od) return -1;
    int tsz = 0;
    uint8_t* tile_data = load_dat_resource(od, osz, 5, &tsz);
    free(od);
    if (!tile_data || tsz < 20) { free(tile_data); return -1; }
    int pixel_count = TILE_COUNT * TILE_W * TILE_H;
    uint8_t* decoded = (uint8_t*)malloc(pixel_count);
    if (!decoded) { free(tile_data); return -1; }
    int decoded_count = rle_decompress(tile_data + 20, tsz - 20, decoded, pixel_count);
    free(tile_data);
    if (decoded_count != pixel_count) { free(decoded); return -1; }
    free(dialog_tile_data);
    dialog_tile_data = decoded;
    dialog_tile_loaded = true;
    return 0;
}

static void render_tile(int tile_idx, int sx, int sy)
{
    if (!dialog_tile_loaded || !dialog_tile_data || tile_idx < 0 || tile_idx >= TILE_COUNT) return;
    uint8_t* tp = dialog_tile_data + tile_idx * TILE_W * TILE_H;
    for (int y = 0; y < TILE_H; y++) {
        for (int x = 0; x < TILE_W; x++) {
            int px = sx + x, py = sy + y;
            if (px < 0 || px >= SCREEN_WIDTH || py < 0 || py >= SCREEN_HEIGHT) continue;
            uint8_t pal = tp[y * TILE_W + x];
            if (pal != 0) screen_buffer[py * SCREEN_WIDTH + px] = dato_palette[pal];
        }
    }
}

static void draw_dialog_box(dialog_type_t dtype)
{
    int dx, dy;
    if (dtype == DIALOG_TYPE_F) { dx = DIALOG_F_X; dy = DIALOG_F_Y; }
    else if (dtype == DIALOG_TYPE_S) { dx = DIALOG_S_X; dy = DIALOG_S_Y; }
    else return;

    if (!dialog_tile_loaded) {
        for (int y = dy; y < dy + DIALOG_H; y++)
            for (int x = dx; x < dx + DIALOG_W; x++)
                screen_buffer[y * SCREEN_WIDTH + x] = 0xFF3848A0;
        return;
    }

    int tiles_x = DIALOG_W / TILE_W;  /* 19 */
    int tiles_y = DIALOG_H / TILE_H;  /* 5 */
    int rx = DIALOG_W % TILE_W;       /* 6 */
    int ry = DIALOG_H % TILE_H;       /* 6 */

    /* 四角 */
    render_tile(0, dx, dy);
    render_tile(1, dx + (tiles_x - 1) * TILE_W, dy);
    render_tile(2, dx, dy + (tiles_y - 1) * TILE_H);
    render_tile(3, dx + (tiles_x - 1) * TILE_W, dy + (tiles_y - 1) * TILE_H);

    /* 上下边 */
    for (int tx = 1; tx < tiles_x - 1; tx++) {
        render_tile(4, dx + tx * TILE_W, dy);
        render_tile(6, dx + tx * TILE_W, dy + (tiles_y - 1) * TILE_H);
    }

    /* 左右边 */
    for (int ty = 1; ty < tiles_y - 1; ty++) {
        render_tile(7, dx, dy + ty * TILE_H);
        render_tile(5, dx + (tiles_x - 1) * TILE_W, dy + ty * TILE_H);
    }

    /* 中间填充 */
    for (int ty = 1; ty < tiles_y - 1; ty++)
        for (int tx = 1; tx < tiles_x - 1; tx++)
            render_tile(12, dx + tx * TILE_W, dy + ty * TILE_H);

    /* 右边剩余 */
    if (rx > 0) {
        for (int ty = 0; ty < tiles_y; ty++) {
            int ti = (ty == 0) ? 1 : ((ty == tiles_y - 1) ? 3 : 5);
            uint8_t* tp = dialog_tile_data + ti * TILE_W * TILE_H;
            for (int y = 0; y < TILE_H; y++)
                for (int x = 0; x < rx; x++) {
                    int px = dx + tiles_x * TILE_W + x, py = dy + ty * TILE_H + y;
                    if (px < SCREEN_WIDTH && py < SCREEN_HEIGHT) {
                        uint8_t pal = tp[y * TILE_W + x];
                        if (pal != 0) screen_buffer[py * SCREEN_WIDTH + px] = dato_palette[pal];
                    }
                }
        }
    }

    /* 底部剩余 */
    if (ry > 0) {
        for (int tx = 0; tx < tiles_x; tx++) {
            int ti = (tx == 0) ? 2 : ((tx == tiles_x - 1) ? 3 : 6);
            uint8_t* tp = dialog_tile_data + ti * TILE_W * TILE_H;
            for (int y = 0; y < ry; y++)
                for (int x = 0; x < TILE_W; x++) {
                    int px = dx + tx * TILE_W + x, py = dy + tiles_y * TILE_H + y;
                    if (px < SCREEN_WIDTH && py < SCREEN_HEIGHT) {
                        uint8_t pal = tp[y * TILE_W + x];
                        if (pal != 0) screen_buffer[py * SCREEN_WIDTH + px] = dato_palette[pal];
                    }
                }
        }
    }

    /* 右下剩余 */
    if (rx > 0 && ry > 0) {
        uint8_t* tp = dialog_tile_data + 3 * TILE_W * TILE_H;
        for (int y = 0; y < ry; y++)
            for (int x = 0; x < rx; x++) {
                int px = dx + tiles_x * TILE_W + x, py = dy + tiles_y * TILE_H + y;
                if (px < SCREEN_WIDTH && py < SCREEN_HEIGHT) {
                    uint8_t pal = tp[y * TILE_W + x];
                    if (pal != 0) screen_buffer[py * SCREEN_WIDTH + px] = dato_palette[pal];
                }
            }
    }
}

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
    uint8_t* rd = dato_data + off_start;
    if (res_size < 20) return -1;
    int16_t w, h;
    memcpy(&w, rd + 16, 2);
    memcpy(&h, rd + 18, 2);
    if (w <= 0 || h <= 0 || w > 512 || h > 512) return -1;
    int pc = w * h;
    for (int i = 0; i < 4; i++) { free(portrait_frames[i]); portrait_frames[i] = NULL; }
    uint32_t foffs[3];
    memcpy(&foffs[0], rd + 4, 4);
    memcpy(&foffs[1], rd + 8, 4);
    memcpy(&foffs[2], rd + 12, 4);
    for (int i = 0; i < 3; i++) if (foffs[i] >= res_size || foffs[i] < 20) return -1;
    struct { int s, e; } reg[4];
    reg[0].s = 20; reg[0].e = foffs[0];
    reg[1].s = foffs[0] + 4; reg[1].e = foffs[1];
    reg[2].s = foffs[1] + 4; reg[2].e = foffs[2];
    reg[3].s = foffs[2] + 4; reg[3].e = res_size;
    for (int i = 0; i < 4; i++) {
        int cs = reg[i].e - reg[i].s;
        if (cs <= 0) return -1;
        portrait_frames[i] = (uint8_t*)malloc(pc);
        if (!portrait_frames[i]) return -1;
        if (rle_decompress(rd + reg[i].s, cs, portrait_frames[i], pc) != pc) {
            for (int j = 0; j <= i; j++) { free(portrait_frames[j]); portrait_frames[j] = NULL; }
            return -1;
        }
    }
    portrait_w = w; portrait_h = h;
    portrait_current_frame = 0;
    portrait_anim_counter = 0;
    portrait_frame_cycle = 0;
    portrait_loaded = true;
    return 0;
}

static void render_portrait(dialog_type_t dtype)
{
    if (!portrait_loaded || !portrait_frames[portrait_current_frame]) return;
    uint8_t* frame = portrait_frames[portrait_current_frame];
    int px_s, py_s;
    if (dtype == DIALOG_TYPE_F) { px_s = PORTRAIT_F_X; py_s = PORTRAIT_F_Y; }
    else if (dtype == DIALOG_TYPE_S) { px_s = PORTRAIT_S_X; py_s = PORTRAIT_S_Y; }
    else return;

    float sx = (float)PORTRAIT_W / portrait_w;
    float sy = (float)PORTRAIT_H / portrait_h;
    float sc = (sx < sy) ? sx : sy;
    int dw = (int)(portrait_w * sc), dh = (int)(portrait_h * sc);
    int ox = (PORTRAIT_W - dw) / 2, oy = (PORTRAIT_H - dh) / 2;

    for (int y = 0; y < dh; y++) {
        for (int x = 0; x < dw; x++) {
            int px = px_s + ox + x, py = py_s + oy + y;
            if (px < 0 || px >= SCREEN_WIDTH || py < 0 || py >= SCREEN_HEIGHT) continue;
            int src_x = (int)(x / sc), src_y = (int)(y / sc);
            if (src_x < portrait_w && src_y < portrait_h) {
                uint8_t idx = frame[src_y * portrait_w + src_x];
                if (idx != 0) screen_buffer[py * SCREEN_WIDTH + px] = dato_palette[idx];
            }
        }
    }
}

static void clear_dialog_area(dialog_type_t dtype)
{
    int dx, dy;
    if (dtype == DIALOG_TYPE_F) { dx = DIALOG_F_X; dy = DIALOG_F_Y; }
    else if (dtype == DIALOG_TYPE_S) { dx = DIALOG_S_X; dy = DIALOG_S_Y; }
    else return;
    for (int y = dy; y < dy + DIALOG_H; y++)
        for (int x = dx; x < dx + DIALOG_W; x++)
            screen_buffer[y * SCREEN_WIDTH + x] = 0x00000000;
}

/* 1:1还原sub_164E8 - 头像动画帧切换 */
static void portrait_tick(void)
{
    if (!portrait_loaded) return;
    portrait_anim_counter++;
    if (portrait_anim_counter == 2) {
        portrait_anim_counter = 0;
        portrait_frame_cycle++;
        if (portrait_frame_cycle == 4) portrait_frame_cycle = 0;
        int df = portrait_frame_cycle;
        if (portrait_frame_cycle == 3) df = 1;
        if (df != portrait_current_frame && portrait_frames[df]) {
            portrait_current_frame = df;
        }
    }
}

static void render_char(int16_t word, int x, int y)
{
    if (!font_data || word < 0 || word >= FONT_MAX_CHARS) return;
    uint8_t* cd = font_data + word * 32;
    for (int row = 0; row < 16; row++) {
        uint16_t bits;
        memcpy(&bits, cd + row * 2, 2);
        bits = ((bits & 0xFF) << 8) | ((bits >> 8) & 0xFF);
        for (int col = 0; col < 16; col++) {
            int px = x + col, py = y + row;
            if (px < 0 || px >= SCREEN_WIDTH || py < 0 || py >= SCREEN_HEIGHT) continue;
            if (bits & (1 << (15 - col)))
                screen_buffer[py * SCREEN_WIDTH + px] = 0xFFFFFFFF;
        }
    }
}

/* 1:1还原sub_16E24 - 文字滚动 */
static void scroll_text(dialog_type_t dtype)
{
    int dx, dy;
    if (dtype == DIALOG_TYPE_F) { dx = DIALOG_F_X + 2; dy = DIALOG_F_Y + 2; }
    else if (dtype == DIALOG_TYPE_S) { dx = DIALOG_S_X + 2; dy = DIALOG_S_Y + 2; }
    else return;

    int tw = 208, th = DIALOG_H - 4;
    /* 上移一行 (16px) */
    for (int y = dy; y < dy + th - 16; y++)
        memcpy(&screen_buffer[y * SCREEN_WIDTH + dx], &screen_buffer[(y + 16) * SCREEN_WIDTH + dx], tw * 4);
    /* 清空最后一行 */
    for (int y = dy + th - 16; y < dy + th; y++)
        for (int x = dx; x < dx + tw; x++)
            screen_buffer[y * SCREEN_WIDTH + x] = 0xFF3848A0;
}

static int16_t* get_sub_text(int res, int sub, int16_t** end)
{
    uint32_t rs = fdtxt_offsets[res];
    uint32_t re = (res + 1 < fdtxt_count) ? fdtxt_offsets[res + 1] : fdtxt_file_size;
    if (rs >= fdtxt_file_size) return NULL;
    uint8_t* rd = fdtxt_data + rs;
    int16_t sc; memcpy(&sc, rd, 2);
    if (sub < 0 || sub >= sc) return NULL;
    int16_t* offs = (int16_t*)(rd + 2);
    int32_t bo = offs[sub];
    if (bo < 0 || bo >= (int32_t)(re - rs)) return NULL;
    int16_t* ts = (int16_t*)(rd + bo);
    if (end) {
        int16_t* p = ts;
        int16_t* mp = (int16_t*)(rd + (re - rs));
        while (p < mp) { if (*p == -1) { *end = p; goto done; } p++; }
        if (sub + 1 < sc && offs[sub + 1] >= 0 && offs[sub + 1] < (int32_t)(re - rs))
            *end = (int16_t*)(rd + offs[sub + 1]);
        else *end = mp;
    done:;
    }
    return ts;
}

static int sdl_init(void)
{
    if (SDL_Init(SDL_INIT_VIDEO) < 0) return -1;
    window = SDL_CreateWindow("FDTXT", SDL_WINDOWPOS_CENTERED, SDL_WINDOWPOS_CENTERED,
                              SCREEN_WIDTH * SCALE_FACTOR, SCREEN_HEIGHT * SCALE_FACTOR, SDL_WINDOW_SHOWN);
    if (!window) return -1;
    renderer = SDL_CreateRenderer(window, -1, SDL_RENDERER_ACCELERATED);
    if (!renderer) return -1;
    texture = SDL_CreateTexture(renderer, SDL_PIXELFORMAT_ARGB8888, SDL_TEXTUREACCESS_STREAMING, SCREEN_WIDTH, SCREEN_HEIGHT);
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

/* 获取字符数据库中的DATO索引 (1:1还原IDA中80*dword_53A45的查找) */
static int get_dato_from_char_db(int char_db_idx)
{
    if (!dato_data) return -1;
    int db_sz = 0;
    uint8_t* db = load_dat_resource(dato_data, dato_file_size, 0, &db_sz);
    if (!db) return -1;
    int cnt = db_sz / 80;
    int dado = -1;
    if (char_db_idx >= 0 && char_db_idx < cnt) dado = db[char_db_idx * 80 + 7];
    free(db);
    return dado;
}

/* 获取字符ID对应的DATO索引 */
static int get_dato_from_char_id(int char_id)
{
    if (!dato_data) return -1;
    int db_sz = 0;
    uint8_t* db = load_dat_resource(dato_data, dato_file_size, 0, &db_sz);
    if (!db) return -1;
    int cnt = db_sz / 80;
    int dado = -1;
    for (int i = 0; i < cnt; i++) {
        if (db[i * 80 + 8] == (uint8_t)char_id) { dado = db[i * 80 + 7]; break; }
    }
    free(db);
    return dado;
}

int main(int argc, char* argv[])
{
    (void)argc; (void)argv;
    printf("=== FDTXT 对话框测试 (IDA MCP 1:1还原) ===\n\n");

    /* 加载资源 */
    printf("1. 加载字体...\n");
    size_t osz;
    uint8_t* od = load_file(FONT_DAT_PATH, &osz);
    if (!od) return 1;
    int fsz = 0;
    font_data = load_dat_resource(od, osz, 3, &fsz);
    int psz;
    uint8_t* pd = load_dat_resource(od, osz, 98, &psz);
    if (pd && psz == 768) load_palette_6bit(pd, psz);
    free(pd); free(od);
    if (!font_data) return 1;

    printf("2. 加载DATO.DAT...\n");
    dato_data = load_file(DATO_DAT_PATH, &dato_file_size);
    if (!dato_data) { free(font_data); return 1; }
    uint32_t dc; memcpy(&dc, dato_data + 6, 4);
    printf("   头像数量: %d\n", dc);

    printf("3. 加载FDTXT.DAT...\n");
    fdtxt_data = load_file(FDTXT_DAT_PATH, &fdtxt_file_size);
    if (!fdtxt_data) { free(font_data); return 1; }
    memcpy(&fdtxt_count, fdtxt_data + 6, 4);
    for (int i = 0; i < fdtxt_count && i < 146; i++)
        memcpy(&fdtxt_offsets[i], fdtxt_data + 10 + i * 4, 4);

    printf("4. 加载对话框tile...\n");
    if (load_dialog_tiles() < 0) printf("   警告: tile加载失败\n");

    if (sdl_init() < 0) return 1;

    /* 只加载第一关第一个对话片段 */
    int cur_res = 1, cur_sub = 0;
    dialog_ctx_t ctx;
    memset(&ctx, 0, sizeof(ctx));
    ctx.n1832 = DIALOG_TYPE_NONE;
    ctx.state = STATE_CONTINUE;

    printf("\n控制: 空格/回车=继续, ESC=退出\n");
    printf("资源集=%d, 子项=%d\n\n", cur_res, cur_sub);

    bool running = true, need_init = true;

    while (running) {
        SDL_Event ev;
        while (SDL_PollEvent(&ev)) {
            if (ev.type == SDL_QUIT) { running = false; break; }
            if (ev.type == SDL_KEYDOWN) {
                if (ev.key.keysym.sym == SDLK_ESCAPE) running = false;
                else if (ev.key.keysym.sym == SDLK_SPACE || ev.key.keysym.sym == SDLK_RETURN) {
                    if (ctx.state == STATE_WAIT_KEY) {
                        ctx.state = STATE_CONTINUE;
                    } else if (ctx.state == STATE_WAIT_END) {
                        /* 1:1还原IDA: sub_16C57(0)返回后清除对话框 */
                        clear_dialog_area(ctx.n1832);
                        ctx.n1832 = DIALOG_TYPE_NONE;
                        ctx.state = STATE_DONE;
                        int sc = 0;
                        if (fdtxt_offsets[cur_res] < fdtxt_file_size) {
                            memcpy(&sc, fdtxt_data + fdtxt_offsets[cur_res], 2);
                        }
                        if (cur_sub < sc - 1) {
                            cur_sub++;
                            memset(screen_buffer, 0, SCREEN_WIDTH * SCREEN_HEIGHT * 4);
                            need_init = true;
                            printf(">>> 切换到子项 %d\n", cur_sub);
                        }
                    } else if (ctx.state == STATE_DONE) {
                        int sc = 0;
                        if (fdtxt_offsets[cur_res] < fdtxt_file_size) {
                            memcpy(&sc, fdtxt_data + fdtxt_offsets[cur_res], 2);
                        }
                        if (cur_sub < sc - 1) {
                            cur_sub++;
                            memset(screen_buffer, 0, SCREEN_WIDTH * SCREEN_HEIGHT * 4);
                            need_init = true;
                            printf(">>> 切换到子项 %d\n", cur_sub);
                        }
                    }
                }
            }
        }

        /* 初始化 */
        if (need_init) {
            need_init = false;
            memset(screen_buffer, 0, SCREEN_WIDTH * SCREEN_HEIGHT * 4);
            memset(&ctx, 0, sizeof(ctx));
            ctx.n1832 = DIALOG_TYPE_NONE;
            ctx.state = STATE_CONTINUE;
            portrait_loaded = false;
            portrait_anim_counter = 0;
            portrait_frame_cycle = 0;
            portrait_current_frame = 0;
            int16_t* te = NULL;
            ctx.ptr = get_sub_text(cur_res, cur_sub, &te);
        }

        /* 1:1还原sub_15F84主循环 - 逐字符处理 */
        if (ctx.ptr && ctx.state == STATE_CONTINUE) {
            int16_t* txt_end = NULL;
            get_sub_text(cur_res, cur_sub, &txt_end);
            if (!txt_end) txt_end = ctx.ptr + 1;

            int16_t word = *ctx.ptr;

            if (word == TEXT_END) {
                ctx.ptr++;
                /* 1:1还原IDA: TEXT_END时调用sub_16C57(0)等待按键 */
                if (ctx.n1832 == DIALOG_TYPE_F || ctx.n1832 == DIALOG_TYPE_S) {
                    ctx.state = STATE_WAIT_END;
                } else {
                    ctx.state = STATE_DONE;
                    ctx.n1832 = DIALOG_TYPE_NONE;
                }
                printf("\n>>> 对话完成，等待输入...\n");
            }
            else if (word == TEXT_NEWLINE) {
                ctx.ptr++;
                if ((ctx.n1832 == DIALOG_TYPE_F || ctx.n1832 == DIALOG_TYPE_S) && ctx.n3 == 3) {
                    scroll_text(ctx.n1832);
                    ctx.n3--;
                }
                ctx.n3++;
                ctx.pixel_y += CHAR_HEIGHT;
                ctx.pixel_x = (ctx.n1832 == DIALOG_TYPE_F) ? TEXT_F_START_X : TEXT_S_START_X;
            }
            else if (word == TEXT_NEWLINE2) {
                ctx.ptr++;
                if ((ctx.n1832 == DIALOG_TYPE_F || ctx.n1832 == DIALOG_TYPE_S) && ctx.n3 == 3) {
                    scroll_text(ctx.n1832);
                    ctx.n3--;
                }
                ctx.n3++;
                ctx.pixel_y += CHAR_HEIGHT;
                ctx.pixel_x = (ctx.n1832 == DIALOG_TYPE_F) ? TEXT_F_START_X : TEXT_S_START_X;
                ctx.state = STATE_WAIT_KEY;
            }
            else if (word == TEXT_RECURSE1 || word == TEXT_RECURSE2) {
                ctx.ptr++;
            }
            else if (word == TEXT_SHOW_NUM) {
                ctx.ptr += 2;
            }
            else if (word == TEXT_PORTRAIT_F) {
                ctx.ptr++;
                int16_t pid = *ctx.ptr++;
                if (ctx.n1832 == DIALOG_TYPE_F || ctx.n1832 == DIALOG_TYPE_S) clear_dialog_area(ctx.n1832);
                ctx.n1832 = DIALOG_TYPE_F;
                int di = get_dato_from_char_id(pid);
                ctx.dado_idx = (di >= 0) ? di : 0;
                if (di >= 0) {
                    load_portrait(di);
                    draw_dialog_box(ctx.n1832);
                    render_portrait(ctx.n1832);
                    portrait_anim_counter = 0;
                    portrait_frame_cycle = 0;
                    portrait_current_frame = 0;
                }
                ctx.n3 = 0;
                ctx.pixel_x = TEXT_F_START_X;
                ctx.pixel_y = TEXT_F_START_Y;
            }
            else if (word == TEXT_PORTRAIT_S) {
                ctx.ptr++;
                int16_t pid = *ctx.ptr++;
                if (ctx.n1832 == DIALOG_TYPE_F || ctx.n1832 == DIALOG_TYPE_S) clear_dialog_area(ctx.n1832);
                ctx.n1832 = DIALOG_TYPE_S;
                int di = get_dato_from_char_id(pid);
                ctx.dado_idx = (di >= 0) ? di : 0;
                if (di >= 0) {
                    load_portrait(di);
                    draw_dialog_box(ctx.n1832);
                    render_portrait(ctx.n1832);
                    portrait_anim_counter = 0;
                    portrait_frame_cycle = 0;
                    portrait_current_frame = 0;
                }
                ctx.n3 = 0;
                ctx.pixel_x = TEXT_S_START_X;
                ctx.pixel_y = TEXT_S_START_Y;
            }
            else if (word == TEXT_CHAR_F) {
                ctx.ptr++;
                int16_t cid = *ctx.ptr++;
                if (ctx.n1832 == DIALOG_TYPE_F || ctx.n1832 == DIALOG_TYPE_S) clear_dialog_area(ctx.n1832);
                ctx.n1832 = DIALOG_TYPE_F;
                int di = get_dato_from_char_db(cid);
                ctx.dado_idx = (di >= 0) ? di : 0;
                if (di >= 0) {
                    load_portrait(di);
                    draw_dialog_box(ctx.n1832);
                    render_portrait(ctx.n1832);
                    portrait_anim_counter = 0;
                    portrait_frame_cycle = 0;
                    portrait_current_frame = 0;
                }
                ctx.n3 = 0;
                ctx.pixel_x = TEXT_F_START_X;
                ctx.pixel_y = TEXT_F_START_Y;
            }
            else if (word == TEXT_CHAR_S) {
                ctx.ptr++;
                int16_t cid = *ctx.ptr++;
                if (ctx.n1832 == DIALOG_TYPE_F || ctx.n1832 == DIALOG_TYPE_S) clear_dialog_area(ctx.n1832);
                ctx.n1832 = DIALOG_TYPE_S;
                int di = get_dato_from_char_db(cid);
                ctx.dado_idx = (di >= 0) ? di : 0;
                if (di >= 0) {
                    load_portrait(di);
                    draw_dialog_box(ctx.n1832);
                    render_portrait(ctx.n1832);
                    portrait_anim_counter = 0;
                    portrait_frame_cycle = 0;
                    portrait_current_frame = 0;
                }
                ctx.n3 = 0;
                ctx.pixel_x = TEXT_S_START_X;
                ctx.pixel_y = TEXT_S_START_Y;
            }
            else {
                /* 渲染字符 */
                render_char(word, ctx.pixel_x, ctx.pixel_y);
                ctx.pixel_x += CHAR_WIDTH;
                /* 1:1还原sub_164E8 - 头像动画+延迟 */
                portrait_tick();
                /* 模拟sub_25A96延迟 - 打字机效果 */
                SDL_Delay(50);
                ctx.ptr++;
            }
        }

        render_frame();
        SDL_Delay(16);
    }

    SDL_DestroyTexture(texture);
    SDL_DestroyRenderer(renderer);
    SDL_DestroyWindow(window);
    SDL_Quit();
    for (int i = 0; i < 4; i++) free(portrait_frames[i]);
    free(dato_data); free(font_data); free(fdtxt_data); free(dialog_tile_data);
    printf("\n完成\n");
    return 0;
}
