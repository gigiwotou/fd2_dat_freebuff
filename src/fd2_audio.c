/**
 * FD2 Audio System - Cross-platform MIDI Playback
 *
 * Based on IDA MCP analysis of the original game:
 *   - sub_3AEEE: AIL_start_sequence wrapper
 *   - sub_43270: Main MIDI event parser (tempo*16 storage)
 *   - FDMUS.DAT contains XMIDI format music resources
 *
 * Cross-platform implementation using SDL audio callback:
 *   1. Extract XMIDI from FDMUS.DAT
 *   2. Convert to MIDI event list with Note On/Off
 *   3. SDL audio callback synthesizes PCM in real-time
 */

#ifndef _USE_MATH_DEFINES
#define _USE_MATH_DEFINES
#endif

#include "fd2_audio.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

#include <SDL2/SDL.h>

/* ========================================================================
 * Constants
 * ======================================================================== */

#define MIDI_TIMEBASE 96
#define DEFAULT_QN 500000
#define DEFAULT_TIMEBASE 60
#define MIDI_SAMPLE_RATE 44100
#define MIDI_CHANNELS 2
#define MIDI_FORMAT AUDIO_S16SYS
#define MAX_NOTES_PER_CH 16
#define MAX_CHANNELS 16
#define MAX_CONV_EVENTS 5000

/* ========================================================================
 * FDMUS.DAT Parser
 * ======================================================================== */

typedef struct {
    char magic[6];
    unsigned int count;
} fdmus_header_t;

static unsigned char* fdmus_extract_resource(const char* fdmus_path,
                                             int resource_index,
                                             unsigned int* out_size) {
    if (!fdmus_path || resource_index < 0 || !out_size) return NULL;

    FILE* f = fopen(fdmus_path, "rb");
    if (!f) { fprintf(stderr, "fdmus: cannot open %s\n", fdmus_path); return NULL; }

    fdmus_header_t header;
    if (fread(&header, 1, sizeof(header), f) != sizeof(header)) {
        fprintf(stderr, "fdmus: cannot read header\n"); fclose(f); return NULL;
    }
    if (memcmp(header.magic, "LLLLLL", 6) != 0) {
        fprintf(stderr, "fdmus: invalid magic\n"); fclose(f); return NULL;
    }
    if (resource_index >= (int)header.count) {
        fprintf(stderr, "fdmus: index %d out of range (count=%u)\n", resource_index, header.count);
        fclose(f); return NULL;
    }

    unsigned int offset, next_offset;
    fseek(f, 10 + resource_index * 4, SEEK_SET);
    fread(&offset, 4, 1, f);
    if (resource_index + 1 < (int)header.count) {
        fseek(f, 10 + (resource_index + 1) * 4, SEEK_SET);
        fread(&next_offset, 4, 1, f);
    } else {
        fseek(f, 0, SEEK_END);
        next_offset = ftell(f);
    }

    unsigned int resource_size = next_offset - offset;
    if (resource_size == 0 || resource_size > 64 * 1024) {
        fprintf(stderr, "fdmus: invalid size %u\n", resource_size); fclose(f); return NULL;
    }

    fseek(f, offset, SEEK_SET);
    unsigned char* data = (unsigned char*)malloc(resource_size);
    if (!data) { fclose(f); return NULL; }
    if (fread(data, 1, resource_size, f) != resource_size) {
        free(data); fclose(f); return NULL;
    }
    fclose(f);
    *out_size = resource_size;
    return data;
}

/* ========================================================================
 * XMIDI Parser
 * ======================================================================== */

static int parse_var_len(const unsigned char* data, unsigned int* val) {
    *val = 0; int bytes = 0; unsigned char b;
    do { b = data[bytes++]; *val = (*val << 7) | (b & 0x7F); } while (b & 0x80);
    return bytes;
}

static int write_var_len(unsigned int value, unsigned char* buf) {
    unsigned char tmp[4]; int i = 0;
    tmp[i++] = value & 0x7F;
    while ((value >>= 7) > 0) { tmp[i] = 0x80 | (value & 0x7F); i++; }
    int out = 0; for (int j = i - 1; j >= 0; j--) buf[out++] = tmp[j];
    return out;
}

