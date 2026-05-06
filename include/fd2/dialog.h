#ifndef FD2_DIALOG_H
#define FD2_DIALOG_H

#include "fd2/types.h"

#ifdef __cplusplus
extern "C" {
#endif

/* ---- Dialog System ----
 * Based on IDA sub_15F84 - Dialog display system.
 * Loads text from FDTXT.DAT and renders dialog UI.
 */

#define FD2_DIALOG_LINE_MAX 64
#define FD2_DIALOG_CHAR_MAX 8
#define FD2_DIALOG_CHOICE_MAX 4

typedef struct {
    char text[FD2_DIALOG_LINE_MAX];
    int  speaker_id;
    bool has_choices;
    int  choice_count;
    char choices[FD2_DIALOG_CHOICE_MAX][FD2_DIALOG_LINE_MAX];
    int  selected_choice;
} fd2_dialog_entry_t;

typedef struct {
    fd2_dialog_entry_t* entries;
    int                 entry_count;
    int                 current_entry;
    int                 char_index;        /* Current character being typed */
    int                 type_timer;        /* Typing speed timer */
    bool                typing;
    bool                waiting_for_input;
    int                 display_x;
    int                 display_y;
    int                 display_w;
    int                 display_h;
    u8                  text_color;
    u8                  bg_color;
    u8                  border_color;
    int                 selected_choice;   /* Currently selected choice index */
} fd2_dialog_box_t;

/* Initialize dialog system */
int  fd2_dialog_init(fd2_dialog_box_t* box);
void fd2_dialog_shutdown(fd2_dialog_box_t* box);

/* Load dialog data from FDTXT.DAT resource */
int  fd2_dialog_load_from_dat(fd2_dialog_box_t* box, const u8* txt_data, u32 txt_size);

/* Start displaying a dialog entry */
int  fd2_dialog_start(fd2_dialog_box_t* box, int entry_id);

/* Update dialog (returns true when dialog is complete) */
bool fd2_dialog_update(fd2_dialog_box_t* box, bool advance_pressed);

/* Render dialog box to screen buffer */
void fd2_dialog_render(fd2_dialog_box_t* box, u8* screen, int screen_w, int screen_h);

/* Get current dialog entry */
const fd2_dialog_entry_t* fd2_dialog_get_current(const fd2_dialog_box_t* box);

/* Skip to end of current dialog */
void fd2_dialog_skip(fd2_dialog_box_t* box);

/* Get selected choice (after choices are shown) */
int  fd2_dialog_get_selected_choice(const fd2_dialog_box_t* box);

#ifdef __cplusplus
}
#endif

#endif /* FD2_DIALOG_H */
