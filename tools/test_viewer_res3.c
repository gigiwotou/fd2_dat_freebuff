/* test_viewer_res3.c - 模拟 viewer 对资源3 (LMI1) 的实际渲染 */
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include "../include/fd2_types.h"
#include "../include/fd2_rle.h"
#include "../include/fd2_fdother_resources.h"
#include "../include/fd2_dat.h"

int main(int argc, char** argv) {
    if (fdother_load("d:/workspace/fd2_dat_freebuff/game/FDOTHER.DAT") != 0) {
        printf("Cannot load\n");
        return 1;
    }

    dword size;
    const byte* data = fdother_get_resource(3, &size);
    if (!data) return 1;
    printf("Resource 3 type: %d (2=LMI1)\n", fdother_get_resource_type(data, size));

    /* 模拟 viewer 的 LMI1 处理流程 */
    fdother_lmi1_t lmi1;
    if (fdother_get_lmi1(3, &lmi1) != 0) {
        printf("Parse LMI1 failed\n");
        return 1;
    }
    printf("LMI1: tile_count=%u, tile_w=%u, tile_h=%u, size=%u\n",
           lmi1.tile_count, lmi1.tile_width, lmi1.tile_height, lmi1.size);

    /* 验证一下偏移表 */
    /* 偏移表地址: 6+0*4..6+22*4, 第23个偏移在 6+23*4=98 */
    printf("First few offsets:\n");
    for (int i = 0; i < 5; i++) {
        dword addr = 6 + i * 4;
        dword off = data[addr] | (data[addr+1]<<8) | (data[addr+2]<<16) | (data[addr+3]<<24);
        printf("  offset[%d] = 0x%x\n", i, off);
    }

    /* 第0个tile的大小 (offset[1] - offset[0]) */
    dword off0 = data[6] | (data[7]<<8) | (data[8]<<16) | (data[9]<<24);
    dword off1 = data[10] | (data[11]<<8) | (data[12]<<16) | (data[13]<<24);
    printf("\nTile 0 offset = 0x%x, Tile 1 offset = 0x%x\n", off0, off1);
    printf("Tile 0 size = %u\n", off1 - off0);

    /* Tile 0 数据 */
    const byte* tile0 = data + off0;
    printf("Tile 0 first 32 bytes: ");
    for (int i = 0; i < 32 && i < (int)(off1 - off0); i++) {
        printf("%02x ", tile0[i]);
    }
    printf("\n");

    /* sub_4ED0B: width(2) + height(2) + raw pixels */
    word w0 = tile0[0] | (tile0[1] << 8);
    word h0 = tile0[2] | (tile0[3] << 8);
    printf("Tile 0 header: w=%u h=%u\n", w0, h0);
    printf("Expected size 4+w*h = %u\n", 4 + w0*h0);
    printf("Actual size = %u\n", off1 - off0);

    /* 尝试解码 */
    byte buf[64*64];
    memset(buf, 0, sizeof(buf));
    /* 先用 raw 像素方式 (4 字节头 + raw 像素) 解码 */
    dword raw_size = (dword)4 + (dword)w0 * (dword)h0;
    if ((dword)(off1 - off0) == raw_size) {
        /* 直接 memcpy */
        memcpy(buf, tile0 + 4, w0 * h0);
        printf("RAW decode: %dx%d, %u bytes\n", w0, h0, w0*h0);
    } else {
        /* 调用 fdother_lmi1_decode_tile */
        int ret = fdother_lmi1_decode_tile(&lmi1, 0, buf, w0 ? w0 : 16);
        printf("decode ret=%d (low16=w, high16=h)\n", ret);
    }
    int aw = w0, ah = h0;
    printf("decoded: w=%d h=%d\n", aw, ah);
    printf("非0像素: ");
    int nz = 0;
    for (int i = 0; i < aw*ah; i++) {
        if (buf[i]) nz++;
    }
    printf("%d / %d\n", nz, aw*ah);

    /* 列出所有tile尺寸 */
    printf("\n=== 所有 23 个 tile 的尺寸 ===\n");
    for (int i = 0; i < (int)lmi1.tile_count; i++) {
        dword addr = 6 + i * 4;
        dword next_addr = 6 + (i+1) * 4;
        if (addr + 4 > size) break;
        dword o = data[addr] | (data[addr+1]<<8) | (data[addr+2]<<16) | (data[addr+3]<<24);
        dword no = (next_addr + 4 <= size)
            ? (data[next_addr] | (data[next_addr+1]<<8) | (data[next_addr+2]<<16) | (data[next_addr+3]<<24))
            : size;
        dword ts = no - o;
        if (o + 4 > size) {
            printf("  tile %d: 偏移0x%x, 越界\n", i, o);
            continue;
        }
        const byte* t = data + o;
        word w = t[0] | (t[1] << 8);
        word h = t[2] | (t[3] << 8);
        if (w > 256 || h > 256) continue;  /* 安全检查 */
        printf("  tile %2d: offset=0x%x, size=%u, header=[w=%d h=%d], expected_raw=%d, %s\n",
               i, o, ts, w, h, 4 + w*h,
               (ts == 4 + w*h) ? "RAW" : (ts < 4 + w*h) ? "RLE/short" : "PADDING");
    }

    fdother_unload();
    return 0;
}