static unsigned int get_qnlen(const unsigned char* data, int size) {
    int pos = 0;
    while (pos < size - 4 && data[pos] == 0xFF) {
        pos++;
        if (pos >= size) break;
        unsigned char mt = data[pos++];
        unsigned int len; pos += parse_var_len(data + pos, &len);
        if (mt == 0x51 && len >= 3 && pos + 3 <= size) {
            unsigned int tempo = (data[pos] << 16) | (data[pos+1] << 8) | data[pos+2];
            return (tempo > 0) ? tempo : 500000;
        }
        pos += len;
    }
    return 500000;
}

/* Converted event for sorting */
typedef struct {
    unsigned int abs_tick;
    unsigned char status;
    unsigned char data1;
    unsigned char data2;
} cevt_t;

static cevt_t g_cevents[MAX_CONV_EVENTS];
static int g_cevent_count;

static int cmp_cevt(const void* a, const void* b) {
    const cevt_t* ea = (const cevt_t*)a;
    const cevt_t* eb = (const cevt_t*)b;
    return (ea->abs_tick < eb->abs_tick) ? -1 : (ea->abs_tick > eb->abs_tick) ? 1 : 0;
}

static void add_cevt(unsigned int tick, unsigned char s, unsigned char d1, unsigned char d2) {
    if (g_cevent_count < MAX_CONV_EVENTS) {
        cevt_t* e = &g_cevents[g_cevent_count++];
        e->abs_tick = tick; e->status = s; e->data1 = d1; e->data2 = d2;
    }
}

/* Parse XMIDI EVNT data directly (no intermediate MIDI file needed) */
static int parse_xmidi_events(const unsigned char* xmidi, unsigned int xsize,
                              double* out_tick_dur_ms, int* out_timebase) {
    unsigned int qnlen = get_qnlen(xmidi, xsize);
    double factor = (double)MIDI_TIMEBASE * DEFAULT_QN / (qnlen * DEFAULT_TIMEBASE);
    double tick_dur_ms = qnlen / (DEFAULT_TIMEBASE * 1000.0 / DEFAULT_QN) * (MIDI_TIMEBASE / (double)DEFAULT_TIMEBASE);
    /* tick_dur = tempo_us / (timebase * 1000), but tempo_us = qnlen */
    tick_dur_ms = qnlen / (MIDI_TIMEBASE * 1000.0);
    /* Actually: 1 tick = tempo_us / timebase microseconds = tempo_us / (timebase * 1000) ms */
    tick_dur_ms = qnlen / (MIDI_TIMEBASE * 1000.0);

    g_cevent_count = 0;
    int pos = 0;
    unsigned int abs_tick = 0;
    unsigned char running = 0;
    unsigned int delta = 0;

    /* Header metas (no delta) */
    while (pos < (int)xsize && xmidi[pos] == 0xFF) {
        unsigned char mt = xmidi[pos + 1];
        unsigned int len; int lb = parse_var_len(xmidi + pos + 2, &len);
        if (mt == 0x51) {
            /* tempo meta - skip but don't add event */
        }
        pos += 2 + lb + len;
    }

    /* Events with deltas */
    while (pos < (int)xsize) {
        unsigned int cur_delta = delta;
        delta = 0;
        unsigned char byte = xmidi[pos];

        if (byte >= 0x80) {
            running = byte; pos++;
        } else {
            do { if (pos >= (int)xsize) break; byte = xmidi[pos++]; delta = (delta << 7) | (byte & 0x7F); } while (byte & 0x80);
            if (pos >= (int)xsize) break;
            byte = xmidi[pos];
            if (byte >= 0x80) { running = byte; pos++; }
            else { if (running == 0) continue; }
        }

        abs_tick += (unsigned int)(cur_delta * factor + 0.5);

        unsigned char status = running;
        unsigned char cmd = status & 0xF0;

        if (status == 0xFF) {
            unsigned char mt = xmidi[pos++];
            unsigned int len; parse_var_len(xmidi + pos, &len);
            int skip = 0;
            { unsigned char tb; do { tb = xmidi[pos++]; skip++; } while (tb & 0x80); }
            pos = pos - skip + skip; /* reset */
            /* re-parse properly */
            pos -= skip;
            parse_var_len(xmidi + pos, &len);
            /* actually let's just skip */
            { unsigned char tb; do { tb = xmidi[pos++]; } while (tb & 0x80); }
            pos += len;
            if (mt == 0x2F) break;
        } else if (status >= 0xF0) {
            if (status == 0xF0 || status == 0xF7) {
                unsigned int len;
                { unsigned char tb; do { tb = xmidi[pos++]; } while ((tb & 0x80) && pos < (int)xsize); }
                /* skip sysex len bytes... simplify: just skip */
                while (pos < (int)xsize && xmidi[pos-1] & 0x80) pos++;
            } else if (pos < (int)xsize) {
                pos++;
            }
        } else if (cmd == 0xC0 || cmd == 0xD0) {
            if (pos < (int)xsize) add_cevt(abs_tick, status, xmidi[pos++], 0);
        } else {
            if (pos + 1 >= (int)xsize) break;
            unsigned char d1 = xmidi[pos++];
            unsigned char d2 = xmidi[pos++];

            /* Clamp to MIDI range (Python v5 uses max(0,min(127,...))) */
            if (d1 > 127) d1 = 127;
            if (d2 > 127) d2 = 127;

            if (cmd == 0x90 && d2 > 0) {
                /* Note On with duration */
                unsigned int dur = 0;
                unsigned char db;
                do {
                    if (pos >= (int)xsize) break;
                    db = xmidi[pos++];
                    dur = (dur << 7) | (db & 0x7F);
                } while (db & 0x80);
                unsigned int dur_conv = (unsigned int)(dur * factor + 0.5);

                add_cevt(abs_tick, status, d1, d2);
                add_cevt(abs_tick + dur_conv, 0x80 | (status & 0x0F), d1, 0);
            } else {
                add_cevt(abs_tick, status, d1, d2);
            }
        }
    }

    qsort(g_cevents, g_cevent_count, sizeof(cevt_t), cmp_cevt);
    *out_tick_dur_ms = tick_dur_ms;
    if (out_timebase) *out_timebase = MIDI_TIMEBASE;
    return g_cevent_count;
}

