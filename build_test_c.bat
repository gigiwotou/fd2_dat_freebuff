@echo off
cd /d d:\workspace\fd2_dat_freebuff
gcc -Wall -Wextra -std=gnu99 -Iinclude -O2 -DFD2_DEBUG ^
    tools/test_c_decode.c ^
    src/fd2_dat.c ^
    src/fd2_rle.c ^
    -o bin/test_c_decode.exe ^
    -lmingw32 -lSDL2 -lm -static-libgcc
if %ERRORLEVEL% EQU 0 (
    echo.
    echo === 编译成功，运行测试 ===
    bin\test_c_decode.exe
) else (
    echo.
    echo === 编译失败 ===
)
pause
