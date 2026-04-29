# Makefile for FD2 reimplementation (Cross-platform)
# Supports Linux, Windows/MSYS2 (UCRT64 and MINGW64), macOS
# Usage: make all          (auto-detect platform)
#        make MINGW64=1 all (force MSYS2 MINGW64 on Windows)

# Auto-detect platform
UNAME_S := $(shell uname -s 2>/dev/null)
UNAME_M := $(shell uname -m 2>/dev/null)

# Platform-specific configuration
ifeq ($(OS),Windows_NT)
  PLATFORM := WINDOWS
  MSYS2_PREFIX = C:/msys64/ucrt64
  ifeq ($(MINGW64),1)
    MSYS2_PREFIX = C:/msys64/mingw64
  endif
  CC = $(MSYS2_PREFIX)/bin/gcc.exe
  AR = $(MSYS2_PREFIX)/bin/ar.exe
  RM = C:/msys64/usr/bin/rm.exe
  MKDIR = C:/msys64/usr/bin/mkdir.exe
  EXE_EXT = .exe
  COPY_CMD = C:/msys64/usr/bin/cp.exe
  PLATFORM_CFLAGS = -I$(MSYS2_PREFIX)/include
  PLATFORM_LDFLAGS = -L$(MSYS2_PREFIX)/lib
  PLATFORM_RELEASE_CFLAGS = -I$(MSYS2_PREFIX)/include
  PLATFORM_RELEASE_LDFLAGS = -L$(MSYS2_PREFIX)/lib
  COPY_DLLS = $(COPY_CMD) $(MSYS2_PREFIX)/bin/SDL2.dll $(BIN_DIR)/ 2>/dev/null
  CLEAN_EXTRAS = $(RM) -f $(BIN_DIR)/*.exe $(BIN_DIR)/*.i64 2>/dev/null
else
  ifeq ($(UNAME_S),Linux)
    PLATFORM := LINUX
    CC = gcc
    AR = ar
    RM = rm
    MKDIR = mkdir
    EXE_EXT =
    COPY_CMD = cp
    PLATFORM_CFLAGS =
    PLATFORM_LDFLAGS =
    PLATFORM_RELEASE_CFLAGS =
    PLATFORM_RELEASE_LDFLAGS =
    COPY_DLLS = @true
    CLEAN_EXTRAS = @true
  else ifeq ($(UNAME_S),Darwin)
    PLATFORM := MACOS
    CC = gcc
    AR = ar
    RM = rm
    MKDIR = mkdir
    EXE_EXT =
    COPY_CMD = cp
    PLATFORM_CFLAGS =
    PLATFORM_LDFLAGS =
    PLATFORM_RELEASE_CFLAGS =
    PLATFORM_RELEASE_LDFLAGS =
    COPY_DLLS = @true
    CLEAN_EXTRAS = @true
  else
    $(error Unsupported platform: $(UNAME_S))
  endif
endif

# Common compiler flags
CFLAGS = -Wall -Wextra -std=gnu99 -Iinclude -O2 $(PLATFORM_CFLAGS)
LDFLAGS = -lSDL2 -lm $(PLATFORM_LDFLAGS)

# Release flags (no console window, no debug output)
RELEASE_CFLAGS = -Wall -Wextra -std=gnu99 -Iinclude -O2 -DNDEBUG $(PLATFORM_RELEASE_CFLAGS)
RELEASE_LDFLAGS = -lSDL2 -lm $(PLATFORM_RELEASE_LDFLAGS)

# Windows-specific flags
ifeq ($(PLATFORM),WINDOWS)
  CFLAGS += -mconsole -static-libgcc
  LDFLAGS += -static-libgcc
  RELEASE_CFLAGS += -mwindows -static-libgcc
  RELEASE_LDFLAGS += -static-libgcc
endif

SRC_DIR = src
OBJ_DIR = obj
OBJ_RELEASE_DIR = obj_release
BIN_DIR = bin

# Source files
DECODER_SRCS = $(SRC_DIR)/fd2_decoder.c
DECODER_OBJS = $(OBJ_DIR)/fd2_decoder.o
DECODER_RELEASE_OBJS = $(OBJ_RELEASE_DIR)/fd2_decoder.o

GAME_SRCS = $(SRC_DIR)/fd2_input.c $(SRC_DIR)/fd2_render.c $(SRC_DIR)/fd2_audio.c $(SRC_DIR)/fd2_resources.c $(SRC_DIR)/fd2_afm.c $(SRC_DIR)/fd2_scene.c $(SRC_DIR)/fd2_game.c $(SRC_DIR)/fd2_map_loader.c $(SRC_DIR)/main.c
GAME_OBJS = $(OBJ_DIR)/fd2_input.o $(OBJ_DIR)/fd2_render.o $(OBJ_DIR)/fd2_audio.o $(OBJ_DIR)/fd2_resources.o $(OBJ_DIR)/fd2_afm.o $(OBJ_DIR)/fd2_scene.o $(OBJ_DIR)/fd2_game.o $(OBJ_DIR)/fd2_map_loader.o $(OBJ_DIR)/main.o
GAME_RELEASE_OBJS = $(OBJ_RELEASE_DIR)/fd2_input.o $(OBJ_RELEASE_DIR)/fd2_render.o $(OBJ_RELEASE_DIR)/fd2_audio.o $(OBJ_RELEASE_DIR)/fd2_resources.o $(OBJ_RELEASE_DIR)/fd2_afm.o $(OBJ_RELEASE_DIR)/fd2_scene.o $(OBJ_RELEASE_DIR)/fd2_game.o $(OBJ_RELEASE_DIR)/fd2_map_loader.o $(OBJ_RELEASE_DIR)/main.o

TEST_OBJS = $(OBJ_DIR)/fd2_decoder_test.o
INTRO_OBJS = $(OBJ_DIR)/fd2_intro.o $(DECODER_OBJS)

# Targets
TARGET_GAME   = $(BIN_DIR)/fd2$(EXE_EXT)
TARGET_TEST   = $(BIN_DIR)/fd2_decoder_test$(EXE_EXT)
TARGET_INTRO  = $(BIN_DIR)/fd2_intro$(EXE_EXT)
TARGET_RELEASE = $(BIN_DIR)/fd2_release$(EXE_EXT)

.PHONY: all clean test decoder intro game release

all: $(TARGET_GAME) $(TARGET_TEST) $(TARGET_INTRO)
	@echo Copying required DLLs...
	-$(COPY_DLLS)
	@echo Copying game data files...
	-$(COPY_CMD) game/* $(BIN_DIR)/ 2>/dev/null || true
	-$(CLEAN_EXTRAS)
	@echo Build complete!

game: $(TARGET_GAME)

release: $(TARGET_RELEASE)
	@echo Copying required DLLs...
	-$(COPY_DLLS) || true
	@echo Release build complete: $(TARGET_RELEASE)

decoder: $(TARGET_TEST)

test: $(TARGET_TEST)
	./$(TARGET_TEST)

intro: $(TARGET_INTRO)

# Release build (no console, no debug output) - separate obj dir
$(TARGET_RELEASE): $(GAME_RELEASE_OBJS) $(DECODER_RELEASE_OBJS) | $(BIN_DIR)
	$(CC) $(RELEASE_CFLAGS) -o $@ $^ $(RELEASE_LDFLAGS)

# Main game
$(TARGET_GAME): $(GAME_OBJS) $(DECODER_OBJS) | $(BIN_DIR)
	$(CC) $(CFLAGS) -o $@ $^ $(LDFLAGS)

# Decoder test (no SDL)
$(TARGET_TEST): $(DECODER_OBJS) $(TEST_OBJS) | $(BIN_DIR)
	$(CC) $(CFLAGS) -o $@ $^ -lm

# Legacy intro player
$(TARGET_INTRO): $(INTRO_OBJS) | $(BIN_DIR)
	$(CC) $(CFLAGS) -o $@ $^ $(LDFLAGS)

# Compilation rules (debug)
$(OBJ_DIR)/%.o: $(SRC_DIR)/%.c | $(OBJ_DIR)
	@echo Compiling $<
	$(CC) $(CFLAGS) -c $< -o $@

# Compilation rules (release)
$(OBJ_RELEASE_DIR)/%.o: $(SRC_DIR)/%.c | $(OBJ_RELEASE_DIR)
	@echo Compiling $< (release)
	$(CC) $(RELEASE_CFLAGS) -c $< -o $@

$(BIN_DIR):
	$(MKDIR) -p $@

$(OBJ_DIR):
	$(MKDIR) -p $@

$(OBJ_RELEASE_DIR):
	$(MKDIR) -p $@

clean:
	$(RM) -rf $(OBJ_DIR) $(OBJ_RELEASE_DIR) $(BIN_DIR)
