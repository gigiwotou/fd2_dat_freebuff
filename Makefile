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
CFLAGS = -Wall -Wextra -std=gnu99 -Iinclude -O2 -DFD2_DEBUG $(PLATFORM_CFLAGS)
LDFLAGS = -lSDL2 -lm $(PLATFORM_LDFLAGS)

# Release flags (no console window, no debug output)
RELEASE_CFLAGS = -Wall -Wextra -std=gnu99 -Iinclude -O2 -DNDEBUG $(PLATFORM_RELEASE_CFLAGS)
RELEASE_LDFLAGS = -lSDL2 -lm $(PLATFORM_RELEASE_LDFLAGS)

# Windows-specific flags
ifeq ($(PLATFORM),WINDOWS)
  CFLAGS += -mconsole -static-libgcc
  LDFLAGS += -lSDL2main -static-libgcc
  RELEASE_CFLAGS += -mwindows -static-libgcc
  RELEASE_LDFLAGS += -lSDL2main -static-libgcc
  COPY_DLLS = $(COPY_CMD) $(MSYS2_PREFIX)/bin/SDL2.dll $(BIN_DIR)/ 2>/dev/null
endif

SRC_DIR = src
OBJ_DIR = obj
OBJ_RELEASE_DIR = obj_release
BIN_DIR = bin

# Source files
DECODER_SRCS = $(SRC_DIR)/fd2_decoder.c
DECODER_OBJS = $(OBJ_DIR)/fd2_decoder.o
DECODER_RELEASE_OBJS = $(OBJ_RELEASE_DIR)/fd2_decoder.o

GAME_SRCS = $(SRC_DIR)/fd2_input.c $(SRC_DIR)/fd2_render.c $(SRC_DIR)/fd2_audio.c $(SRC_DIR)/fd2_resources.c $(SRC_DIR)/fd2_afm.c $(SRC_DIR)/fd2_scene.c $(SRC_DIR)/fd2_game_core.c $(SRC_DIR)/fd2_map_loader.c $(SRC_DIR)/fd2_icon_b24.c $(SRC_DIR)/fd2_sprite.c $(SRC_DIR)/main.c $(SRC_DIR)/fd2_states.c $(SRC_DIR)/fd2_states_intro.c $(SRC_DIR)/fd2_menu.c $(SRC_DIR)/fd2_battle.c $(SRC_DIR)/fd2_battle_sprite.c $(SRC_DIR)/fd2_battle_cursor.c $(SRC_DIR)/fd2_battle_menu.c $(SRC_DIR)/fd2_battle_terrain_info.c $(SRC_DIR)/fd2_save_load.c $(SRC_DIR)/fd2_continue.c $(SRC_DIR)/fd2_cutscene.c
GAME_OBJS = $(OBJ_DIR)/fd2_input.o $(OBJ_DIR)/fd2_render.o $(OBJ_DIR)/fd2_audio.o $(OBJ_DIR)/fd2_resources.o $(OBJ_DIR)/fd2_afm.o $(OBJ_DIR)/fd2_scene.o $(OBJ_DIR)/fd2_game_core.o $(OBJ_DIR)/fd2_map_loader.o $(OBJ_DIR)/fd2_icon_b24.o $(OBJ_DIR)/fd2_sprite.o $(OBJ_DIR)/main.o $(OBJ_DIR)/fd2_states.o $(OBJ_DIR)/fd2_states_intro.o $(OBJ_DIR)/fd2_menu.o $(OBJ_DIR)/fd2_battle.o $(OBJ_DIR)/fd2_battle_sprite.o $(OBJ_DIR)/fd2_battle_cursor.o $(OBJ_DIR)/fd2_battle_menu.o $(OBJ_DIR)/fd2_battle_terrain_info.o $(OBJ_DIR)/fd2_save_load.o $(OBJ_DIR)/fd2_continue.o $(OBJ_DIR)/fd2_cutscene.o
GAME_RELEASE_OBJS = $(OBJ_RELEASE_DIR)/fd2_input.o $(OBJ_RELEASE_DIR)/fd2_render.o $(OBJ_RELEASE_DIR)/fd2_audio.o $(OBJ_RELEASE_DIR)/fd2_resources.o $(OBJ_RELEASE_DIR)/fd2_afm.o $(OBJ_RELEASE_DIR)/fd2_scene.o $(OBJ_RELEASE_DIR)/fd2_game_core.o $(OBJ_RELEASE_DIR)/fd2_map_loader.o $(OBJ_RELEASE_DIR)/fd2_icon_b24.o $(OBJ_RELEASE_DIR)/fd2_sprite.o $(OBJ_RELEASE_DIR)/main.o $(OBJ_RELEASE_DIR)/fd2_states.o $(OBJ_RELEASE_DIR)/fd2_states_intro.o $(OBJ_RELEASE_DIR)/fd2_menu.o $(OBJ_RELEASE_DIR)/fd2_battle.o $(OBJ_RELEASE_DIR)/fd2_battle_sprite.o $(OBJ_RELEASE_DIR)/fd2_battle_cursor.o $(OBJ_RELEASE_DIR)/fd2_battle_menu.o $(OBJ_RELEASE_DIR)/fd2_battle_terrain_info.o $(OBJ_RELEASE_DIR)/fd2_save_load.o $(OBJ_RELEASE_DIR)/fd2_continue.o $(OBJ_RELEASE_DIR)/fd2_cutscene.o

