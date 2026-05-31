@echo off
setlocal

REM 编译viewer
set CC=C:\msys64\mingw64\bin\gcc.exe
set CFLAGS=-Wall -Wextra -std=gnu99 -Iinclude -O2 -DFD2_DEBUG -mconsole -static-libgcc
set LDFLAGS=-lmingw32 -lSDL2main -lSDL2 -lm -static-libgcc

echo 编译 fd2_fdother_viewer...
%CC% %CFLAGS% ^
    src/fd2_fdother_viewer.c ^
    src/fd2_fdother_resources.c ^
    src/fd2_dat.c ^
    src/fd2_rle.c ^
    src/fd2_sfx.c ^
    -o bin/fd2_fdother_viewer.exe ^
    %LDFLAGS%

if %ERRORLEVEL% EQU 0 (
    echo.
    echo 编译成功！
    echo 运行 viewer...
    echo.
    bin\fd2_fdother_viewer.exe
) else (
    echo.
    echo 编译失败！
)

pause
