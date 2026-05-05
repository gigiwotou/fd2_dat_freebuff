@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

:: FD2 Build Script for Windows (MSYS2)
:: Supports both UCRT64 and MINGW64 environments
:: Usage: build.bat [all|game|test|intro|menu_debug|sub_111ba_test|clean|release] [mingw64]

:: Detect environment
set MSYS2_PREFIX=C:\msys64\ucrt64
if /I "%~2"=="mingw64" set MSYS2_PREFIX=C:\msys64\mingw64
if /I "%~1"=="mingw64" (
    set MSYS2_PREFIX=C:\msys64\mingw64
    set TARGET=all
)

set GCC=%MSYS2_PREFIX%\bin\gcc.exe
set CFLAGS=-Wall -Wextra -std=gnu99 -Iinclude -I"%MSYS2_PREFIX%\include" -O2 -DFD2_DEBUG -mconsole -static-libgcc
set LDFLAGS=-L"%MSYS2_PREFIX%\lib" -lmingw32 -lSDL2main -lSDL2 -lm -static-libgcc
set SDL_LDFLAGS=-lmingw32 -lSDL2main -lSDL2 -lm

:: Release flags (no console window, no debug output)
set RELEASE_CFLAGS=-Wall -Wextra -std=gnu99 -Iinclude -I"%MSYS2_PREFIX%\include" -O2 -DNDEBUG -mwindows -static-libgcc
set RELEASE_LDFLAGS=-L"%MSYS2_PREFIX%\lib" -lSDL2 -lm -static-libgcc

set SRC_DIR=src
set OBJ_DIR=obj
set OBJ_RELEASE_DIR=obj_release
set BIN_DIR=bin
set EXE_EXT=.exe

:: Object files (debug)
set DECODER_OBJ=%OBJ_DIR%\fd2_decoder.o
set GAME_OBJS=%OBJ_DIR%\fd2_input.o %OBJ_DIR%\fd2_render.o %OBJ_DIR%\fd2_audio.o %OBJ_DIR%\fd2_resources.o %OBJ_DIR%\fd2_afm.o %OBJ_DIR%\fd2_map_loader.o %OBJ_DIR%\fd2_icon_b24.o %OBJ_DIR%\fd2_sprite.o %OBJ_DIR%\main.o %OBJ_DIR%\fd2_save_load.o %OBJ_DIR%\fd2_state_machine.o %OBJ_DIR%\fd2_scenes.o %OBJ_DIR%\fd2_globals.o %OBJ_DIR%\fd2_data_loader.o %OBJ_DIR%\fd2_scene_interact.o %OBJ_DIR%\fd2_input_scan.o %OBJ_DIR%\fd2_rle.o

:: Object files (release)
set DECODER_RELEASE_OBJ=%OBJ_RELEASE_DIR%\fd2_decoder.o
set GAME_RELEASE_OBJS=%OBJ_RELEASE_DIR%\fd2_input.o %OBJ_RELEASE_DIR%\fd2_render.o %OBJ_RELEASE_DIR%\fd2_audio.o %OBJ_RELEASE_DIR%\fd2_resources.o %OBJ_RELEASE_DIR%\fd2_afm.o %OBJ_RELEASE_DIR%\fd2_map_loader.o %OBJ_RELEASE_DIR%\fd2_icon_b24.o %OBJ_RELEASE_DIR%\fd2_sprite.o %OBJ_RELEASE_DIR%\main.o %OBJ_RELEASE_DIR%\fd2_save_load.o %OBJ_RELEASE_DIR%\fd2_state_machine.o %OBJ_RELEASE_DIR%\fd2_scenes.o %OBJ_RELEASE_DIR%\fd2_globals.o %OBJ_RELEASE_DIR%\fd2_data_loader.o %OBJ_RELEASE_DIR%\fd2_scene_interact.o %OBJ_RELEASE_DIR%\fd2_input_scan.o %OBJ_RELEASE_DIR%\fd2_rle.o

:: Targets
set TARGET_GAME=%BIN_DIR%\fd2%EXE_EXT%
set TARGET_GAME_RELEASE=%BIN_DIR%\fd2_release%EXE_EXT%

:: Parse arguments (order-independent)
set TARGET=all
set RELEASE=0

:arg_loop
if "%~1"=="" goto :arg_done
if /I "%~1"=="all" set TARGET=all
if /I "%~1"=="game" set TARGET=game
if /I "%~1"=="clean" set TARGET=clean
if /I "%~1"=="release" set RELEASE=1
if /I "%~1"=="mingw64" set MSYS2_PREFIX=C:\msys64\mingw64
shift
goto :arg_loop
:arg_done