# Modern architecture sources
MODERN_SRCS = $(SRC_DIR)/platform/sdl_video.c $(SRC_DIR)/platform/sdl_audio.c $(SRC_DIR)/platform/sdl_input.c $(SRC_DIR)/platform/sdl_file.c $(SRC_DIR)/platform/sdl_time.c $(SRC_DIR)/core/event_bus.c $(SRC_DIR)/core/sim/entity.c $(SRC_DIR)/core/sim/systems.c
MODERN_OBJS = $(OBJ_DIR)/platform/sdl_video.o $(OBJ_DIR)/platform/sdl_audio.o $(OBJ_DIR)/platform/sdl_input.o $(OBJ_DIR)/platform/sdl_file.o $(OBJ_DIR)/platform/sdl_time.o $(OBJ_DIR)/core/event_bus.o $(OBJ_DIR)/core/sim/entity.o $(OBJ_DIR)/core/sim/systems.o
MODERN_RELEASE_OBJS = $(OBJ_RELEASE_DIR)/platform/sdl_video.o $(OBJ_RELEASE_DIR)/platform/sdl_audio.o $(OBJ_RELEASE_DIR)/platform/sdl_input.o $(OBJ_RELEASE_DIR)/platform/sdl_file.o $(OBJ_RELEASE_DIR)/platform/sdl_time.o $(OBJ_RELEASE_DIR)/core/event_bus.o $(OBJ_RELEASE_DIR)/core/sim/entity.o $(OBJ_RELEASE_DIR)/core/sim/systems.o

TEST_OBJS = $(OBJ_DIR)/fd2_decoder_test.o
INTRO_OBJS = $(OBJ_DIR)/fd2_intro.o $(DECODER_OBJS)

# Phase 2: Data-driven system
PHASE2_SRCS = $(SRC_DIR)/core/data/dat_parser.c $(SRC_DIR)/core/mod/loader.c $(SRC_DIR)/core/mod/api.c
PHASE2_OBJS = $(OBJ_DIR)/core/data/dat_parser.o $(OBJ_DIR)/core/mod/loader.o $(OBJ_DIR)/core/mod/api.o
PHASE2_RELEASE_OBJS = $(OBJ_RELEASE_DIR)/core/data/dat_parser.o $(OBJ_RELEASE_DIR)/core/mod/loader.o $(OBJ_RELEASE_DIR)/core/mod/api.o

# New modern architecture test target
MODERN_TEST_SRCS = $(SRC_DIR)/app/modern_test.c
MODERN_TEST_OBJS = $(OBJ_DIR)/app/modern_test.o $(MODERN_OBJS) $(OBJ_DIR)/fd2_input.o $(PHASE2_OBJS)
TARGET_MODERN_TEST = $(BIN_DIR)/fd2_modern_test$(EXE_EXT)

# Phase 4: Plot system
PHASE4_SRCS = $(SRC_DIR)/core/dialog.c $(SRC_DIR)/core/npc.c $(SRC_DIR)/core/event_system.c
PHASE4_OBJS = $(OBJ_DIR)/core/dialog.o $(OBJ_DIR)/core/npc.o $(OBJ_DIR)/core/event_system.o
PHASE4_RELEASE_OBJS = $(OBJ_RELEASE_DIR)/core/dialog.o $(OBJ_RELEASE_DIR)/core/npc.o $(OBJ_RELEASE_DIR)/core/event_system.o

