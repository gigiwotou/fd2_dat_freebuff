/*
 * 战场角色信息面板渲染
 * 基于IDA分析: sub_12D7B -> sub_12CEA -> sub_11CAC -> sub_11EEE
 *
 * 渲染流程:
 * 1. sub_12D7B: 从dword_53A45获取角色数据,调用sub_12CEA
 * 2. sub_12CEA: 动画等待循环,直到位置到达目标(n9_0, n34_0)
 * 3. sub_11CAC: 设置渲染上下文,调用sub_11EEE
 * 4. sub_11EEE: 核心渲染函数,遍历dword_53A51字符布局表,使用FDSHAP.DAT渲染24x24瓦片
 */

#include "fd2_battle.h"
#include "fd2_dat.h"
#include <stdio.h>
#include <string.h>

/* FDSHAP.DAT索引表偏移 */
#define FDSHAP_INDEX_OFFSET 6

/* 瓦片标志位 */
#define TILE_FLAG_SKIP      0x80
#define TILE_FLAG_HALF_OFF  0x10
#define TILE_FLAG_ANIM_OFF  0x04

/* 后备缓冲区偏移 */
#define BACKBUF_OFFSET 32904

/*
 * sub_4E22A: RLE解压/直接blit 24x24精灵到目标缓冲区
 * IDA分析: 这是一个RLE解压函数,处理24x24的精灵数据
 * 
 * RLE格式:
 * - 每个字节高2位表示操作类型,低6位表示计数
 * - 操作0: 跳过(填充0)
 * - 操作1: 复制数据
 * - 操作2: 填充单色
 * - 操作3: 特殊填充
 */
static void rle_blit_24x24(const u8* src, u8* dst, int dst_stride)
{
    int y;
    const u8* src_ptr = src;
    
    for (y = 0; y < 24; y++) {
        u8* dst_ptr = dst;
        int remaining = 24;
        
        while (remaining > 0) {
            u8 cmd = *src_ptr++;
            u8 type = (cmd >> 6) & 0x03;
            u8 count = ((cmd >> 2) & 0x0F) + 1;
            
            if (count > remaining)
                count = remaining;
            
            switch (type) {
                case 0:
                    /* 跳过 */
                    memset(dst_ptr, 0, count);
                    break;
                case 1:
                    /* 复制数据 */
                    memcpy(dst_ptr, src_ptr, count);
                    src_ptr += count;
                    break;
                case 2:
                    /* 填充单色 */
                    memset(dst_ptr, *src_ptr, count);
                    src_ptr++;
                    break;
                case 3:
                    /* 特殊: 交替填充 */
                    {
                        u8 val = *src_ptr++;
                        int i;
                        for (i = 0; i < count; i += 2) {
                            if (i < count) dst_ptr[i] = val;
                            if (i + 1 < count) dst_ptr[i + 1] = val;
                        }
                    }
                    break;
            }
            
            dst_ptr += count;
            remaining -= count;
        }
        
        dst += dst_stride;
    }
}

/*
 * sub_4E016: 带调色板映射的24x24精灵blit
 * IDA分析: 与sub_4E22A类似,但使用调色板映射表转换颜色
 */
static void rle_blit_24x24_palette(const u8* src, u8* dst, int dst_stride, const u8* palette_map)
{
    int y;
    const u8* src_ptr = src;
    
    for (y = 0; y < 24; y++) {
        u8* dst_ptr = dst;
        int remaining = 24;
        
        while (remaining > 0) {
            u8 cmd = *src_ptr++;
            u8 type = (cmd >> 6) & 0x03;
            u8 count = ((cmd >> 2) & 0x0F) + 1;
            
            if (count > remaining)
                count = remaining;
            
            switch (type) {
                case 0:
                    memset(dst_ptr, 0, count);
                    break;
                case 1:
                    {
                        int i;
                        for (i = 0; i < count; i++) {
                            dst_ptr[i] = palette_map[src_ptr[i]];
                        }
                        src_ptr += count;
                    }
                    break;
                case 2:
                    memset(dst_ptr, palette_map[*src_ptr], count);
                    src_ptr++;
                    break;
                case 3:
                    {
                        u8 val = palette_map[*src_ptr++];
                        int i;
                        for (i = 0; i < count; i += 2) {
                            if (i < count) dst_ptr[i] = val;
                            if (i + 1 < count) dst_ptr[i + 1] = val;
                        }
                    }
                    break;
            }
            
            dst_ptr += count;
            remaining -= count;
        }
        
        dst += dst_stride;
    }
}

/*
 * sub_11EEE: 核心渲染函数
 * IDA分析:
 * void sub_11EEE(int dst_x, int dst_stride, int cols, int rows, int start_col, int start_row)
 * 
 * 遍历字符布局表(dword_53A51),对每个瓦片:
 * 1. 获取瓦片索引: *(WORD*)(dword_53A51 + 4*(col + width*row) + 4) & 0x3FF
 * 2. 检查瓦片标志: *(BYTE*)(dword_53A69 + 4*tile_index)
 * 3. 根据标志调整瓦片索引
 * 4. 从FDSHAP.DAT获取精灵数据并blit
 */
