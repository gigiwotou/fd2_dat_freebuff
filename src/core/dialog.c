/**
 * Dialog System Implementation
 * Based on IDA sub_15F84 - Dialog display system.
 * Loads text from FDTXT.DAT and renders dialog UI.
 */

#define _GNU_SOURCE
#include "fd2/dialog.h"
#include <stdlib.h>
#include <string.h>
#include <stdio.h>

/* FDTXT.DAT text encoding: GB2312-like, simple ASCII subset */
static int decode_txt_char(const u8* src, char* out, int* out_len) {
    if (src[0] < 0x80) {
        *out = (char)src[0];
        *out_len = 1;
        return 1;
    } else if (src[0] >= 0xA1 && src[0] <= 0xF7 && src[1] >= 0xA1) {
        /* GB2312 character */
        out[0] = (char)src[0];
        out[1] = (char)src[1];
        out[2] = '\0';
        *out_len = 2;
        return 2;
    }
    *out = '?';
    *out_len = 1;
    return 1;
}

int fd2_dialog_init(fd2_dialog_box_t* box) {
    if (!box) return -1;

    memset(box, 0, sizeof(*box));
    box->entries = NULL;
    box->entry_count = 0;
    box->current_entry = -1;
    box->char_index = 0;
    box->type_timer = 0;
    box->typing = false;
    box->waiting_for_input = false;

    /* Default dialog box position: bottom of screen */
    box->display_x = 10;
    box->display_y = 140;
    box->display_w = 300;
    box->display_h = 50;
    box->text_color = 255;  /* White */
    box->bg_color = 0;      /* Black */
    box->border_color = 60; /* Gray */

    return 0;
}

void fd2_dialog_shutdown(fd2_dialog_box_t* box) {
    if (!box) return;
    if (box->entries) {
        free(box->entries);
        box->entries = NULL;
    }
    box->entry_count = 0;
}

int fd2_dialog_load_from_dat(fd2_dialog_box_t* box, const u8* txt_data, u32 txt_size) {
    if (!box || !txt_data || txt_size < 4) return -1;

    /* FDTXT.DAT format: RLE compressed text entries */
    /* Simple parsing: count entries by looking for delimiters */
    int max_entries = 256;
    box->entries = (fd2_dialog_entry_t*)calloc(max_entries, sizeof(fd2_dialog_entry_t));
    if (!box->entries) return -1;

    /* Parse text entries - simple newline-separated format */
    int entry_idx = 0;
    int char_idx = 0;
    const u8* ptr = txt_data;
    const u8* end = txt_data + txt_size;

    while (ptr < end && entry_idx < max_entries) {
        if (*ptr == 0x0A || *ptr == 0x0D) {
            /* Newline - end of entry */
            box->entries[entry_idx].text[char_idx] = '\0';
            if (char_idx > 0) {
                entry_idx++;
                char_idx = 0;
            }
            ptr++;
            continue;
        }

        if (*ptr == 0x00) {
            /* Null terminator */
            box->entries[entry_idx].text[char_idx] = '\0';
            if (char_idx > 0) {
                entry_idx++;
            }
            break;
        }

        /* Decode character */
        char decoded[4];
        int decoded_len;
        int bytes_consumed = decode_txt_char(ptr, decoded, &decoded_len);

        for (int i = 0; i < decoded_len && char_idx < FD2_DIALOG_LINE_MAX - 1; i++) {
            box->entries[entry_idx].text[char_idx++] = decoded[i];
        }

        ptr += bytes_consumed;
    }

    box->entry_count = entry_idx;
    printf("[DIALOG] Loaded %d dialog entries from FDTXT.DAT\n", box->entry_count);

    return box->entry_count;
}

int fd2_dialog_start(fd2_dialog_box_t* box, int entry_id) {
    if (!box || entry_id < 0 || entry_id >= box->entry_count) return -1;

    box->current_entry = entry_id;
    box->char_index = 0;
    box->type_timer = 0;
    box->typing = true;
    box->waiting_for_input = false;
    box->selected_choice = -1;

    /* Check if entry has choices (marked by | separator) */
    const char* text = box->entries[entry_id].text;
    const char* pipe = strchr(text, '|');
    if (pipe) {
        box->entries[entry_id].has_choices = true;
        /* Parse choices after | */
        const char* choice_ptr = pipe + 1;
        box->entries[entry_id].choice_count = 0;
        while (*choice_ptr && box->entries[entry_id].choice_count < FD2_DIALOG_CHOICE_MAX) {
            int i = 0;
            while (*choice_ptr && *choice_ptr != ';' && *choice_ptr != '|' && i < FD2_DIALOG_LINE_MAX - 1) {
                box->entries[entry_id].choices[box->entries[entry_id].choice_count][i++] = *choice_ptr++;
            }
            box->entries[entry_id].choices[box->entries[entry_id].choice_count][i] = '\0';
            box->entries[entry_id].choice_count++;
            if (*choice_ptr == ';') choice_ptr++;
            else break;
        }
    } else {
        box->entries[entry_id].has_choices = false;
        box->entries[entry_id].choice_count = 0;
    }

    return 0;
}