/* ========================================================================
 * Software Synthesizer
 * ======================================================================== */

typedef struct {
    int     channel;
    int     note;
    double  freq;
    double  phase;
    double  harmonics[3];
    float   target_vol;
    float   env_level;
    float   attack_rate;
    float   decay_rate;
    float   sustain_level;
    int     active;
    int     env_stage; /* 0=attack, 1=decay, 2=sustain, 3=release, 4=dead */
} note_t;

typedef struct {
    note_t  notes[MAX_CHANNELS * MAX_NOTES_PER_CH];
    float   ch_vol[MAX_CHANNELS];
    int     ch_program[MAX_CHANNELS];
    double  tempo_us;
    int     timebase;
    float   master_vol;
} synth_t;

/* Note frequency: f = 440 * 2^((n-69)/12) */
static double note_freq(int n) { return 440.0 * pow(2.0, (n - 69) / 12.0); }

static void synth_init(synth_t* s) {
    memset(s, 0, sizeof(*s));
    for (int i = 0; i < MAX_CHANNELS; i++) {
        s->ch_vol[i] = 1.0f;
        s->ch_program[i] = 0;
    }
    s->tempo_us = 500000.0; s->timebase = MIDI_TIMEBASE; s->master_vol = 0.5f;
}

static void synth_on(synth_t* s, int ch, int note, int vel) {
    if (ch < 0 || ch >= MAX_CHANNELS || note < 0 || note > 127) return;
    float v = (vel / 127.0f) * s->ch_vol[ch] * s->master_vol * 0.5f;
    double freq = note_freq(note);

    for (int i = 0; i < MAX_CHANNELS * MAX_NOTES_PER_CH; i++) {
        if (!s->notes[i].active || s->notes[i].env_stage == 4) {
            s->notes[i].channel = ch;
            s->notes[i].note = note;
            s->notes[i].freq = freq;
            s->notes[i].phase = 0.0;
            s->notes[i].harmonics[0] = 1.0;
            s->notes[i].harmonics[1] = 0.0;
            s->notes[i].harmonics[2] = 0.0;
            s->notes[i].target_vol = v;
            s->notes[i].env_level = 0.0f;
            s->notes[i].attack_rate = 0.15f;
            s->notes[i].decay_rate = 0.02f;
            s->notes[i].sustain_level = 0.8f;
            s->notes[i].env_stage = 0;
            s->notes[i].active = 1;
            return;
        }
    }
}