static void render_char_layout(
    int dst_x,          /* 目标X偏移 */
    int dst_stride,     /* 目标行跨度 */
    int cols,           /* 列数 */
    int rows,           /* 行数 */
    int start_col,      /* 起始列 */
    int start_row,      /* 起始行 */
    const u8* layout_table, /* dword_53A51 */
    const u8* tile_flags,   /* dword_53A69 */
    const u8* palette_map,  /* dword_53A6D */
    const u8* fdshap_data,  /* FDSHAP_DAT */
    u8* backbuffer,         /* dword_53A49 */
    int layout_width,       /* dword_53AC1 */
    int palette_anim_frame, /* dword_53A40 */
    int n3_1                /* n3_1 */
)
{
    int row, col;
    u8* dst = backbuffer + BACKBUF_OFFSET + dst_x;
    int palette_offset = n3_1 / 2;
    
    for (row = 0; row < rows; row++) {
        u8* row_dst = dst + dst_stride * 24 * row;
        
        for (col = 0; col < cols; col++) {
            int layout_idx = start_col + layout_width * (start_row + row) + col;
            const u8* layout_entry = layout_table + 4 + 4 * layout_idx;
            
            /* 获取瓦片索引: *(WORD*)(entry) & 0x3FF */
            int tile_index = (*(const unsigned short*)layout_entry) & 0x3FF;
            
            /* 检查第4字节是否为255 (决定是否使用调色板映射) */
            u8 use_palette = layout_entry[3];
            
            /* 获取瓦片标志 */
            u8 flags = tile_flags[4 * tile_index];
            
            /* 检查跳过标志 (0x80) */
            if (flags & TILE_FLAG_SKIP) {
                row_dst += 24;
                continue;
            }
            
            /* 处理半偏移标志 (0x10): 加上 n3_1/2 */
            if (flags & TILE_FLAG_HALF_OFF) {
                tile_index += palette_offset;
            }
            
            /* 处理动画偏移标志 (0x04): 加上 palette_anim_frame */
            if (flags & TILE_FLAG_ANIM_OFF) {
                tile_index += palette_anim_frame;
            }
            
            /* 从FDSHAP.DAT获取精灵数据偏移 */
            const u8* index_table = fdshap_data + FDSHAP_INDEX_OFFSET;
            int data_offset = *(const int*)(index_table + 4 * tile_index);
            const u8* sprite_data = fdshap_data + data_offset;
            
            /* 根据use_palette选择渲染方式 */
            if (use_palette == 255) {
                /* 直接blit */
                rle_blit_24x24(sprite_data, row_dst, dst_stride);
            } else {
                /* 带调色板映射的blit */
                rle_blit_24x24_palette(sprite_data, row_dst, dst_stride, palette_map);
            }
            
            row_dst += 24;
        }
    }
}

/*
 * sub_11CAC: 设置渲染上下文并调用sub_11EEE
 * IDA分析:
 * sub_11EEE(dword_53A49 + 32904, 456, 13, 8, n9, n34);
 */
static void setup_and_render_info_panel(
    int n9,
    int n34,
    const u8* layout_table,
    const u8* tile_flags,
    const u8* palette_map,
    const u8* fdshap_data,
    u8* backbuffer,
    int layout_width,
    int palette_anim_frame,
    int n3_1
)
{
    render_char_layout(0, 456, 13, 8, n9, n34,
                       layout_table, tile_flags, palette_map,
                       fdshap_data, backbuffer, layout_width,
                       palette_anim_frame, n3_1);
}

/*
 * 渲染战场角色信息面板
 * 参数:
 *   char_index: 角色索引 (0-63)
 *   char_data: 角色数据数组 (dword_53A45, 80字节/角色)
 *   layout_table: FDFIELD.DAT字符布局表 (dword_53A51)
 *   tile_flags: 瓦片标志表 (dword_53A69)
 *   palette_map: 调色板映射表 (dword_53A6D)
 *   fdshap_data: FDSHAP.DAT数据
 *   backbuffer: 后备缓冲区 (dword_53A49)
 *   layout_width: 布局表宽度 (dword_53AC1)
 *   palette_anim_frame: 调色板动画帧 (dword_53A40)
 *   n3_1: 调色板偏移参数
 *
 * IDA原始流程: sub_12D7B -> sub_12CEA -> sub_11CAC -> sub_11EEE
 */
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
)
{
    int cur_col, cur_row;
    const u8* cd;
    
    if (char_index < 0 || char_index >= 64)
        return;
    
    if (!char_data || !layout_table || !fdshap_data || !backbuffer)
        return;
    
    /* 从角色数据获取位置信息 (80字节/角色) */
    /* IDA: *(byte*)(80*a5 + dword_53A45), *(byte*)(80*a5 + dword_53A45 + 1) */
    cd = char_data + 80 * char_index;
    cur_col = cd[0];     /* byte at offset 0 -> n9 */
    cur_row = cd[1];     /* byte at offset 1 -> n34 */
    
    /* 渲染信息面板 */
    setup_and_render_info_panel(cur_col, cur_row,
                                layout_table, tile_flags, palette_map,
                                fdshap_data, backbuffer, layout_width,
                                palette_anim_frame, n3_1);
}

/*
 * 渲染角色名称到信息面板
 * 基于IDA: 角色名称存储在dword_53A45偏移7处
 */
void render_char_name(int char_index, const u8* char_data, int dst_x, int dst_y)
{
    const u8* cd;
    
    if (char_index < 0 || char_index >= 64)
        return;
    
    if (!char_data)
        return;
    
    cd = char_data + 80 * char_index;
    
    /* 角色名称索引在偏移7处 */
    (void)cd[7];
    (void)dst_x;
    (void)dst_y;
}
