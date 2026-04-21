# Project knowledge

This file gives Codebuff context about your project: goals, commands, conventions, and gotchas.

## Quickstart
- **Setup**: No package manager — uses `gcc` + locally bundled SDL2 in `sdl2_install/`. No `./configure` or `cmake`.
- **Build**: `make` (builds all targets), `make game` (main game only), `make intro` (intro player), `make decoder` (decoder test)
- **Run game**: `bin/fd2 [data_dir]` — default data_dir is `game/`
- **Test**: `make test` — builds and runs `bin/fd2_decoder_test` (no SDL required)
- **Clean**: `make clean`

## Architecture

FD2 is a **deterministic reimplementation** of Flame Dragon  2 (炎龙骑士团2), a 1993 DOS fighting game. The goal is NOT a modern remake — it must reproduce the DOS build's behavior exactly, then wrap that core in a platform layer (SDL2).

### Key directories
- `src/` — C source: game engine, decoder, renderer, audio, input, AFM animation player
- `include/` — C headers; `include/SDL2/` has the bundled SDL2 headers
- `game/` — Original DOS data files (DAT, MDI, DIG, etc.) needed at runtime
- `bin/` — Build output; also contains runtime data copies and configs
- `sdl2_install/` — Locally built SDL2 libraries (linked via rpath)
- `tools/` — Python scripts for reverse-engineering, extraction, and analysis
- `docs/` — Reverse-engineering notes (DAT formats, AFM format, port architecture)
- `tools/export-for-ai/` — IDA decompiled C fragments and memory dumps from FD2.EXE
- `output/` — Generated extraction results (images, resource maps, metadata)

### Data flow
1. `fd2_dat_load()` maps a DAT file into memory and parses the LLLLLL-header + offset table
2. `fd2_dat_get_resource()` returns a pointer to a specific resource by index
3. Resources are classified (RLE image, palette, raw, nested DAT) via `fd2_resource_classify()`
4. RLE images decompressed via `fd2_rle_decompress()` (IDA sub_4E98D algorithm)
5. AFM animations (ANI.DAT) decoded via `fd2_afm_*` API (frame-by-frame command dispatch)
6. Game state machine: INIT → INTRO → MENU → CHAR_SELECT → BATTLE → VICTORY → ...

### Core source files
| File | Purpose |
|------|---------|
| `src/main.c` | Entry point, creates `fd2_game_t`, runs game loop |
| `src/fd2_game.c` | State machine (enter/update/exit per state) |
| `src/fd2_decoder.c` | DAT loading, RLE decompression, palette, resource classification |
| `src/fd2_afm.c` | AFM animation decoder (ANI.DAT playback) |
| `src/fd2_render.c` | SDL2 rendering pipeline |
| `src/fd2_input.c` | Input handling (keyboard → game actions) |
| `src/fd2_audio.c` | Audio system (Miles AIL / SDL audio) |
| `src/fd2_resources.c` | Resource manager (loads all DAT files) |
| `src/fd2_rle.c` | Standalone RLE helpers |
| `src/fd2_intro.c` | Legacy intro player |
| `src/fd2_decoder_test.c` | Standalone decoder test (no SDL) |

## Conventions

- **Language**: C99 (`-std=gnu99`), no C++. All game code is C.
- **Compiler flags**: `-Wall -Wextra -O2 -Iinclude -Isdl2_install/include/SDL2`
- **Linker**: `-Lsdl2_install/lib -Wl,-rpath,'$$ORIGIN/../sdl2_install/lib' -lSDL2 -lm`
- **Naming**: `fd2_` prefix for public API (e.g., `fd2_dat_load`, `fd2_rle_decompress`). `fd_` prefix for some older internal helpers.
- **Types**: Project defines its own `u8/u16/u32/s8/s16/s32` in `fd2_decoder.h`; older headers also define `byte/word/dword` — prefer the `u8/u16/u32` variants.
- **No dynamic dependencies beyond SDL2**: SDL2 is statically bundled in `sdl2_install/`. The rpath makes the binary find it relative to its own location.
- **Game data must be present**: The `game/` (or `bin/`) directory must contain all original DAT files (FDOTHER.DAT, ANI.DAT, FDSHAP.DAT, etc.) for the game to run.
- **Python tools**: Analysis/extraction scripts in `tools/` are Python 3. They are NOT part of the build — they are for reverse-engineering workflows.
- **Chinese-language docs**: Several docs are written in Chinese (逆向工程 notes). Key technical terms are given in both languages.

## Key DAT file formats

All DAT files share a common container format:
- 6 bytes: magic `"LLLLLL"`
- 4 bytes: resource count (little-endian u32)
- N×4 bytes: offset table (one u32 per resource)
- Resources can be: RLE-compressed images, 768-byte palettes, raw data, or nested DATs

### RLE algorithm (sub_4E98D)
Control byte top 2 bits determine mode:
- `11`: skip (transparent) — count pixels skipped
- `10`: copy — count bytes from source
- `01`: fill — repeat next byte count times
- `00`: sparse fill — write at every 2nd position

Count = `(value & 0x3F) + 1`

### AFM animation format (ANI.DAT)
- 173-byte header with frame count at offset 0xA5
- Each frame: 8-byte header (2B size + 2B param + 4B reserved) + frame data
- Frame dispatch via command bytes (0x00–0x09) to different decode functions
- Different RLE variant: `if (byte & 0xC0) == 0xC0` → RLE run, else literal

## Gotchas

- **Two different RLE algorithms**: `fd2_rle_decompress` (sub_4E98D, for DAT image resources) vs `fd2_afm_rle_decode` (for AFM animation frames). Do not confuse them.
- **6-bit vs 8-bit palette**: DOS VGA uses 6-bit values (0–63). Must convert to 8-bit via `(v6 << 2) | (v6 >> 4)` before rendering with SDL2.
- **Duplicate type definitions**: `byte/word/dword` in `fd2_types.h` and `fd2_reimpl.h`; `u8/u16/u32` in `fd2_decoder.h`. Prefer the decoder types for new code.
- **`fd2_reimpl.h` is legacy**: It defines an older `GameState` struct and a flat function API. The current codebase uses `fd2_game_t` (from `fd2_game.h`) instead. Don't add new code to `fd2_reimpl.h`.
- **SDL2 is not in system paths**: It's in `sdl2_install/`. The Makefile handles this, but if you add new build targets you must use the same `-I` and `-L` flags.
- **Original DOS data is required**: The game cannot run without the original DAT files from the DOS distribution. These are in `game/` and `bin/`.
- **Intro animation timing**: The original plays 535 frames at 30ms each (16.05 seconds total), with sound/video effects triggered at specific frame numbers (10, 25, 110, 210, 330, 450).
