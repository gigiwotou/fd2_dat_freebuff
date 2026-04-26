# Makefile for FD2 reimplementation (Windows/MSYS2)

# Set temp directory to avoid C:\WINDOWS\ permission issues
export TMPDIR = /tmp

# MSYS2 tool paths
GCC = C:/msys64/ucrt64/bin/gcc.exe
AR = C:/msys64/ucrt64/bin/ar.exe
RM = C:/msys64/usr/bin/rm.exe
MKDIR = C:/msys64/usr/bin/mkdir.exe
MAKE = C:/msys64/ucrt64/bin/mingw32-make.exe

# Compiler flags
CFLAGS = -Wall -Wextra -std=gnu99 -Iinclude -IC:/msys64/ucrt64/include -O2 -mconsole -static-libgcc
LDFLAGS = -LC:/msys64/ucrt64/lib -lSDL2 -lm -static-libgcc

SRC_DIR = src
OBJ_DIR = obj
BIN_DIR = bin

# ---- Source Files ----

# Core decoder library (no SDL dependency)
DECODER_SRCS = $(SRC_DIR)/fd2_decoder.c
DECODER_OBJS = $(OBJ_DIR)/fd2_decoder.o

# Game framework (requires SDL2)
GAME_SRCS = $(SRC_DIR)/fd2_input.c $(SRC_DIR)/fd2_render.c $(SRC_DIR)/fd2_audio.c $(SRC_DIR)/fd2_resources.c $(SRC_DIR)/fd2_afm.c $(SRC_DIR)/fd2_game.c $(SRC_DIR)/main.c
GAME_OBJS = $(OBJ_DIR)/fd2_input.o $(OBJ_DIR)/fd2_render.o $(OBJ_DIR)/fd2_audio.o $(OBJ_DIR)/fd2_resources.o $(OBJ_DIR)/fd2_afm.o $(OBJ_DIR)/fd2_game.o $(OBJ_DIR)/main.o

# Legacy standalone programs
TEST_OBJS = $(OBJ_DIR)/fd2_decoder_test.o
INTRO_OBJS = $(OBJ_DIR)/fd2_intro.o $(DECODER_OBJS)

# ---- Targets ----

TARGET_GAME   = $(BIN_DIR)/fd2.exe
TARGET_TEST   = $(BIN_DIR)/fd2_decoder_test.exe
TARGET_INTRO  = $(BIN_DIR)/fd2_intro.exe

.PHONY: all clean test decoder intro game

all: $(TARGET_GAME) $(TARGET_TEST) $(TARGET_INTRO)
	@echo Copying required DLLs...
	@cp C:/msys64/ucrt64/bin/libwinpthread-1.dll $(BIN_DIR)/ 2>/dev/null || true
	@cp C:/msys64/ucrt64/bin/SDL2.dll $(BIN_DIR)/ 2>/dev/null || true

game: $(TARGET_GAME)

decoder: $(TARGET_TEST)

test: $(TARGET_TEST)
	./$(TARGET_TEST)

intro: $(TARGET_INTRO)

# ---- Main game ----

$(TARGET_GAME): $(GAME_OBJS) $(DECODER_OBJS) | $(BIN_DIR)
	$(GCC) $(CFLAGS) -o $@ $^ $(LDFLAGS)

# ---- Decoder test (no SDL) ----

$(TARGET_TEST): $(DECODER_OBJS) $(TEST_OBJS) | $(BIN_DIR)
	$(GCC) $(CFLAGS) -o $@ $^ -lm

# ---- Legacy intro player ----

$(TARGET_INTRO): $(INTRO_OBJS) | $(BIN_DIR)
	$(GCC) $(CFLAGS) -o $@ $^ $(LDFLAGS) -lmingw32 -lSDL2main -lSDL2

# ---- Compilation rules ----

$(OBJ_DIR)/%.o: $(SRC_DIR)/%.c | $(OBJ_DIR)
	@echo Compiling $<
	$(GCC) $(CFLAGS) -c $< -o $@

$(BIN_DIR):
	$(MKDIR) -p $@

$(OBJ_DIR):
	$(MKDIR) -p $@

clean:
	$(RM) -rf $(OBJ_DIR) $(BIN_DIR)
