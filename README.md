# FD2 — Flame Dragon 2 Reimplementation

A deterministic, from-scratch reimplementation of **Flame Dragon 2 (炎龙骑士团2)**, a 1993 DOS fighting/tactical game. The goal is to reproduce the original DOS build's behavior exactly, then wrap that core in a portable SDL2 platform layer.

> This project is **not** a modern remake — it aims to match the original DOS behavior bit-for-bit, then play it back through SDL2.

## Quickstart

No package manager is used. The build relies on `gcc` plus a locally bundled SDL2 in `sdl2_install/`.

```bash
make            # build all targets and copy data files
make game       # build the main game only
make release    # build a release (no console window) binary
make test       # build & run the standalone decoder test (no SDL required)
make clean      # remove build artifacts
```

### Run

```bash
bin/fd2 [data_dir]    # default data_dir is game/
```

The original DOS data files (DAT, MDI, DIG, etc.) must be present in `game/` (or the directory passed as `data_dir`) for the game to run.

## Architecture

FD2 reconstructs the original game as a state machine driven by the original data files:

```
DAT container ─▶ resource classification ─▶ RLE decode ─▶ renderer / AFM player
```

1. `fd2_dat_load()` maps a DAT file and parses its `LLLLLL` magic header + offset table.
2. `fd2_dat_get_resource()` returns a pointer to a resource by index.
3. Resources are classified (RLE image, palette, raw, nested DAT) via `fd2_resource_classify()`.
4. RLE images are decoded by `fd2_rle_decompress()` (IDA `sub_4E98D`).
5. AFM animations (`ANI.DAT`) are decoded frame-by-frame via the `fd2_afm_*` API.
6. Game state machine: `INIT → INTRO → MENU → CHAR_SELECT → BATTLE → VICTORY → …`

### Key directories

| Path | Purpose |
|------|---------|
| `src/` | C source: engine, decoder, renderer, audio, input, AFM player |
| `include/` | C headers (`include/SDL2/` holds bundled SDL2 headers) |
| `game/` | Original DOS data files required at runtime |
| `bin/` | Build output, runtime data copies, configs |
| `sdl2_install/` | Locally built SDL2 libraries (linked via rpath) |
| `tools/` | Python reverse-engineering / extraction scripts |
| `docs/` | Reverse-engineering notes (DAT, AFM, port architecture) |
| `output/` | Generated extraction results |

### Core source files

| File | Purpose |
|------|---------|
| `src/main.c` | Entry point; creates `fd2_game_t`, runs game loop |
| `src/fd2_game.c` / `fd2_states*.c` | State machine (enter/update/exit per state) |
| `src/fd2_decoder.c` | DAT loading, RLE decompression, palette, classification |
| `src/fd2_afm.c` | AFM animation decoder (`ANI.DAT` playback) |
| `src/fd2_render.c` | SDL2 rendering pipeline |
| `src/fd2_input.c` | Input handling (keyboard → game actions) |
| `src/fd2_audio.c` | Audio system (Miles AIL / SDL audio) |
| `src/fd2_resources.c` | Resource manager (loads all DAT files) |
| `src/fd2_rle.c` | Standalone RLE helpers |
| `src/fd2_decoder_test.c` | Standalone decoder test (no SDL) |

## Conventions

- **Language**: C99 (`-std=gnu99`), no C++.
- **Flags**: `-Wall -Wextra -O2 -Iinclude -Isdl2_install/include/SDL2`
- **Linker**: `-Lsdl2_install/lib -Wl,-rpath,'$$ORIGIN/../sdl2_install/lib' -lSDL2 -lm`
- **Naming**: `fd2_` prefix for public API. Prefer `u8/u16/u32` types from `fd2_decoder.h`.
- **Dependencies**: Only SDL2, statically bundled in `sdl2_install/` (resolved via rpath).
- **Python tools** in `tools/` are for reverse-engineering workflows and are not part of the build.

## DAT file formats

All DAT files share a common container:

- 6 bytes: magic `"LLLLLL"`
- 4 bytes: resource count (little-endian `u32`)
- N×4 bytes: offset table (one `u32` per resource)

Resources may be RLE-compressed images, 768-byte palettes, raw data, or nested DATs.

### RLE algorithm (`sub_4E98D`)

Control byte top 2 bits select the mode; count = `(value & 0x3F) + 1`:

- `11` — skip (transparent)
- `10` — copy from source
- `01` — fill (repeat next byte)
- `00` — sparse fill (write every 2nd position)

> Note: there are **two** RLE algorithms — `fd2_rle_decompress` (DAT images) and `fd2_afm_rle_decode` (AFM frames). Do not confuse them.

### AFM animation format (`ANI.DAT`)

- 173-byte header; frame count at offset `0xA5`
- Each frame: 8-byte header + frame data; dispatch via command bytes `0x00`–`0x09`
- RLE variant: `if (byte & 0xC0) == 0xC0` → RLE run, else literal

## Gotchas

- **6-bit vs 8-bit palette**: DOS VGA uses 6-bit values (0–63). Convert to 8-bit via `(v6 << 2) | (v6 >> 4)` before rendering.
- **Duplicate type definitions**: `byte/word/dword` in `fd2_types.h`/`fd2_reimpl.h` vs `u8/u16/u32` in `fd2_decoder.h`. Prefer the decoder types.
- **`fd2_reimpl.h` is legacy**: use `fd2_game_t` from `fd2_game.h` for new code.
- **SDL2 is local**: add the same `-I`/`-L` flags if you introduce new build targets.
- **Original data is required**: the game cannot run without the original DAT files.
- **Intro timing**: the original plays 535 frames at 30 ms each (≈16.05 s), with effects at frames 10, 25, 110, 210, 330, 450.

## License

See individual files for licensing of reimplemented code. Original DOS game data is property of its respective rights holders and is not included.
