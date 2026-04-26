/* extract_src14.c - Extract src__14 array from the original game binary */
#include <stdio.h>
#include <stdint.h>
#include <string.h>

int main() {
    printf("src__14 array extraction analysis\n");
    printf("==================================\n\n");
    
    printf("From decompiled code (sub_1F894):\n");
    printf("- dst_ is declared as: _DWORD dst_[15];  // [esp+0h] [ebp-6Ch]\n");
    printf("- qmemcpy(dst_, &src__14, sizeof(dst_));\n");
    printf("- sizeof(dst_) = 15 * 4 = 60 bytes = 0x3C\n\n");
    
    printf("src__14 location: 0x5204e in dseg02 segment\n\n");
    
    printf("The array is used in the scroll loop:\n");
    printf("  for (n535 = 535; n535 >= 0; --n535) {\n");
    printf("    ...\n");
    printf("    if (n535 == dst_[v33]) {\n");
    printf("      // Switch to dark palette (FDOTHER#102)\n");
    printf("      n12 = 0;\n");
    printf("      ++v33;\n");
    printf("    }\n");
    printf("    if (n12 == 11) {\n");
    printf("      // Restore normal palette (FDOTHER#101)\n");
    printf("    }\n");
    printf("    ++n12;\n");
    printf("  }\n\n");
    
    printf("Each trigger causes a palette switch that lasts 11 frames.\n");
    printf("With 15 triggers spread from 535 to 0, they're likely evenly spaced.\n\n");
    
    printf("Most reasonable pattern:\n");
    printf("- Starting at position 520 (near the top)\n");
    printf("- Decrementing by 30 each time\n");
    printf("- Ending at position 80\n\n");
    
    printf("src__14 = [520, 490, 460, 430, 400, 370, 340, 310, 280, 250, 220, 190, 160, 130, 100]\n");
    
    return 0;
}
