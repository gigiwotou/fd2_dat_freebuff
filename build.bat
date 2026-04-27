@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

:: FD2 Build Script for Windows (MSYS2)
:: Supports both UCRT64 and MINGW64 environments
:: Usage: build.bat [all|game|test|intro|clean|release] [mingw64]
::        build.bat all          (uses UCRT64 by default)
::        build.bat all mingw64  (uses MINGW64)

:: Detect environment
set MSYS2_PREFIX=C:\msys64\ucrt64
if /I "%~2"=="mingw64" set MSYS2_PREFIX=C:\msys64\mingw64
if /I "%~1"=="mingw64" (
    set MSYS2_PREFIX=C:\msys64\mingw64
    set TARGET=all
)

set GCC=%MSYS2_PREFIX%\bin\gcc.exe
set CFLAGS=-Wall -Wextra -std=gnu99 -Iinclude -I"%MSYS2_PREFIX%\include" -O2 -mconsole -static-libgcc
set LDFLAGS=-L"%MSYS2_PREFIX%\lib" -lSDL2 -lm -static-libgcc
set SDL_LDFLAGS=-lmingw32 -lSDL2main -lSDL2

:: Release flags (no console window, no debug output)
set RELEASE_CFLAGS=-Wall -Wextra -std=gnu99 -Iinclude -I"%MSYS2_PREFIX%\include" -O2 -DNDEBUG -mwindows -static-libgcc
set RELEASE_LDFLAGS=-L"%MSYS2_PREFIX%\lib" -lSDL2 -lm -static-libgcc

set SRC_DIR=src
set OBJ_DIR=obj
set BIN_DIR=bin

:: Object files
set DECODER_OBJ=%OBJ_DIR%\fd2_decoder.o
set GAME_OBJS=%OBJ_DIR%\fd2_input.o %OBJ_DIR%\fd2_render.o %OBJ_DIR%\fd2_audio.o %OBJ_DIR%\fd2_resources.o %OBJ_DIR%\fd2_afm.o %OBJ_DIR%\fd2_game.o %OBJ_DIR%\main.o
set TEST_OBJ=%OBJ_DIR%\fd2_decoder_test.o
set INTRO_OBJ=%OBJ_DIR%\fd2_intro.o

:: Targets
set TARGET_GAME=%BIN_DIR%\fd2.exe
set TARGET_GAME_RELEASE=%BIN_DIR%\fd2_release.exe
set TARGET_TEST=%BIN_DIR%\fd2_decoder_test.exe
set TARGET_INTRO=%BIN_DIR%\fd2_intro.exe

:: Default target
if "%~1"=="" set TARGET=all
if not "%~1"=="" set TARGET=%~1

:: Release target
set RELEASE=0
if /I "%~1"=="release" (
    set TARGET=game
    set RELEASE=1
)

:: Clean
if "%TARGET%"=="clean" (
    echo Cleaning build artifacts...
    if exist %OBJ_DIR% rmdir /S /Q %OBJ_DIR%
    if exist %BIN_DIR% rmdir /S /Q %BIN_DIR%
    echo Clean complete.
    goto :end
)

:: Create directories
if not exist %OBJ_DIR% mkdir %OBJ_DIR%
if not exist %BIN_DIR% mkdir %BIN_DIR%

:: Compile all source files
if "%TARGET%"=="all" (
    call :compile %SRC_DIR%\fd2_decoder.c %DECODER_OBJ%
    if errorlevel 1 goto :error
    call :compile %SRC_DIR%\fd2_input.c %OBJ_DIR%\fd2_input.o
    if errorlevel 1 goto :error
    call :compile %SRC_DIR%\fd2_render.c %OBJ_DIR%\fd2_render.o
    if errorlevel 1 goto :error
    call :compile %SRC_DIR%\fd2_audio.c %OBJ_DIR%\fd2_audio.o
    if errorlevel 1 goto :error
    call :compile %SRC_DIR%\fd2_resources.c %OBJ_DIR%\fd2_resources.o
    if errorlevel 1 goto :error
    call :compile %SRC_DIR%\fd2_afm.c %OBJ_DIR%\fd2_afm.o
    if errorlevel 1 goto :error
    call :compile %SRC_DIR%\fd2_game.c %OBJ_DIR%\fd2_game.o
    if errorlevel 1 goto :error
    call :compile %SRC_DIR%\main.c %OBJ_DIR%\main.o
    if errorlevel 1 goto :error
    call :compile %SRC_DIR%\fd2_decoder_test.c %TEST_OBJ%
    if errorlevel 1 goto :error
    call :compile %SRC_DIR%\fd2_intro.c %INTRO_OBJ%
    if errorlevel 1 goto :error

    echo Linking %TARGET_GAME% ...
    %GCC% %CFLAGS% -o %TARGET_GAME% %GAME_OBJS% %DECODER_OBJ% %LDFLAGS%
    if errorlevel 1 goto :error
    echo [OK] %TARGET_GAME%

    echo Linking %TARGET_TEST% ...
    %GCC% %CFLAGS% -o %TARGET_TEST% %DECODER_OBJ% %TEST_OBJ% -lm
    if errorlevel 1 goto :error
    echo [OK] %TARGET_TEST%

    echo Linking %TARGET_INTRO% ...
    %GCC% %CFLAGS% -o %TARGET_INTRO% %INTRO_OBJ% %DECODER_OBJ% %LDFLAGS% %SDL_LDFLAGS%
    if errorlevel 1 goto :error
    echo [OK] %TARGET_INTRO%
)