bool fd2_dialog_update(fd2_dialog_box_t* box, bool advance_pressed) {
    if (!box || !box->typing) return true;

    if (box->waiting_for_input) {
        if (advance_pressed) {
            if (box->entries[box->current_entry].has_choices &&
                box->entries[box->current_entry].choice_count > 0) {
                /* Show choices, wait for selection */
                box->selected_choice = 0;
                return false;
            }
            /* Move to next entry */
            box->current_entry++;
            if (box->current_entry >= box->entry_count) {
                box->typing = false;
                return true;
            }
            fd2_dialog_start(box, box->current_entry);
        }
        return false;
    }

    /* Typing animation */
    box->type_timer++;
    if (box->type_timer >= 2) {  /* 1 character every 2 frames */
        box->type_timer = 0;
        box->char_index++;

        const char* text = box->entries[box->current_entry].text;
        int text_len = (int)strlen(text);

        if (box->char_index >= text_len) {
            box->waiting_for_input = true;
        }
    }

    if (advance_pressed) {
        /* Skip typing animation */
        box->char_index = (int)strlen(box->entries[box->current_entry].text);
        box->waiting_for_input = true;
    }

    return false;
}

static void draw_box(u8* screen, int x, int y, int w, int h, u8 bg, u8 border) {
    for (int dy = 0; dy < h; dy++) {
        for (int dx = 0; dx < w; dx++) {
            int sx = x + dx;
            int sy = y + dy;
            if (sx >= 0 && sx < 320 && sy >= 0 && sy < 200) {
                if (dx == 0 || dx == w - 1 || dy == 0 || dy == h - 1) {
                    screen[sy * 320 + sx] = border;
                } else {
                    screen[sy * 320 + sx] = bg;
                }
            }
        }
    }
}

void fd2_dialog_render(fd2_dialog_box_t* box, u8* screen, int screen_w, int screen_h) {
    if (!box || !screen || box->current_entry < 0) return;

    /* Draw dialog box */
    draw_box(screen, box->display_x, box->display_y,
             box->display_w, box->display_h,
             box->bg_color, box->border_color);

    /* Render text */
    const char* text = box->entries[box->current_entry].text;
    int text_x = box->display_x + 8;
    int text_y = box->display_y + 12;
    int max_chars = box->char_index;

    for (int i = 0; i < max_chars && text[i]; i++) {
        int x = text_x + i * 6;  /* 6 pixels per character */
        int y = text_y;

        if (x < box->display_x + box->display_w - 8 &&
            y < box->display_y + box->display_h - 8) {
            /* Simple character rendering - fill 5x7 pixel block */
            u8 color = box->text_color;
            for (int cy = 0; cy < 7; cy++) {
                for (int cx = 0; cx < 5; cx++) {
                    int px = x + cx;
                    int py = y + cy;
                    if (px >= 0 && px < screen_w && py >= 0 && py < screen_h) {
                        screen[py * screen_w + px] = color;
                    }
                }
            }
        }
    }

    /* Draw blinking cursor if typing */
    if (box->typing && !box->waiting_for_input) {
        int cursor_x = text_x + max_chars * 6;
        int cursor_y = text_y;
        for (int cy = 0; cy < 7; cy++) {
            int px = cursor_x;
            int py = cursor_y + cy;
            if (px >= 0 && px < screen_w && py >= 0 && py < screen_h) {
                screen[py * screen_w + px] = box->text_color;
            }
        }
    }

    /* Draw choices if waiting and has choices */
    if (box->waiting_for_input && box->entries[box->current_entry].has_choices) {
        int choice_y = box->display_y + box->display_h + 5;
        for (int c = 0; c < box->entries[box->current_entry].choice_count; c++) {
            const char* choice_text = box->entries[box->current_entry].choices[c];
            u8 color = (c == box->selected_choice) ? 255 : 180;
            for (int i = 0; choice_text[i]; i++) {
                int x = box->display_x + 20 + i * 6;
                int y = choice_y + c * 10;
                if (x < screen_w - 6 && y < screen_h - 7) {
                    for (int cy = 0; cy < 7; cy++) {
                        int px = x;
                        int py = y + cy;
                        if (px >= 0 && px < screen_w && py >= 0 && py < screen_h) {
                            screen[py * screen_w + px] = color;
                        }
                    }
                }
            }
        }
    }

    /* Draw prompt arrow if waiting */
    if (box->waiting_for_input) {
        int arrow_x = box->display_x + box->display_w - 16;
        int arrow_y = box->display_y + box->display_h - 12;
        /* Simple down arrow */
        screen[(arrow_y) * screen_w + arrow_x] = 255;
        screen[(arrow_y + 1) * screen_w + arrow_x - 1] = 255;
        screen[(arrow_y + 1) * screen_w + arrow_x + 1] = 255;
        screen[(arrow_y + 2) * screen_w + arrow_x - 2] = 255;
        screen[(arrow_y + 2) * screen_w + arrow_x] = 255;
        screen[(arrow_y + 2) * screen_w + arrow_x + 2] = 255;
    }
}

const fd2_dialog_entry_t* fd2_dialog_get_current(const fd2_dialog_box_t* box) {
    if (!box || box->current_entry < 0 || box->current_entry >= box->entry_count) return NULL;
    return &box->entries[box->current_entry];
}

void fd2_dialog_skip(fd2_dialog_box_t* box) {
    if (!box) return;
    if (box->current_entry >= 0 && box->current_entry < box->entry_count) {
        box->char_index = (int)strlen(box->entries[box->current_entry].text);
        box->waiting_for_input = true;
    }
}

int fd2_dialog_get_selected_choice(const fd2_dialog_box_t* box) {
    if (!box) return -1;
    return box->selected_choice;
}