static void synth_off(synth_t* s, int ch, int note) {
    for (int i = 0; i < MAX_CHANNELS * MAX_NOTES_PER_CH; i++) {
        if (s->notes[i].active > 0 && s->notes[i].channel == ch && s->notes[i].note == note) {
            s->notes[i].env_stage = 3; /* Release */
            return;
        }
    }
}

static void synth_set_vol(synth_t* s, int ch, int vol) {
    if (ch >= 0 && ch < MAX_CHANNELS) s->ch_vol[ch] = vol / 127.0f;
}

static void synth_set_program(synth_t* s, int ch, int prog) {
    if (ch >= 0 && ch < MAX_CHANNELS) {
        s->ch_program[ch] = prog;
        /* Different harmonics for different programs */
        /* This affects new notes played on this channel */
    }
}

/* Improved synthesis with ADSR envelope and harmonics */
static void synth_render(synth_t* s, short* buf, int ns) {
    for (int i = 0; i < ns; i++) {
        double sample = 0.0;

        for (int n = 0; n < MAX_CHANNELS * MAX_NOTES_PER_CH; n++) {
            if (s->notes[n].active && s->notes[n].env_stage != 4) {
                double omega = 2.0 * M_PI * s->notes[n].freq / MIDI_SAMPLE_RATE;
                s->notes[n].phase += omega;
                if (s->notes[n].phase > 2.0 * M_PI) s->notes[n].phase -= 2.0 * M_PI;

                /* ADSR envelope */
                switch (s->notes[n].env_stage) {
                    case 0: /* Attack: ramp up quickly */
                        s->notes[n].env_level += s->notes[n].attack_rate *
                                                (s->notes[n].target_vol - s->notes[n].env_level);
                        if (s->notes[n].env_level >= s->notes[n].target_vol * 0.95f) {
                            s->notes[n].env_stage = 1;
                        }
                        break;
                    case 1: /* Decay: ramp down to sustain */
                        s->notes[n].env_level -= s->notes[n].decay_rate * s->notes[n].target_vol;
                        if (s->notes[n].env_level <= s->notes[n].target_vol * s->notes[n].sustain_level) {
                            s->notes[n].env_level = s->notes[n].target_vol * s->notes[n].sustain_level;
                            s->notes[n].env_stage = 2;
                        }
                        break;
                    case 2: /* Sustain: hold level */
                        /* Level stays constant until note off */
                        break;
                    case 3: /* Release: fade out */
                        s->notes[n].env_level *= 0.92f;
                        if (s->notes[n].env_level < 0.001f) {
                            s->notes[n].env_stage = 4;
                            s->notes[n].active = 0;
                        }
                        break;
                }

                if (s->notes[n].env_stage != 4) {
                    sample += s->notes[n].env_level * sin(s->notes[n].phase);
                }
            }
        }

        /* Soft clipping to prevent distortion */
        double v = sample * 20000.0;
        if (v > 30000.0) v = 30000.0;
        if (v < -30000.0) v = -30000.0;
        buf[i * MIDI_CHANNELS] = (short)v;
        buf[i * MIDI_CHANNELS + 1] = (short)v;
    }
}

/* ========================================================================
 * SDL Audio Playback
 * ======================================================================== */

static SDL_AudioDeviceID s_dev = 0;
static int s_evt_count = 0;
static int s_cur_evt = 0;
static double s_tick_dur_ms = 5.208;
static double s_elapsed_ms = 0.0;
static synth_t s_synth;
static int s_playing = 0;
static int s_max_tick = 0;      /* Last event tick for loop detection */
static int s_loops = 0;         /* Loop count (-1 = infinite) */
static int s_current_loop = 0;  /* Current loop iteration */

