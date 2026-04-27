# Makefile for FD2 reimplementation (Windows/MSYS2)
# Supports both UCRT64 and MINGW64 environments
# Usage: make all          (uses UCRT64 by default)
#        make MINGW64=1 all (uses MINGW64)

# Set temp directory to avoid C:\WINDOWS\ permission issues
export TMPDIR = /tmp

# Detect environment: MINGW64=1 to use mingw64, otherwise ucrt64
ifeq ($(MINGW64),1)
  MSYS2_PREFIX = C:/msys64/mingw64
else
  MSYS2_PREFIX = C:/msys64/ucrt64
endif

# MSYS2 tool paths
GCC = $(MSYS2_PREFIX)/bin/gcc.exe
AR = $(MSYS2_PREFIX)/bin/ar.exe
RM = C:/msys64/usr/bin/rm.exe
MKDIR = C:/msys64/usr/bin/mkdir.exe
MAKE = $(MSYS2_PREFIX)/bin/mingw32-make.exe

# Compiler flags
CFLAGS = -Wall -Wextra -std=gnu99 -Iinclude -I$(MSYS2_PREFIX)/include -O2 -mconsole -static-libgcc
LDFLAGS = -L$(MSYS2_PREFIX)/lib -lSDL2 -lm -static-libgcc

# Release flags (no console window, no debug output)
RELEASE_CFLAGS = -Wall -Wextra -std=gnu99 -Iinclude -I$(MSYS2_PREFIX)/include -O2 -DNDEBUG -mwindows -static-libgcc
RELEASE_LDFLAGS = -L$(MSYS2_PREFIX)/lib -lSDL2 -lm -static-libgcc

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

.PHONY: all clean test decoder intro game release

all: $(TARGET_GAME) $(TARGET_TEST) $(TARGET_INTRO)
	@echo Copying required DLLs...
	-cp $(MSYS2_PREFIX)/bin/SDL2.dll $(BIN_DIR)/ 2>/dev/null
	@echo Copying game data files...
	-cp game/* $(BIN_DIR)/ 2>/dev/null
	-$(RM) -f $(BIN_DIR)/*.exe $(BIN_DIR)/*.i64 2>/dev/null

game: $(TARGET_GAME)

release: $(BIN_DIR)/fd2_release.exe
	@echo Copying required DLLs...
	@cp $(MSYS2_PREFIX)/bin/SDL2.dll $(BIN_DIR)/ 2>/dev/null || true
	@echo Release build complete: $(BIN_DIR)/fd2_release.exe

decoder: $(TARGET_TEST)

test: $(TARGET_TEST)
	./$(TARGET_TEST)

intro: $(TARGET_INTRO)

# ---- Release build (no console, no debug output) ----

$(BIN_DIR)/fd2_release.exe: $(GAME_OBJS) $(DECODER_OBJS) | $(BIN_DIR)
	$(GCC) $(RELEASE_CFLAGS) -o $@ $^ $(RELEASE_LDFLAGS)

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