# Phase 2 test target
PHASE2_TEST_SRCS = $(SRC_DIR)/app/phase2_test.c
PHASE2_TEST_OBJS = $(OBJ_DIR)/app/phase2_test.o $(PHASE2_OBJS) $(MODERN_OBJS) $(OBJ_DIR)/fd2_input.o
TARGET_PHASE2_TEST = $(BIN_DIR)/fd2_phase2_test$(EXE_EXT)

# Phase 5: Battle system
PHASE5_SRCS = $(SRC_DIR)/core/battle_system.c
PHASE5_OBJS = $(OBJ_DIR)/core/battle_system.o
PHASE5_RELEASE_OBJS = $(OBJ_RELEASE_DIR)/core/battle_system.o

# Phase 4 test target
PHASE4_TEST_SRCS = $(SRC_DIR)/app/phase4_test.c
PHASE4_TEST_OBJS = $(OBJ_DIR)/app/phase4_test.o $(PHASE4_OBJS)
TARGET_PHASE4_TEST = $(BIN_DIR)/fd2_phase4_test$(EXE_EXT)

# Phase 6: Game framework
PHASE6_SRCS = $(SRC_DIR)/core/game_framework.c
PHASE6_OBJS = $(OBJ_DIR)/core/game_framework.o
PHASE6_RELEASE_OBJS = $(OBJ_RELEASE_DIR)/core/game_framework.o

# Modern app target
MODERN_APP_OBJS = $(OBJ_DIR)/app/app_main.o $(PHASE6_OBJS) $(PHASE5_OBJS) $(PHASE4_OBJS) $(PHASE2_OBJS) $(MODERN_OBJS) $(OBJ_DIR)/fd2_input.o
TARGET_MODERN_APP = $(BIN_DIR)/fd2_modern$(EXE_EXT)

# Phase 5 test target
PHASE5_TEST_SRCS = $(SRC_DIR)/app/phase5_test.c
PHASE5_TEST_OBJS = $(OBJ_DIR)/app/phase5_test.o $(PHASE5_OBJS)
TARGET_PHASE5_TEST = $(BIN_DIR)/fd2_phase5_test$(EXE_EXT)

# Targets
TARGET_GAME   = $(BIN_DIR)/fd2$(EXE_EXT)
TARGET_TEST   = $(BIN_DIR)/fd2_decoder_test$(EXE_EXT)
TARGET_INTRO  = $(BIN_DIR)/fd2_intro$(EXE_EXT)
TARGET_RELEASE = $(BIN_DIR)/fd2_release$(EXE_EXT)

.PHONY: all clean test decoder intro game release modern_test phase2_test phase4_test phase5_test modern_app

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

modern_test: $(TARGET_MODERN_TEST)

phase2_test: $(TARGET_PHASE2_TEST)

phase4_test: $(TARGET_PHASE4_TEST)

phase5_test: $(TARGET_PHASE5_TEST)

modern_app: $(TARGET_MODERN_APP)

# Modern app
$(TARGET_MODERN_APP): $(MODERN_APP_OBJS) | $(BIN_DIR)
	$(CC) $(CFLAGS) -o $@ $^ $(LDFLAGS)

# Phase 5 test
$(TARGET_PHASE5_TEST): $(PHASE5_TEST_OBJS) | $(BIN_DIR)
	$(CC) $(CFLAGS) -o $@ $^ $(LDFLAGS)

# Phase 4 test
$(TARGET_PHASE4_TEST): $(PHASE4_TEST_OBJS) | $(BIN_DIR)
	$(CC) $(CFLAGS) -o $@ $^ $(LDFLAGS)

# Phase 2 test
$(TARGET_PHASE2_TEST): $(PHASE2_TEST_OBJS) | $(BIN_DIR)
	$(CC) $(CFLAGS) -o $@ $^ $(LDFLAGS)

# Modern architecture test
$(TARGET_MODERN_TEST): $(MODERN_TEST_OBJS) | $(BIN_DIR)
	$(CC) $(CFLAGS) -o $@ $^ $(LDFLAGS)

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

# Subdirectory compilation rules (debug)
$(OBJ_DIR)/platform/%.o: $(SRC_DIR)/platform/%.c | $(OBJ_DIR)/platform
	@echo Compiling $<
	$(CC) $(CFLAGS) -c $< -o $@