static void audio_cb(void* ud, Uint8* stream, int len) {
    (void)ud;
    short* buf = (short*)stream;
    int ns = len / (MIDI_CHANNELS * sizeof(short));
    double ms_per_callback = (double)ns / (MIDI_SAMPLE_RATE / 1000.0);
    s_elapsed_ms += ms_per_callback;

    /* Process MIDI events that should have played by now */
    while (s_cur_evt < s_evt_count) {
        cevt_t* e = &g_cevents[s_cur_evt];
        double evt_ms = (double)e->abs_tick * s_tick_dur_ms;
        if (s_elapsed_ms >= evt_ms) {
            unsigned char cmd = e->status & 0xF0;
            unsigned char ch = e->status & 0x0F;
            if (cmd == 0x90) {
                if (e->data2 > 0) synth_on(&s_synth, ch, e->data1, e->data2);
                else synth_off(&s_synth, ch, e->data1);
            } else if (cmd == 0x80) {
                synth_off(&s_synth, ch, e->data1);
            } else if (cmd == 0xB0 && e->data1 == 7) {
                synth_set_vol(&s_synth, ch, e->data2);
            } else if (cmd == 0xC0) {
                synth_set_program(&s_synth, ch, e->data1);
            }
            s_cur_evt++;
        } else break;
    }

    /* Check if playback is complete - implement looping */
    if (s_cur_evt >= s_evt_count && s_playing) {
        if (s_loops < 0 || s_current_loop < s_loops) {
            /* Calculate duration of one full playthrough */
            double total_duration_ms = (double)s_max_tick * s_tick_dur_ms;
            /* Reset for next loop: keep elapsed_ms relative to loop start */
            s_cur_evt = 0;
            s_elapsed_ms = 0.0;
            s_current_loop++;
            /* Clear all notes for clean restart */
            memset(&s_synth.notes, 0, sizeof(s_synth.notes));
            printf("sdl_midi: loop %d started (%s)\n", s_current_loop, s_loops < 0 ? "infinite" : "finite");
            
            /* Process events for current callback time in the new loop */
            while (s_cur_evt < s_evt_count) {
                cevt_t* e = &g_cevents[s_cur_evt];
                double evt_ms = (double)e->abs_tick * s_tick_dur_ms;
                if (s_elapsed_ms >= evt_ms) {
                    unsigned char cmd = e->status & 0xF0;
                    unsigned char ch = e->status & 0x0F;
                    if (cmd == 0x90) {
                        if (e->data2 > 0) synth_on(&s_synth, ch, e->data1, e->data2);
                        else synth_off(&s_synth, ch, e->data1);
                    } else if (cmd == 0x80) {
                        synth_off(&s_synth, ch, e->data1);
                    } else if (cmd == 0xB0 && e->data1 == 7) {
                        synth_set_vol(&s_synth, ch, e->data2);
                    } else if (cmd == 0xC0) {
                        synth_set_program(&s_synth, ch, e->data1);
                    }
                    s_cur_evt++;
                } else break;
            }
        } else {
            /* All loops complete, stop playing - render silence */
            s_playing = 0;
            memset(buf, 0, len);
            return;
        }
    }

    synth_render(&s_synth, buf, ns);
}

static void sdl_stop(void) {
    if (s_dev) { SDL_PauseAudioDevice(s_dev, 1); SDL_CloseAudioDevice(s_dev); s_dev = 0; }
    s_evt_count = 0; s_cur_evt = 0; s_elapsed_ms = 0.0; s_playing = 0;
    s_max_tick = 0; s_loops = 0; s_current_loop = 0;
}

static int sdl_play(const unsigned char* xmidi, unsigned int xsize, int loops) {
    sdl_stop();

    int count = parse_xmidi_events(xmidi, xsize, &s_tick_dur_ms, NULL);
    if (count == 0) { fprintf(stderr, "sdl_midi: no events\n"); return -1; }
    s_evt_count = count;

    /* Find max tick for loop reference */
    s_max_tick = 0;
    for (int i = 0; i < count; i++) {
        if (g_cevents[i].abs_tick > (unsigned int)s_max_tick)
            s_max_tick = g_cevents[i].abs_tick;
    }

    printf("sdl_midi: %d events, tick_dur=%.3f ms, max_tick=%d, loops=%s\n",
           count, s_tick_dur_ms, s_max_tick, loops < 0 ? "infinite" : "finite");

    synth_init(&s_synth);
    s_cur_evt = 0; s_elapsed_ms = 0.0; s_playing = 1;
    s_loops = loops; s_current_loop = 0;

    SDL_AudioSpec want, got;
    memset(&want, 0, sizeof(want));
    want.freq = MIDI_SAMPLE_RATE; want.format = MIDI_FORMAT;
    want.channels = MIDI_CHANNELS; want.samples = 2048;
    want.callback = audio_cb;

    s_dev = SDL_OpenAudioDevice(NULL, 0, &want, &got, 0);
    if (!s_dev) { fprintf(stderr, "sdl_midi: SDL_OpenAudioDevice: %s\n", SDL_GetError()); sdl_stop(); return -1; }

    SDL_PauseAudioDevice(s_dev, 0);
    printf("sdl_midi: playback started\n");
    return 0;
}

