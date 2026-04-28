#!/bin/bash
# FD2 Build Script for Linux
# Usage: ./build.sh [all|game|test|intro|clean|release]

set -e

# Configuration
CC=gcc
CFLAGS="-Wall -Wextra -std=gnu99 -Iinclude -O2"
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
GAME_OBJS="${OBJ_DIR}/fd2_input.o ${OBJ_DIR}/fd2_render.o ${OBJ_DIR}/fd2_audio.o ${OBJ_DIR}/fd2_resources.o ${OBJ_DIR}/fd2_afm.o ${OBJ_DIR}/fd2_game.o ${OBJ_DIR}/main.o"
TEST_OBJ="${OBJ_DIR}/fd2_decoder_test.o"
INTRO_OBJ="${OBJ_DIR}/fd2_intro.o"

# Object files (release)
DECODER_RELEASE_OBJ="${OBJ_RELEASE_DIR}/fd2_decoder.o"
GAME_RELEASE_OBJS="${OBJ_RELEASE_DIR}/fd2_input.o ${OBJ_RELEASE_DIR}/fd2_render.o ${OBJ_RELEASE_DIR}/fd2_audio.o ${OBJ_RELEASE_DIR}/fd2_resources.o ${OBJ_RELEASE_DIR}/fd2_afm.o ${OBJ_RELEASE_DIR}/fd2_game.o ${OBJ_RELEASE_DIR}/main.o"

# Targets
TARGET_GAME="${BIN_DIR}/fd2${EXE_EXT}"
TARGET_GAME_RELEASE="${BIN_DIR}/fd2_release${EXE_EXT}"
TARGET_TEST="${BIN_DIR}/fd2_decoder_test${EXE_EXT}"
TARGET_INTRO="${BIN_DIR}/fd2_intro${EXE_EXT}"

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
    compile "${SRC_DIR}/fd2_game.c" "${OBJ_DIR}/fd2_game.o"
    compile "${SRC_DIR}/main.c" "${OBJ_DIR}/main.o"

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
    compile_release "${SRC_DIR}/fd2_game.c" "${OBJ_RELEASE_DIR}/fd2_game.o"
    compile_release "${SRC_DIR}/main.c" "${OBJ_RELEASE_DIR}/main.o"

    echo "Linking ${TARGET_GAME_RELEASE} (Release Mode)"
    $CC $RELEASE_CFLAGS -o "${TARGET_GAME_RELEASE}" ${GAME_RELEASE_OBJS} ${DECODER_RELEASE_OBJ} ${RELEASE_LDFLAGS}
}

build_test() {
    compile "${SRC_DIR}/fd2_decoder.c" "${DECODER_OBJ}"
    compile "${SRC_DIR}/fd2_decoder_test.c" "${TEST_OBJ}"
    echo "Linking ${TARGET_TEST}"
    $CC $CFLAGS -o "${TARGET_TEST}" "${DECODER_OBJ}" "${TEST_OBJ}" -lm
}

build_intro() {
    compile "${SRC_DIR}/fd2_decoder.c" "${DECODER_OBJ}"
    compile "${SRC_DIR}/fd2_intro.c" "${INTRO_OBJ}"
    echo "Linking ${TARGET_INTRO}"
    $CC $CFLAGS -o "${TARGET_INTRO}" "${INTRO_OBJ}" "${DECODER_OBJ}" ${LDFLAGS}
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
        compile "${SRC_DIR}/fd2_decoder.c" "${DECODER_OBJ}"
        compile "${SRC_DIR}/fd2_input.c" "${OBJ_DIR}/fd2_input.o"
        compile "${SRC_DIR}/fd2_render.c" "${OBJ_DIR}/fd2_render.o"
        compile "${SRC_DIR}/fd2_audio.c" "${OBJ_DIR}/fd2_audio.o"
        compile "${SRC_DIR}/fd2_resources.c" "${OBJ_DIR}/fd2_resources.o"
        compile "${SRC_DIR}/fd2_afm.c" "${OBJ_DIR}/fd2_afm.o"
        compile "${SRC_DIR}/fd2_game.c" "${OBJ_DIR}/fd2_game.o"
        compile "${SRC_DIR}/main.c" "${OBJ_DIR}/main.o"
        compile "${SRC_DIR}/fd2_decoder_test.c" "${TEST_OBJ}"
        compile "${SRC_DIR}/fd2_intro.c" "${INTRO_OBJ}"

        echo "Linking ${TARGET_GAME}"
        $CC $CFLAGS -o "${TARGET_GAME}" ${GAME_OBJS} ${DECODER_OBJ} ${LDFLAGS}
        echo "[OK] ${TARGET_GAME}"

        echo "Linking ${TARGET_TEST}"
        $CC $CFLAGS -o "${TARGET_TEST}" "${DECODER_OBJ}" "${TEST_OBJ}" -lm
        echo "[OK] ${TARGET_TEST}"

        echo "Linking ${TARGET_INTRO}"
        $CC $CFLAGS -o "${TARGET_INTRO}" "${INTRO_OBJ}" "${DECODER_OBJ}" ${LDFLAGS}
        echo "[OK] ${TARGET_INTRO}"

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
    test)
        build_test
        ;;
    intro)
        build_intro
        ;;
    clean)
        clean
        ;;
    *)
        echo "Unknown target: $TARGET"
        echo "Usage: $0 [all|game|test|intro|clean|release]"
        exit 1
        ;;
esac

echo "Build successful!"
