#!/bin/bash
# FD2 Build Script for Linux
# Usage: ./build.sh [all|game|clean|release]

set -e

# Configuration
CC=gcc
CFLAGS="-Wall -Wextra -std=gnu99 -Iinclude -O2 -DFD2_DEBUG"
LDFLAGS="-lSDL2 -lm"

# Release flags (no debug output)
RELEASE_CFLAGS="-Wall -Wextra -std=gnu99 -Iinclude -O2 -DNDEBUG"
RELEASE_LDFLAGS="-lSDL2 -lm"

SRC_DIR=src
OBJ_DIR=obj
OBJ_RELEASE_DIR=obj_release
BIN_DIR=bin
EXE_EXT=""

# Object files (debug)
DECODER_OBJ="${OBJ_DIR}/fd2_decoder.o"
GAME_OBJS="${OBJ_DIR}/fd2_input.o ${OBJ_DIR}/fd2_render.o ${OBJ_DIR}/fd2_audio.o ${OBJ_DIR}/fd2_resources.o ${OBJ_DIR}/fd2_afm.o ${OBJ_DIR}/fd2_map_loader.o ${OBJ_DIR}/fd2_icon_b24.o ${OBJ_DIR}/fd2_sprite.o ${OBJ_DIR}/main.o ${OBJ_DIR}/fd2_save_load.o ${OBJ_DIR}/fd2_state_machine.o ${OBJ_DIR}/fd2_scenes.o ${OBJ_DIR}/fd2_globals.o ${OBJ_DIR}/fd2_data_loader.o ${OBJ_DIR}/fd2_scene_interact.o ${OBJ_DIR}/fd2_input_scan.o"

# Object files (release)
DECODER_RELEASE_OBJ="${OBJ_RELEASE_DIR}/fd2_decoder.o"
GAME_RELEASE_OBJS="${OBJ_RELEASE_DIR}/fd2_input.o ${OBJ_RELEASE_DIR}/fd2_render.o ${OBJ_RELEASE_DIR}/fd2_audio.o ${OBJ_RELEASE_DIR}/fd2_resources.o ${OBJ_RELEASE_DIR}/fd2_afm.o ${OBJ_RELEASE_DIR}/fd2_map_loader.o ${OBJ_RELEASE_DIR}/fd2_icon_b24.o ${OBJ_RELEASE_DIR}/fd2_sprite.o ${OBJ_RELEASE_DIR}/main.o ${OBJ_RELEASE_DIR}/fd2_save_load.o ${OBJ_RELEASE_DIR}/fd2_state_machine.o ${OBJ_RELEASE_DIR}/fd2_scenes.o ${OBJ_RELEASE_DIR}/fd2_globals.o ${OBJ_RELEASE_DIR}/fd2_data_loader.o ${OBJ_RELEASE_DIR}/fd2_scene_interact.o ${OBJ_RELEASE_DIR}/fd2_input_scan.o"

# Targets
TARGET_GAME="${BIN_DIR}/fd2${EXE_EXT}"
TARGET_GAME_RELEASE="${BIN_DIR}/fd2_release${EXE_EXT}"

# Default target
TARGET=${1:-all}
RELEASE=0

# Functions
compile() {
    echo "Compiling $1"
    $CC $CFLAGS -c "$1" -o "$2"
}

compile_release() {
    echo "Compiling $1 (release)"
    $CC $RELEASE_CFLAGS -c "$1" -o "$2"
}

build_game() {
    compile "${SRC_DIR}/fd2_decoder.c" "${DECODER_OBJ}"
    compile "${SRC_DIR}/fd2_input.c" "${OBJ_DIR}/fd2_input.o"
    compile "${SRC_DIR}/fd2_render.c" "${OBJ_DIR}/fd2_render.o"
    compile "${SRC_DIR}/fd2_audio.c" "${OBJ_DIR}/fd2_audio.o"
    compile "${SRC_DIR}/fd2_resources.c" "${OBJ_DIR}/fd2_resources.o"
    compile "${SRC_DIR}/fd2_afm.c" "${OBJ_DIR}/fd2_afm.o"
    compile "${SRC_DIR}/fd2_map_loader.c" "${OBJ_DIR}/fd2_map_loader.o"
    compile "${SRC_DIR}/fd2_icon_b24.c" "${OBJ_DIR}/fd2_icon_b24.o"
    compile "${SRC_DIR}/fd2_sprite.c" "${OBJ_DIR}/fd2_sprite.o"
    compile "${SRC_DIR}/main.c" "${OBJ_DIR}/main.o"
    compile "${SRC_DIR}/fd2_save_load.c" "${OBJ_DIR}/fd2_save_load.o"
    compile "${SRC_DIR}/fd2_state_machine.c" "${OBJ_DIR}/fd2_state_machine.o"
    compile "${SRC_DIR}/fd2_scenes.c" "${OBJ_DIR}/fd2_scenes.o"
    compile "${SRC_DIR}/fd2_globals.c" "${OBJ_DIR}/fd2_globals.o"
    compile "${SRC_DIR}/fd2_data_loader.c" "${OBJ_DIR}/fd2_data_loader.o"
    compile "${SRC_DIR}/fd2_scene_interact.c" "${OBJ_DIR}/fd2_scene_interact.o"
    compile "${SRC_DIR}/fd2_input_scan.c" "${OBJ_DIR}/fd2_input_scan.o"

    echo "Linking ${TARGET_GAME}"
    $CC $CFLAGS -o "${TARGET_GAME}" ${GAME_OBJS} ${DECODER_OBJ} ${LDFLAGS}
}

