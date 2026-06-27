import sys
import os
import time
import threading
from datetime import datetime
import pytz
sys.path.append('/home/bpho/rpi-rgb-led-matrix/bindings/python')

from rgbmatrix import RGBMatrix, RGBMatrixOptions, graphics
from fetcher import get_queens_plaza, get_court_square

MATRIX_PATH = '/home/bpho/rpi-rgb-led-matrix'

TRAIN_COLORS = {
    'E': (0, 57, 166),
    'R': (252, 204, 10),
    'G': (108, 190, 69),
    '7': (182, 56, 158),
}

BULLET_TEXT_COLOR = graphics.Color(255, 255, 255)

DESTINATIONS = {
    'E': 'WTC',
    'R': 'Bay Ridge',
    '7': 'Hudson Yds',
    'G': 'Church Av',
}

STALE_THRESHOLD = 180
BRIGHTNESS_DAY = 50
BRIGHTNESS_NIGHT = 15
NIGHT_HOUR_START = 20
NIGHT_HOUR_END = 7
ET = pytz.timezone('America/New_York')
FETCH_INTERVAL = 30

state_lock = threading.Lock()
all_data = [[None, None], [None, None]]
all_fetch_times = [0, 0]

def is_night():
    now = datetime.now(ET)
    hour = now.hour
    return hour >= NIGHT_HOUR_START or hour < NIGHT_HOUR_END

def fetch_loop(screens):
    while True:
        for i, screen in enumerate(screens):
            try:
                data = screen['fetcher']()
                print(f"Fetched {screen['title']}: {data}")
                with state_lock:
                    all_data[i] = data
                    all_fetch_times[i] = time.time()
            except Exception as e:
                print(f"Fetch error for {screen['title']}: {e}")
        time.sleep(FETCH_INTERVAL)

def draw_bullet(canvas, x, y, route):
    color = TRAIN_COLORS.get(route, (255, 255, 255))
    r, g, b = color
    for dx in range(5):
        for dy in range(5):
            if (dx == 0 or dx == 4) and (dy == 0 or dy == 4):
                continue
            canvas.SetPixel(x + dx, y + dy, r, g, b)
    graphics.DrawText(canvas, font, x + 1, y + 5, BULLET_TEXT_COLOR, route)

def draw_train_row(canvas, y, route, minutes):
    draw_bullet(canvas, 1, y + 1, route)
    dest = DESTINATIONS.get(route, route)
    text_color = graphics.Color(255, 255, 255)
    graphics.DrawText(canvas, font, 8, y + 6, text_color, dest)
    time_str = f'{minutes}m'
    time_color = graphics.Color(255, 255, 0) if minutes <= 3 else graphics.Color(125, 211, 69)
    time_x = 62 - (len(time_str) * 4)
    graphics.DrawText(canvas, font, time_x, y + 6, time_color, time_str)

def draw_loading(canvas, title):
    canvas.Clear()
    title_color = graphics.Color(255, 204, 0)
    text_color = graphics.Color(100, 100, 100)
    graphics.DrawText(canvas, font, 1, 7, title_color, title)
    graphics.DrawLine(canvas, 0, 9, 63, 9, graphics.Color(40, 40, 40))
    graphics.DrawText(canvas, font, 8, 16, text_color, 'Loading...')

def draw_screen(canvas, title, trains, last_fetch_time):
    canvas.Clear()
    title_color = graphics.Color(255, 204, 0)
    text_color = graphics.Color(255, 255, 255)
    stale = (time.time() - last_fetch_time) > STALE_THRESHOLD

    graphics.DrawText(canvas, font, 1, 7, title_color, title)
    graphics.DrawLine(canvas, 0, 9, 63, 9, graphics.Color(40, 40, 40))

    row_y = [10, 21]
    for i, train in enumerate(trains):
        if stale:
            graphics.DrawText(canvas, font, 8, row_y[i] + 6, graphics.Color(150, 150, 150), 'No data')
            continue
        if train is None:
            graphics.DrawText(canvas, font, 8, row_y[i] + 6, text_color, 'No service')
            continue
        draw_train_row(canvas, row_y[i], train['route'], train['minutes'])

def run():
    global font

    font = graphics.Font()
    font.LoadFont(os.path.join(MATRIX_PATH, 'fonts/4x6.bdf'))

    options = RGBMatrixOptions()
    options.rows = 32
    options.cols = 64
    options.hardware_mapping = 'adafruit-hat'
    options.gpio_slowdown = 4
    options.disable_hardware_pulsing = True
    options.brightness = BRIGHTNESS_NIGHT if is_night() else BRIGHTNESS_DAY
    matrix = RGBMatrix(options=options)

    SCREEN_DURATION = 10
    BRIGHTNESS_CHECK_INTERVAL = 60

    screens = [
        {'title': 'QUEENS PLAZA', 'fetcher': get_queens_plaza},
        {'title': 'COURT SQ-23 ST', 'fetcher': get_court_square},
    ]

    # Create canvas once
    canvas = matrix.CreateFrameCanvas()

    # Show loading screen
    draw_loading(canvas, screens[0]['title'])
    canvas = matrix.SwapOnVSync(canvas)

    # Initial fetch
    for i, screen in enumerate(screens):
        try:
            data = screen['fetcher']()
            print(f"Fetched {screen['title']}: {data}")
            with state_lock:
                all_data[i] = data
                all_fetch_times[i] = time.time()
        except Exception as e:
            print(f"Fetch error: {e}")

    # Start background fetch thread
    fetcher_thread = threading.Thread(target=fetch_loop, args=(screens,), daemon=True)
    fetcher_thread.start()

    current_screen = 0
    last_switch = time.time()
    last_brightness_check = time.time()
    current_brightness = options.brightness
    last_drawn_screen = -1
    last_drawn_data = None

    try:
        while True:
            now = time.time()

            # Brightness check
            if now - last_brightness_check > BRIGHTNESS_CHECK_INTERVAL:
                target = BRIGHTNESS_NIGHT if is_night() else BRIGHTNESS_DAY
                if target != current_brightness:
                    matrix.SetBrightness(target)
                    current_brightness = target
                    print(f"Brightness set to {target}")
                last_brightness_check = now

            # Screen switch
            if now - last_switch > SCREEN_DURATION:
                current_screen = (current_screen + 1) % len(screens)
                last_switch = now
                print(f"Switched to {screens[current_screen]['title']}")

            # Get current data safely
            with state_lock:
                train_data = list(all_data[current_screen])
                fetch_time = all_fetch_times[current_screen]

            # Only redraw if something changed
            if current_screen != last_drawn_screen or train_data != last_drawn_data:
                draw_screen(canvas, screens[current_screen]['title'], train_data, fetch_time)
                canvas = matrix.SwapOnVSync(canvas)
                last_drawn_screen = current_screen
                last_drawn_data = list(train_data)

            time.sleep(0.1)

    except KeyboardInterrupt:
        matrix.Clear()

if __name__ == '__main__':
    run()
