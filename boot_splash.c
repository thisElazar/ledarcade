/*
 * boot_splash.c — instant boot indicator for LED arcade.
 * Compiled C so it starts in milliseconds, not seconds like Python.
 * Shows a pulsing white dot in the center of the 64x64 matrix.
 *
 * Compile on Pi:
 *   gcc -O2 -o boot_splash boot_splash.c \
 *       -I/home/thiselazar/rpi-rgb-led-matrix/include \
 *       -L/home/thiselazar/rpi-rgb-led-matrix/lib \
 *       -lrgbmatrix -lstdc++ -lm -lpthread
 */

#include <led-matrix-c.h>
#include <math.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

static volatile int running = 1;

static void handle_signal(int sig) {
    (void)sig;
    running = 0;
}

int main(void) {
    struct RGBLedMatrixOptions opts;
    struct RGBLedMatrix *matrix;
    struct LedCanvas *canvas;

    memset(&opts, 0, sizeof(opts));
    opts.rows = 64;
    opts.cols = 64;
    opts.hardware_mapping = "led-arcade";
    opts.brightness = 80;

    int argc = 4;
    char *argv[] = {"boot_splash", "--led-gpio-slowdown=4",
                    "--led-drop-privs=0", NULL};
    char **argv_ptr = argv;

    matrix = led_matrix_create_from_options(&opts, &argc, &argv_ptr);
    if (!matrix) {
        fprintf(stderr, "boot_splash: could not init matrix\n");
        return 1;
    }

    canvas = led_matrix_create_offscreen_canvas(matrix);

    signal(SIGTERM, handle_signal);
    signal(SIGINT, handle_signal);

    const int cx = 31, cy = 31;
    double t = 0.0;

    while (running) {
        double breath = (sin(t * 2.5) + 1.0) / 2.0;
        int bright = (int)(30 + 225 * breath);
        int dim = (int)(10 + 50 * breath);

        led_canvas_clear(canvas);

        /* Core pixel */
        led_canvas_set_pixel(canvas, cx, cy, bright, bright, bright);

        /* Soft halo */
        led_canvas_set_pixel(canvas, cx - 1, cy, dim, dim, dim);
        led_canvas_set_pixel(canvas, cx + 1, cy, dim, dim, dim);
        led_canvas_set_pixel(canvas, cx, cy - 1, dim, dim, dim);
        led_canvas_set_pixel(canvas, cx, cy + 1, dim, dim, dim);

        canvas = led_matrix_swap_on_vsync(matrix, canvas);

        usleep(33333); /* ~30 fps */
        t += 1.0 / 30.0;
    }

    led_matrix_delete(matrix);
    return 0;
}