:: If release mode, set target to release
if "%RELEASE%"=="1" (
    if "%TARGET%"=="game" set TARGET=release
)

:: Clean
if "%TARGET%"=="clean" (
    echo Cleaning build artifacts...
    if exist %OBJ_DIR% rmdir /S /Q %OBJ_DIR%
    if exist %OBJ_RELEASE_DIR% rmdir /S /Q %OBJ_RELEASE_DIR%
    if exist %BIN_DIR% (
        for %%F in (%BIN_DIR%\*.exe) do (
            del /F /Q "%%F" 2>nul
        )
    )
    echo Clean complete.
    goto :end
)

:: Create directories
if not exist %OBJ_DIR% mkdir %OBJ_DIR%
if not exist %OBJ_RELEASE_DIR% mkdir %OBJ_RELEASE_DIR%
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
    call :compile %SRC_DIR%\fd2_map_loader.c %OBJ_DIR%\fd2_map_loader.o
    if errorlevel 1 goto :error
    call :compile %SRC_DIR%\fd2_icon_b24.c %OBJ_DIR%\fd2_icon_b24.o
    if errorlevel 1 goto :error
    call :compile %SRC_DIR%\fd2_sprite.c %OBJ_DIR%\fd2_sprite.o
    if errorlevel 1 goto :error
    call :compile %SRC_DIR%\main.c %OBJ_DIR%\main.o
    if errorlevel 1 goto :error
    call :compile %SRC_DIR%\fd2_save_load.c %OBJ_DIR%\fd2_save_load.o
    if errorlevel 1 goto :error
    call :compile %SRC_DIR%\fd2_state_machine.c %OBJ_DIR%\fd2_state_machine.o
    if errorlevel 1 goto :error
    call :compile %SRC_DIR%\fd2_scenes.c %OBJ_DIR%\fd2_scenes.o
    if errorlevel 1 goto :error
    call :compile %SRC_DIR%\fd2_globals.c %OBJ_DIR%\fd2_globals.o
    if errorlevel 1 goto :error
    call :compile %SRC_DIR%\fd2_data_loader.c %OBJ_DIR%\fd2_data_loader.o
    if errorlevel 1 goto :error
    call :compile %SRC_DIR%\fd2_scene_interact.c %OBJ_DIR%\fd2_scene_interact.o
    if errorlevel 1 goto :error
    call :compile %SRC_DIR%\fd2_input_scan.c %OBJ_DIR%\fd2_input_scan.o
    if errorlevel 1 goto :error

    echo Linking %TARGET_GAME% ...
    %GCC% %CFLAGS% -o %TARGET_GAME% %GAME_OBJS% %DECODER_OBJ% %LDFLAGS%
    if errorlevel 1 goto :error
    echo [OK] %TARGET_GAME%

    echo.
    echo Copying required DLLs...
)

:: Individual targets
if "%TARGET%"=="game" goto :build_game
if "%TARGET%"=="release" goto :build_release

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
                    if /I not "!ext!"==".ini" (
                        if /I not "!ext!"==".MDI" (
                            if /I not "!ext!"==".DIG" (
                                copy /Y "%%F" "%BIN_DIR%\" >nul 2>&1
                            )
                        )
                    )
                )
            )
        )
    )
    echo Build complete! All targets generated in %BIN_DIR%\.
    goto :end
)

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
call :compile %SRC_DIR%\fd2_map_loader.c %OBJ_DIR%\fd2_map_loader.o
if errorlevel 1 goto :error
call :compile %SRC_DIR%\fd2_icon_b24.c %OBJ_DIR%\fd2_icon_b24.o
if errorlevel 1 goto :error
call :compile %SRC_DIR%\fd2_sprite.c %OBJ_DIR%\fd2_sprite.o
if errorlevel 1 goto :error
call :compile %SRC_DIR%\main.c %OBJ_DIR%\main.o
if errorlevel 1 goto :error
call :compile %SRC_DIR%\fd2_save_load.c %OBJ_DIR%\fd2_save_load.o
if errorlevel 1 goto :error
call :compile %SRC_DIR%\fd2_state_machine.c %OBJ_DIR%\fd2_state_machine.o
if errorlevel 1 goto :error
call :compile %SRC_DIR%\fd2_scenes.c %OBJ_DIR%\fd2_scenes.o
if errorlevel 1 goto :error
call :compile %SRC_DIR%\fd2_globals.c %OBJ_DIR%\fd2_globals.o
if errorlevel 1 goto :error
call :compile %SRC_DIR%\fd2_data_loader.c %OBJ_DIR%\fd2_data_loader.o
if errorlevel 1 goto :error
call :compile %SRC_DIR%\fd2_scene_interact.c %OBJ_DIR%\fd2_scene_interact.o
if errorlevel 1 goto :error
call :compile %SRC_DIR%\fd2_input_scan.c %OBJ_DIR%\fd2_input_scan.o
if errorlevel 1 goto :error

