# mta-sign

A real-time NYC subway arrival board running on a Raspberry Pi Zero W with a 64x32 RGB LED matrix, styled after the MTA's own station signs.

## Hardware

- Waveshare 64x32 RGB LED Matrix Panel (3mm pitch)
- Adafruit RGB Matrix Bonnet
- Raspberry Pi Zero W (with headers)
- Adafruit 5V 4A switching power supply (via bonnet barrel jack)
- M3 standoffs to mount Pi + bonnet to panel back

## Display

Two screens rotate every 10 seconds:

- Queens Plaza -- E train to WTC, R train to Bay Ridge
- Court Square -- 7 train to Hudson Yards, G train to Church Av

Each row shows a colored train bullet, destination text, and arrival time pinned right. Arrival times under 3 minutes show in yellow, everything else in green.

## Features

- Live MTA GTFS-RT data, refreshed every 30 seconds
- Background fetch thread so display never stutters during API calls
- Late night dim mode -- brightness drops from 50 to 15 after 8:00 PM ET
- Stale data warning after 3 minutes without a successful fetch
- No service message if a train is not running

## Sample Experience (Updated 6/28)
<img width="300" height="400" alt="F709512C-A89B-4540-8FBA-DE4BDEEC2295_1_102_o" src="https://github.com/user-attachments/assets/3029c7fc-5455-4fb1-8429-12baa679d48e" />

## Setup

### Hardware
- Power runs through bonnet barrel jack -- do not power via Pi micro-USB
- HUB75 ribbon cable connects bonnet to panel INPUT port
- Red/black power cable connects bonnet screw terminals (+/-) to panel VH4 connector
- M3 standoffs mount Pi + bonnet flush to panel back

### System dependencies
sudo apt update && sudo apt upgrade -y
sudo apt install -y git python3-dev python3-pillow cython3 python3-pip

### Disable audio (required)
Add to /boot/firmware/config.txt:
dtparam=audio=off

Blacklist the module in /etc/modprobe.d/blacklist.conf:
blacklist snd_bcm2835

### RGB matrix library
cd ~
git clone --recurse-submodules https://github.com/hzeller/rpi-rgb-led-matrix.git
cd rpi-rgb-led-matrix
make -C lib
make -C examples-api-use
cd bindings/python
sudo cython3 --cplus rgbmatrix/core.pyx rgbmatrix/graphics.pyx
Then compile core and graphics extensions with distutils (see setup notes in repo history).

### Python dependencies
sudo pip3 install --break-system-packages gtfs-realtime-bindings requests protobuf pytz

### Running

Install and start as a systemd service (auto-starts on boot, restarts on crash):
```
cd ~/mta-sign && git pull
sudo cp mta-sign.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable mta-sign
sudo systemctl start mta-sign
```

Common service commands:
```
sudo systemctl status mta-sign   # check status and recent logs
sudo systemctl stop mta-sign     # stop
sudo systemctl restart mta-sign  # restart
sudo systemctl disable mta-sign  # prevent auto-start on boot
journalctl -fu mta-sign          # stream live logs
```

To run manually without systemd:
```
cd ~/mta-sign
sudo python3 display.py
```

## Data source

MTA real-time GTFS-RT feeds -- no API key required for subway:
- gtfs-ace (E train)
- gtfs-nqrw (R train)
- gtfs (7 train)
- gtfs-g (G train)

All feeds at: https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct/

## Known issues / next steps

- Slight pixel flickering present -- likely a Pi Zero W GPIO timing limitation
- Troubleshooting plan:
  - Test power adapter plugged into different outlet
  - Disable Tailscale VPN on Pi to reduce CPU/WiFi load
  - Disable FreshRSS to free up resources
  - Test with WiFi disabled to confirm WiFi interference theory
- Displayed arrival times deviate from Google Maps / MTA apps -- see [NOTES.md](NOTES.md) for the five root causes and proposed fixes

## Potential improvements

- Auto-start on boot via systemd
- Show next 2 arrivals per line (e.g. 5m 12m)
- Real-time countdown between fetches
- Clock screen between station screens
- Flash arrival time when train is 1 minute away
- Service alert indicator for delays
- Smooth screen transition (fade/wipe)
- Config file for stations, brightness, and timing
- Retry logic in fetcher
- Watchdog systemd service
- Error logging to file
- isolcpus=3 in cmdline.txt to reserve a CPU core for matrix
