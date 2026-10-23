// Headless doomgeneric backend for the LED preview (doom_preview/viewer.py).
// Each frame goes out on the fd named by $DOOM_FRAME_FD as "DOOM" + 40 int16
// player-state fields + the last HUD message (64 bytes) + the finished and
// next level names (2 x 32 bytes, intermission only) + the 320x200 XRGB buffer. Key events come in on stdin as 2-byte pairs
// (pressed, doomkey); pressed 2/3/4 instead sets run turn speed / slow turn
// speed (value * 32 angle units per tic) / slow-turn ramp tics, 5 extra light
// (0-15), 6 full bright (0/1), 7 paused (0/1), 8 finish level (test harness),
// 9 no red damage tint (0/1), 10 save the game to slot <value> (only in a
// level, alive, not in a demo; header field 37 counts finished saves).
// After the frame comes the
// 320x200 sprite mask.
// Doom's own printf chatter stays on stdout.
#include "doomgeneric.h"
#include "doomstat.h"
#include "d_items.h"
#include "i_video.h"
#include "g_game.h"
#include "r_main.h"
#include "deh_str.h"
#include "m_misc.h"

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/time.h>

static int frame_fd = -1;

extern char dg_message[64];      // hu_stuff.c
extern int dg_message_serial;
extern fixed_t angleturn[3];     // g_game.c: walk, run, slow turn
extern int slowturntics;
extern int dg_extralight, dg_fullbright;   // r_main.c
extern int dg_no_damage_tint;              // st_stuff.c
extern byte dg_spritemask[];               // r_things.c
void DG_WIStats(short *out);               // wi_stuff.c
extern char *mapnames[], *mapnames_commercial[];   // hu_stuff.c
extern int dg_save_serial;                 // g_game.c: saves written so far

static void write_all(const void *buf, size_t n)
{
    const char *p = buf;
    while (n) {
        ssize_t w = write(frame_fd, p, n);
        if (w <= 0) _exit(0);   // viewer went away
        p += w;
        n -= (size_t)w;
    }
}

void DG_Init()
{
    const char *fd = getenv("DOOM_FRAME_FD");
    frame_fd = fd ? atoi(fd) : 3;
    fcntl(STDIN_FILENO, F_SETFL, fcntl(STDIN_FILENO, F_GETFL) | O_NONBLOCK);
}

void DG_DrawFrame()
{
    int16_t hdr[40] = {0};
    if (gamestate == GS_LEVEL) {
        player_t *p = &players[consoleplayer];
        int at = weaponinfo[p->readyweapon].ammo;
        int keys = 0, owned = 0;
        for (int i = 0; i < NUMCARDS; i++)
            if (p->cards[i]) keys |= 1 << i;
        for (int i = 0; i < NUMWEAPONS; i++)
            if (p->weaponowned[i]) owned |= 1 << i;
        hdr[0] = 1;                                   // in a level
        hdr[1] = p->health;
        hdr[2] = p->armorpoints;
        hdr[3] = at == am_noammo ? -1 : p->ammo[at];
        hdr[4] = keys;                                // bit order: blue yellow red, then skulls
        hdr[5] = p->readyweapon;
        hdr[6] = p->damagecount;
        hdr[7] = owned;                               // bit per weapontype_t
        for (int i = 0; i < NUMAMMO; i++) {
            hdr[8 + i] = p->ammo[i];
            hdr[12 + i] = p->maxammo[i];
        }
        hdr[16] = p->armortype;
        hdr[17] = p->bonuscount;
        hdr[18] = at;                                 // ammotype_t of the ready weapon
        if (p->mo) {
            hdr[20] = p->mo->x >> FRACBITS;             // map units
            hdr[21] = p->mo->y >> FRACBITS;
            hdr[22] = p->mo->angle >> 20;               // 0-4095 = full turn
            if (p->damagecount && p->attacker && p->attacker != p->mo) {
                angle_t a = R_PointToAngle2(p->mo->x, p->mo->y, p->attacker->x, p->attacker->y);
                hdr[34] = 1;                                // hit by something with a position
                hdr[35] = (a - p->mo->angle) >> 20;         // 0 ahead, 1024 left, 2048 behind
            }
        }
    }
    hdr[23] = gamestate;                              // 0 level, 1 intermission, 2 finale, 3 demo
    if (gamestate == GS_INTERMISSION)
        DG_WIStats(&hdr[24]);                         // 24-33, see wi_stuff.c
    hdr[19] = (int16_t)dg_message_serial;
    hdr[36] = 1;                                      // this engine takes command 10 (save)
    hdr[37] = (int16_t)dg_save_serial;
    hdr[38] = gameepisode;                            // current level (also during the tally)
    hdr[39] = gamemap;
    write_all("DOOM", 4);
    write_all(hdr, sizeof hdr);
    write_all(dg_message, sizeof dg_message);
    char names[2][32] = {{0}};
    if (gamestate == GS_INTERMISSION) {
        for (int i = 0; i < 2; i++) {
            int e = hdr[31], m = hdr[32 + i];           // wi episode, last / next
            const char *n = gamemode == commercial ? mapnames_commercial[m] : mapnames[e * 9 + m];
            M_StringCopy(names[i], DEH_String(n), sizeof names[i]);
        }
    }
    write_all(names, sizeof names);
    write_all(DG_ScreenBuffer, DOOMGENERIC_RESX * DOOMGENERIC_RESY * 4);
    write_all(dg_spritemask, SCREENWIDTH * SCREENHEIGHT);
    memset(dg_spritemask, 0, SCREENWIDTH * SCREENHEIGHT);
}

void DG_SleepMs(uint32_t ms) { usleep(ms * 1000); }

uint32_t DG_GetTicksMs()
{
    struct timeval tv;
    gettimeofday(&tv, NULL);
    return (uint32_t)(tv.tv_sec * 1000 + tv.tv_usec / 1000);
}

int DG_GetKey(int *pressed, unsigned char *key)
{
    unsigned char ev[2];
    for (;;) {
        if (read(STDIN_FILENO, ev, 2) != 2) return 0;
        if (ev[0] == 2) angleturn[1] = ev[1] * 32;
        else if (ev[0] == 3) angleturn[2] = ev[1] * 32;
        else if (ev[0] == 4) slowturntics = ev[1];
        else if (ev[0] == 5) dg_extralight = ev[1];
        else if (ev[0] == 6) dg_fullbright = ev[1];
        else if (ev[0] == 7) paused = ev[1];
        else if (ev[0] == 8) G_ExitLevel();
        else if (ev[0] == 9) dg_no_damage_tint = ev[1];
        else if (ev[0] == 10) {
            if (gamestate == GS_LEVEL && !demoplayback
                && players[consoleplayer].playerstate == PST_LIVE)
                G_SaveGame(ev[1], "CABINET");
        }
        else break;
    }
    *pressed = ev[0];
    *key = ev[1];
    return 1;
}

void DG_SetWindowTitle(const char *title) { (void)title; }

int main(int argc, char **argv)
{
    doomgeneric_Create(argc, argv);
    for (;;) doomgeneric_Tick();
}