echo Linking %TARGET_GAME%
%GCC% %CFLAGS% -o %TARGET_GAME% %GAME_OBJS% %DECODER_OBJ% %LDFLAGS%
if errorlevel 1 goto :error
echo [OK] %TARGET_GAME%
goto :end

:build_release
call :compile_release %SRC_DIR%\fd2_decoder.c %DECODER_RELEASE_OBJ%
if errorlevel 1 goto :error
call :compile_release %SRC_DIR%\fd2_input.c %OBJ_RELEASE_DIR%\fd2_input.o
if errorlevel 1 goto :error
call :compile_release %SRC_DIR%\fd2_render.c %OBJ_RELEASE_DIR%\fd2_render.o
if errorlevel 1 goto :error
call :compile_release %SRC_DIR%\fd2_audio.c %OBJ_RELEASE_DIR%\fd2_audio.o
if errorlevel 1 goto :error
call :compile_release %SRC_DIR%\fd2_resources.c %OBJ_RELEASE_DIR%\fd2_resources.o
if errorlevel 1 goto :error
call :compile_release %SRC_DIR%\fd2_afm.c %OBJ_RELEASE_DIR%\fd2_afm.o
if errorlevel 1 goto :error
call :compile_release %SRC_DIR%\fd2_map_loader.c %OBJ_RELEASE_DIR%\fd2_map_loader.o
if errorlevel 1 goto :error
call :compile_release %SRC_DIR%\fd2_icon_b24.c %OBJ_RELEASE_DIR%\fd2_icon_b24.o
if errorlevel 1 goto :error
call :compile_release %SRC_DIR%\fd2_sprite.c %OBJ_RELEASE_DIR%\fd2_sprite.o
if errorlevel 1 goto :error
call :compile_release %SRC_DIR%\main.c %OBJ_RELEASE_DIR%\main.o
if errorlevel 1 goto :error
call :compile_release %SRC_DIR%\fd2_save_load.c %OBJ_RELEASE_DIR%\fd2_save_load.o
if errorlevel 1 goto :error
call :compile_release %SRC_DIR%\fd2_state_machine.c %OBJ_RELEASE_DIR%\fd2_state_machine.o
if errorlevel 1 goto :error
call :compile_release %SRC_DIR%\fd2_scenes.c %OBJ_RELEASE_DIR%\fd2_scenes.o
if errorlevel 1 goto :error
call :compile_release %SRC_DIR%\fd2_globals.c %OBJ_RELEASE_DIR%\fd2_globals.o
if errorlevel 1 goto :error
call :compile_release %SRC_DIR%\fd2_data_loader.c %OBJ_RELEASE_DIR%\fd2_data_loader.o
if errorlevel 1 goto :error
call :compile_release %SRC_DIR%\fd2_scene_interact.c %OBJ_RELEASE_DIR%\fd2_scene_interact.o
if errorlevel 1 goto :error
call :compile_release %SRC_DIR%\fd2_input_scan.c %OBJ_RELEASE_DIR%\fd2_input_scan.o
if errorlevel 1 goto :error

echo Linking %TARGET_GAME_RELEASE% (Release Mode)
%GCC% %RELEASE_CFLAGS% -o %TARGET_GAME_RELEASE% %GAME_RELEASE_OBJS% %DECODER_RELEASE_OBJ% %RELEASE_LDFLAGS%
if errorlevel 1 goto :error
echo [OK] %TARGET_GAME_RELEASE%
goto :end

echo Unknown target: %TARGET%
echo Usage: build.bat [all^|game^|clean^|release] [mingw64]
goto :end

:compile
echo Compiling %~1
%GCC% %CFLAGS% -c %~1 -o %~2
if errorlevel 1 (
    echo ERROR: Failed to compile %~1
    exit /b 1
)
exit /b 0

:compile_release
echo Compiling %~1 (release)
%GCC% %RELEASE_CFLAGS% -c %~1 -o %~2
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
