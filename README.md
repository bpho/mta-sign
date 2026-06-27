# mta-sign

A real-time NYC subway arrival board running on a Raspberry Pi Zero W with a 64×32 RGB LED matrix, styled after the MTA's own station signs.

## Hardware

- Waveshare 64×32 RGB LED Matrix Panel (3mm pitch)
- Adafruit RGB Matrix Bonnet
- Raspberry Pi Zero W (with headers)
- Adafruit 5V 4A switching power supply (via bonnet barrel jack)
- M3 standoffs to mount Pi + bonnet to panel back

## Display

Two screens rotate automatically:

- **Queens Plaza** — R and E trains to Manhattan
- **Court Square** — 7 train to Manhattan, G train to Brooklyn

Each row shows a colored train bullet, scrolling destination text (left scroll, MTA-style), and arrival time pinned right.

## Setup

### Hardware
- Power runs through bonnet barrel jack — do not power via Pi micro-USB
- HUB75 ribbon cable connects bonnet to panel INPUT port
- Red/black power cable connects bonnet screw terminals (+/−) to panel VH4 connector

### Software dependencies
- Raspbian Bookworm
- rpi-rgb-led-matrix (hzeller) — built from source at `~/rpi-rgb-led-matrix`
- Python bindings manually compiled with Cython
- `gtfs-realtime-bindings`, `requests`, `protobuf`
- Audio module blacklisted (`/etc/modprobe.d/blacklist.conf`)

### Config
Copy `config.example.json` to `config.json` and add your MTA API key. Never commit `config.json`.

## Data source
MTA real-time GTFS feed via `https://api.mta.info/`
