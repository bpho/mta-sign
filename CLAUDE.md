# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A real-time NYC subway arrival board running on a Raspberry Pi Zero W with a 64x32 RGB LED matrix, styled after MTA station signs. Two screens rotate every 10 seconds — Queens Plaza (E/R trains) and Court Square (7/G trains).

## Running

```bash
# On the Pi only — requires hardware and the rpi-rgb-led-matrix library
sudo python3 display.py

# Test fetcher independently (no hardware needed)
python3 fetcher.py
```

`display.py` must run as root (`sudo`) because the RGB matrix library requires direct GPIO access.

## Architecture

Two files, no framework:

**`fetcher.py`** — pulls MTA GTFS-RT protobuf feeds over HTTP, parses them, and returns the next arrival per route as `{'route': str, 'minutes': int, 'destination': str}` or `None` if no train is running. No API key required. Run it standalone to test feed connectivity.

**`display.py`** — owns the matrix and all rendering. On startup it does an initial blocking fetch, then spawns a daemon thread (`fetch_loop`) that refreshes every 30 seconds. The main loop redraws only when data or screen index changes, swapping via `matrix.SwapOnVSync` to avoid tearing. A `state_lock` (`threading.Lock`) guards `all_data` and `all_fetch_times` shared between threads.

Key constants in `display.py`:
- `SCREEN_DURATION = 10` — seconds per station screen
- `FETCH_INTERVAL = 30` — background fetch cadence
- `STALE_THRESHOLD = 180` — seconds before "No data" warning
- `BRIGHTNESS_DAY/NIGHT = 50/15` — checked every 60s; night is 8 PM–7 AM ET
- `gpio_slowdown = 4` — tuned for Pi Zero W; reduce for faster Pi models

## Hardware-specific setup

The `rpi-rgb-led-matrix` library is cloned to `/home/bpho/rpi-rgb-led-matrix` and built in-place. `display.py` hardcodes this path in `sys.path.append` and for font loading. Audio must be disabled system-wide (blacklist `snd_bcm2835`) because it conflicts with the matrix PWM.

## MTA feed mapping

| Feed key | URL suffix | Routes |
|----------|-----------|--------|
| `ace` | `gtfs-ace` | E train |
| `nqrw` | `gtfs-nqrw` | R train |
| `1234567` | `gtfs` | 7 train |
| `g` | `gtfs-g` | G train |

Stop IDs: Queens Plaza = `G08N` (E and R, northbound), Court Square = `723N` (7, northbound) and `G22S` (G, southbound).
