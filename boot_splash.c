/*
 * boot_splash.c — instant boot indicator for LED arcade.
 * Compiled C so it starts in milliseconds, not seconds like Python.
 * Shows a pulsing white dot in the center of the 64x64 matrix.
 *
 * Compile on Pi (adjust library path to match your setup):
 *   gcc -O2 -o boot_splash boot_splash.c \
 *       -I$HOME/rpi-rgb-led-matrix/include \
 *       -L$HOME/rpi-rgb-led-matrix/lib \
 *       -lrgbmatrix -lstdc++ -lm -lpthread
 */

#include <led-matrix-c.h>
#include <math.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

static volatile int running = 1;

static void handle_signal(int sig) {
    (void)sig;
    running = 0;
}

/*
 * Read hardware_mapping and gpio_slowdown from cabinet_config.json.
 * Falls back to dev defaults if the file is missing or unparseable.
 */
static void read_config(char *mapping, size_t map_size, int *slowdown) {
    strncpy(mapping, "led-arcade", map_size - 1);
    mapping[map_size - 1] = '\0';
    *slowdown = 4;

    FILE *f = fopen("cabinet_config.json", "r");
    if (!f) return;

    char buf[1024];
    size_t n = fread(buf, 1, sizeof(buf) - 1, f);
    fclose(f);
    buf[n] = '\0';

    char *p = strstr(buf, "\"hardware_mapping\"");
    if (p) {
        p = strchr(p + 18, '"');
        if (p) {
            p++;
            char *end = strchr(p, '"');
            if (end && (size_t)(end - p) < map_size) {
                memcpy(mapping, p, end - p);
                mapping[end - p] = '\0';
            }
        }
    }

    p = strstr(buf, "\"gpio_slowdown\"");
    if (p) {
        p = strchr(p + 15, ':');
        if (p) {
            int val = atoi(p + 1);
            if (val > 0) *slowdown = val;
        }
    }
}

int main(void) {
    struct RGBLedMatrixOptions opts;
    struct RGBLedMatrix *matrix;
    struct LedCanvas *canvas;

    struct RGBLedRuntimeOptions rt_opts;

    char mapping[64];
    int slowdown;
    read_config(mapping, sizeof(mapping), &slowdown);

    memset(&opts, 0, sizeof(opts));
    opts.rows = 64;
    opts.cols = 64;
    opts.hardware_mapping = mapping;
    opts.brightness = 80;

    memset(&rt_opts, 0, sizeof(rt_opts));
    rt_opts.gpio_slowdown = slowdown;
    rt_opts.drop_privileges = 0;
    rt_opts.do_gpio_init = true;

    matrix = led_matrix_create_from_options_and_rt_options(&opts, &rt_opts);
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