:: Individual targets
if "%TARGET%"=="game" goto :build_game
if "%TARGET%"=="test" goto :build_test
if "%TARGET%"=="intro" goto :build_intro

if "%TARGET%"=="all" (
    echo.
    echo Copying required DLLs...
    copy /Y "%MSYS2_PREFIX%\bin\SDL2.dll" "%BIN_DIR%\" >nul 2>&1
    echo Copying game data files...
    if exist game\ (
        for %%F in (game\*) do (
            set "ext=%%~xF"
            if /I not "!ext!"==".exe" (
                if /I not "!ext!"==".i64" (
                    copy /Y "%%F" "%BIN_DIR%\" >nul 2>&1
                )
            )
        )
    )
    echo Build complete! All targets generated in %BIN_DIR%\.
    goto :end
)

echo Unknown target: %TARGET%
echo Usage: build.bat [all^|game^|test^|intro^|clean^|release] [mingw64]
goto :end

:build_game
call :compile %SRC_DIR%\fd2_decoder.c %DECODER_OBJ%
if errorlevel 1 goto :error
call :compile %SRC_DIR%\fd2_input.c %OBJ_DIR%\fd2_input.o
if errorlevel 1 goto :error
call :compile %SRC_DIR%\fd2_render.c %OBJ_DIR%\fd2_render.o
if errorlevel 1 goto :error
call :compile %SRC_DIR%\fd2_audio.c %OBJ_DIR%\fd2_audio.o
if errorlevel 1 goto :error
call :compile %SRC_DIR%\fd2_resources.c %OBJ_DIR%\fd2_resources.o
if errorlevel 1 goto :error
call :compile %SRC_DIR%\fd2_afm.c %OBJ_DIR%\fd2_afm.o
if errorlevel 1 goto :error
call :compile %SRC_DIR%\fd2_game.c %OBJ_DIR%\fd2_game.o
if errorlevel 1 goto :error
call :compile %SRC_DIR%\main.c %OBJ_DIR%\main.o
if errorlevel 1 goto :error

if "%RELEASE%"=="1" (
    echo Linking %TARGET_GAME_RELEASE% (Release Mode)
    %GCC% %RELEASE_CFLAGS% -o %TARGET_GAME_RELEASE% %GAME_OBJS% %DECODER_OBJ% %RELEASE_LDFLAGS%
    if errorlevel 1 goto :error
    echo [OK] %TARGET_GAME_RELEASE%
) else (
    echo Linking %TARGET_GAME%
    %GCC% %CFLAGS% -o %TARGET_GAME% %GAME_OBJS% %DECODER_OBJ% %LDFLAGS%
    if errorlevel 1 goto :error
    echo [OK] %TARGET_GAME%
)
goto :end

:build_test
call :compile %SRC_DIR%\fd2_decoder.c %DECODER_OBJ%
if errorlevel 1 goto :error
call :compile %SRC_DIR%\fd2_decoder_test.c %TEST_OBJ%
if errorlevel 1 goto :error
echo Linking %TARGET_TEST% ...
%GCC% %CFLAGS% -o %TARGET_TEST% %DECODER_OBJ% %TEST_OBJ% -lm
if errorlevel 1 goto :error
echo [OK] %TARGET_TEST%
goto :end

:build_intro
call :compile %SRC_DIR%\fd2_decoder.c %DECODER_OBJ%
if errorlevel 1 goto :error
call :compile %SRC_DIR%\fd2_intro.c %INTRO_OBJ%
if errorlevel 1 goto :error
echo Linking %TARGET_INTRO% ...
%GCC% %CFLAGS% -o %TARGET_INTRO% %INTRO_OBJ% %DECODER_OBJ% %LDFLAGS% %SDL_LDFLAGS%
if errorlevel 1 goto :error
echo [OK] %TARGET_INTRO%
goto :end

:compile
echo Compiling %~1
%GCC% %CFLAGS% -c %~1 -o %~2
if errorlevel 1 (
    echo ERROR: Failed to compile %~1
    exit /b 1
)
exit /b 0

:error
echo.
echo BUILD FAILED!
exit /b 1

:end
endlocal
