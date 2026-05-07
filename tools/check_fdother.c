#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>

int main(int argc, char* argv[]) {
    if (argc < 2) {
        fprintf(stderr, "Usage: %s <fdother.dat path>\n", argv[0]);
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
    
    printf("FDOTHER.DAT file size: %ld bytes\n", file_size);
    
    /* 读取头部 */
    uint8_t header[6];
    fread(header, 1, 6, fp);
    printf("Magic: %.*s\n", 6, header);
    
    /* 读取资源数量 */
    uint32_t count;
    fread(&count, 4, 1, fp);
    printf("Resource count: %u\n", count);
    
    /* 读取索引69-73的偏移和大小 */
    for (int i = 69; i <= 73; i++) {
        fseek(fp, 6 + 4 + i * 4, SEEK_SET);
        uint32_t offset;
        fread(&offset, 4, 1, fp);
        
        uint32_t next_offset;
        if (i + 1 < count) {
            fread(&next_offset, 4, 1, fp);
        } else {
            next_offset = file_size;
        }
        
        uint32_t size = next_offset - offset;
        printf("Resource %d: offset=0x%08x (%u), size=%u bytes\n", i, offset, offset, size);
        
        /* 读取前4字节 (width/height header) */
        fseek(fp, offset, SEEK_SET);
        uint8_t img_header[4];
        fread(img_header, 1, 4, fp);
        uint16_t width = img_header[0] | (img_header[1] << 8);
        uint16_t height = img_header[2] | (img_header[3] << 8);
        printf("  -> Image: %dx%d, data_size=%u\n", width, height, size - 4);
    }
    
    fclose(fp);
    return 0;
}