build_release() {
    compile_release "${SRC_DIR}/fd2_decoder.c" "${DECODER_RELEASE_OBJ}"
    compile_release "${SRC_DIR}/fd2_input.c" "${OBJ_RELEASE_DIR}/fd2_input.o"
    compile_release "${SRC_DIR}/fd2_render.c" "${OBJ_RELEASE_DIR}/fd2_render.o"
    compile_release "${SRC_DIR}/fd2_audio.c" "${OBJ_RELEASE_DIR}/fd2_audio.o"
    compile_release "${SRC_DIR}/fd2_resources.c" "${OBJ_RELEASE_DIR}/fd2_resources.o"
    compile_release "${SRC_DIR}/fd2_afm.c" "${OBJ_RELEASE_DIR}/fd2_afm.o"
    compile_release "${SRC_DIR}/fd2_map_loader.c" "${OBJ_RELEASE_DIR}/fd2_map_loader.o"
    compile_release "${SRC_DIR}/fd2_icon_b24.c" "${OBJ_RELEASE_DIR}/fd2_icon_b24.o"
    compile_release "${SRC_DIR}/fd2_sprite.c" "${OBJ_RELEASE_DIR}/fd2_sprite.o"
    compile_release "${SRC_DIR}/main.c" "${OBJ_RELEASE_DIR}/main.o"
    compile_release "${SRC_DIR}/fd2_save_load.c" "${OBJ_RELEASE_DIR}/fd2_save_load.o"
    compile_release "${SRC_DIR}/fd2_state_machine.c" "${OBJ_RELEASE_DIR}/fd2_state_machine.o"
    compile_release "${SRC_DIR}/fd2_scenes.c" "${OBJ_RELEASE_DIR}/fd2_scenes.o"
    compile_release "${SRC_DIR}/fd2_globals.c" "${OBJ_RELEASE_DIR}/fd2_globals.o"
    compile_release "${SRC_DIR}/fd2_data_loader.c" "${OBJ_RELEASE_DIR}/fd2_data_loader.o"
    compile_release "${SRC_DIR}/fd2_scene_interact.c" "${OBJ_RELEASE_DIR}/fd2_scene_interact.o"
    compile_release "${SRC_DIR}/fd2_input_scan.c" "${OBJ_RELEASE_DIR}/fd2_input_scan.o"

    echo "Linking ${TARGET_GAME_RELEASE} (Release Mode)"
    $CC $RELEASE_CFLAGS -o "${TARGET_GAME_RELEASE}" ${GAME_RELEASE_OBJS} ${DECODER_RELEASE_OBJ} ${RELEASE_LDFLAGS}
}

clean() {
    echo "Cleaning build artifacts..."
    rm -rf "${OBJ_DIR}" "${OBJ_RELEASE_DIR}" "${BIN_DIR}"
    echo "Clean complete."
}

# Create directories
mkdir -p "${OBJ_DIR}" "${OBJ_RELEASE_DIR}" "${BIN_DIR}"

# Build targets
case "$TARGET" in
    all)
        build_game
        echo ""
        echo "Copying game data files..."
        if [ -d "game" ]; then
            cp -r game/* "${BIN_DIR}/" 2>/dev/null || true
        fi
        echo "Build complete! All targets generated in ${BIN_DIR}/."
        ;;
    game)
        build_game
        ;;
    release)
        build_release
        ;;
    clean)
        clean
        ;;
    *)
        echo "Unknown target: $TARGET"
        echo "Usage: $0 [all|game|clean|release]"
        exit 1
        ;;
esac

echo "Build successful!"
