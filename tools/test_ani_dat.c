#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>

int main(int argc, char* argv[]) {
    if (argc < 2) {
        fprintf(stderr, "Usage: %s <ani.dat path>\n", argv[0]);
        return 1;
    }
    
    FILE* fp = fopen(argv[1], "rb");
    if (!fp) {
        perror("fopen");
        return 1;
    }
    
    /* 读取文件大小 */
    fseek(fp, 0, SEEK_END);
    long file_size = ftell(fp);
    fseek(fp, 0, SEEK_SET);
    
    printf("ANI.DAT file size: %ld bytes\n", file_size);
    
    /* 读取前100字节 */
    uint8_t header[100];
    size_t read = fread(header, 1, 100, fp);
    printf("First 100 bytes:\n");
    for (size_t i = 0; i < read; i++) {
        if (i % 16 == 0) printf("  %04lx: ", i);
        printf("%02x ", header[i]);
        if (i % 16 == 15 || i == read - 1) printf("\n");
    }
    
    /* 根据原始游戏逻辑: fseek(_rb_, 4 * a5 + 6, 0) */
    /* 对于a5=3: fseek(fp, 4*3+6, 0) = fseek(fp, 18, 0) */
    /* 然后读取8字节 */
    for (int a5 = 0; a5 < 5; a5++) {
        long offset = 4 * a5 + 6;
        fseek(fp, offset, SEEK_SET);
        
        uint8_t idx_data[8];
        fread(idx_data, 1, 8, fp);
        
        uint32_t anim_offset = idx_data[0] | (idx_data[1] << 8) | 
                               (idx_data[2] << 16) | (idx_data[3] << 24);
        uint32_t anim_size = idx_data[4] | (idx_data[5] << 8) | 
                             (idx_data[6] << 16) | (idx_data[7] << 24);
        
        printf("Index %d: offset=0x%08x (%u), size_from_8bytes=0x%08x (%u)\n", 
               a5, anim_offset, anim_offset, anim_size, anim_size);
        
        /* 定位到动画数据 */
        fseek(fp, anim_offset, SEEK_SET);
        
        /* 读取173字节头 */
        uint8_t afm_header[173];
        fread(afm_header, 1, 173, fp);
        
        /* 检查AFM签名 */
        if (afm_header[0] == 'A' && afm_header[1] == 'F' && afm_header[2] == 'M') {
            printf("  -> Valid AFM signature found at offset 0x%08lx\n", anim_offset);
            
            /* 读取帧数 (偏移165) */
            uint16_t frame_count = afm_header[165] | (afm_header[166] << 8);
            printf("  -> Frame count: %u\n", frame_count);
        } else {
            printf("  -> No AFM signature, first 16 bytes: ");
            for (int i = 0; i < 16; i++) {
                printf("%02x ", afm_header[i]);
            }
            printf("\n");
        }
    }
    
    fclose(fp);
    return 0;
}