$(OBJ_DIR)/core/%.o: $(SRC_DIR)/core/%.c | $(OBJ_DIR)/core
	@echo Compiling $<
	$(CC) $(CFLAGS) -c $< -o $@

$(OBJ_DIR)/core/sim/%.o: $(SRC_DIR)/core/sim/%.c | $(OBJ_DIR)/core/sim
	@echo Compiling $<
	$(CC) $(CFLAGS) -c $< -o $@

$(OBJ_DIR)/core/data/%.o: $(SRC_DIR)/core/data/%.c | $(OBJ_DIR)/core/data
	@echo Compiling $<
	$(CC) $(CFLAGS) -c $< -o $@

$(OBJ_DIR)/core/script/%.o: $(SRC_DIR)/core/script/%.c | $(OBJ_DIR)/core/script
	@echo Compiling $<
	$(CC) $(CFLAGS) -c $< -o $@

$(OBJ_DIR)/core/mod/%.o: $(SRC_DIR)/core/mod/%.c | $(OBJ_DIR)/core/mod
	@echo Compiling $<
	$(CC) $(CFLAGS) -c $< -o $@

$(OBJ_DIR)/render/%.o: $(SRC_DIR)/render/%.c | $(OBJ_DIR)/render
	@echo Compiling $<
	$(CC) $(CFLAGS) -c $< -o $@

$(OBJ_DIR)/app/%.o: $(SRC_DIR)/app/%.c | $(OBJ_DIR)/app
	@echo Compiling $<
	$(CC) $(CFLAGS) -c $< -o $@

# Subdirectory compilation rules (release)
$(OBJ_RELEASE_DIR)/platform/%.o: $(SRC_DIR)/platform/%.c | $(OBJ_RELEASE_DIR)/platform
	@echo Compiling $< (release)
	$(CC) $(RELEASE_CFLAGS) -c $< -o $@

$(OBJ_RELEASE_DIR)/core/%.o: $(SRC_DIR)/core/%.c | $(OBJ_RELEASE_DIR)/core
	@echo Compiling $< (release)
	$(CC) $(RELEASE_CFLAGS) -c $< -o $@

$(OBJ_RELEASE_DIR)/core/sim/%.o: $(SRC_DIR)/core/sim/%.c | $(OBJ_RELEASE_DIR)/core/sim
	@echo Compiling $< (release)
	$(CC) $(RELEASE_CFLAGS) -c $< -o $@

$(OBJ_RELEASE_DIR)/app/%.o: $(SRC_DIR)/app/%.c | $(OBJ_RELEASE_DIR)/app
	@echo Compiling $< (release)
	$(CC) $(RELEASE_CFLAGS) -c $< -o $@

# Compilation rules (release)
$(OBJ_RELEASE_DIR)/%.o: $(SRC_DIR)/%.c | $(OBJ_RELEASE_DIR)
	@echo Compiling $< (release)
	$(CC) $(RELEASE_CFLAGS) -c $< -o $@

$(BIN_DIR):
	$(MKDIR) -p $@

$(OBJ_DIR):
	$(MKDIR) -p $@

$(OBJ_DIR)/platform:
	$(MKDIR) -p $@

$(OBJ_DIR)/core:
	$(MKDIR) -p $@

$(OBJ_DIR)/core/sim:
	$(MKDIR) -p $@

$(OBJ_DIR)/core/data:
	$(MKDIR) -p $@

$(OBJ_DIR)/core/script:
	$(MKDIR) -p $@

$(OBJ_DIR)/core/mod:
	$(MKDIR) -p $@

$(OBJ_DIR)/render:
	$(MKDIR) -p $@

$(OBJ_DIR)/app:
	$(MKDIR) -p $@

$(OBJ_RELEASE_DIR):
	$(MKDIR) -p $@

$(OBJ_RELEASE_DIR)/platform:
	$(MKDIR) -p $@

$(OBJ_RELEASE_DIR)/core:
	$(MKDIR) -p $@

$(OBJ_RELEASE_DIR)/core/sim:
	$(MKDIR) -p $@

$(OBJ_RELEASE_DIR)/app:
	$(MKDIR) -p $@

clean:
	$(RM) -rf $(OBJ_DIR) $(OBJ_RELEASE_DIR) $(BIN_DIR)