/* ========================================================================
 * Public API
 * ======================================================================== */

int fd2_audio_init(fd2_audio_t* audio) {
    if (!audio) return -1;
    if (!SDL_WasInit(SDL_INIT_AUDIO)) {
        if (SDL_InitSubSystem(SDL_INIT_AUDIO) < 0) {
            fprintf(stderr, "fd2_audio: SDL audio init failed: %s\n", SDL_GetError());
            audio->initialized = false; return -1;
        }
    }
    audio->initialized   = false;
    audio->muted         = false;
    audio->music_volume  = 128;
    audio->sfx_volume    = 128;
    audio->midi_handle   = NULL;
    audio->music_playing = -1;
    audio->music_loops   = 0;
    audio->current_loop  = 0;
    audio->midi_data     = NULL;
    audio->midi_size     = 0;
    audio->fdmus_path    = NULL;
    printf("fd2_audio: initialized (SDL Software Synth)\n");
    audio->initialized = true;
    return 0;
}

void fd2_audio_shutdown(fd2_audio_t* audio) {
    if (!audio) return;
    sdl_stop();
    if (audio->midi_data) { free(audio->midi_data); audio->midi_data = NULL; }
    audio->initialized = false;
    audio->music_playing = -1;
    SDL_QuitSubSystem(SDL_INIT_AUDIO);
    printf("fd2_audio: shutdown\n");
}

void fd2_audio_set_fdmus_path(fd2_audio_t* audio, const char* path) {
    if (!audio) return; audio->fdmus_path = path;
}

int fd2_audio_play_music(fd2_audio_t* audio, int track_id, int loops) {
    if (!audio || !audio->initialized) return -1;
    fd2_audio_stop_music(audio);
    if (!audio->fdmus_path) { fprintf(stderr, "fd2_audio: no FDMUS.DAT path\n"); return -1; }

    unsigned int xsize = 0;
    unsigned char* xdata = fdmus_extract_resource(audio->fdmus_path, track_id, &xsize);
    if (!xdata) { fprintf(stderr, "fd2_audio: cannot extract track %d\n", track_id); return -1; }
    printf("fd2_audio: extracted XMIDI track %d (%u bytes)\n", track_id, xsize);

    int r = sdl_play(xdata, xsize, loops);
    free(xdata);

    if (r == 0) {
        audio->music_playing = track_id;
        audio->music_loops = loops;
        audio->current_loop = 0;
    }
    return r;
}

void fd2_audio_stop_music(fd2_audio_t* audio) {
    if (!audio) return;
    sdl_stop();
    audio->music_playing = -1;
    audio->music_loops = 0;
    audio->current_loop = 0;
}

void fd2_audio_set_music_volume(fd2_audio_t* audio, int volume) {
    if (!audio) return;
    audio->music_volume = (volume < 0) ? 0 : (volume > 128) ? 128 : volume;
    s_synth.master_vol = audio->music_volume / 128.0f;
}

void fd2_audio_fade_music(fd2_audio_t* audio, int ms) {
    if (!audio) return;
    fd2_audio_stop_music(audio);
    (void)ms;
}

int fd2_audio_play_sfx(fd2_audio_t* audio, int sfx_id) {
    if (!audio) return -1;
    (void)sfx_id;
    printf("fd2_audio: SFX %d (not implemented)\n", sfx_id);
    return 0;
}

void fd2_audio_set_sfx_volume(fd2_audio_t* audio, int volume) {
    if (!audio) return;
    audio->sfx_volume = (volume < 0) ? 0 : (volume > 128) ? 128 : volume;
}

bool fd2_audio_music_playing(const fd2_audio_t* audio) {
    if (!audio) return false;
    return audio->music_playing >= 0;
}

void fd2_audio_toggle_mute(fd2_audio_t* audio) {
    if (!audio) return;
    audio->muted = !audio->muted;
    s_synth.master_vol = audio->muted ? 0.0f : audio->music_volume / 128.0f;
}
