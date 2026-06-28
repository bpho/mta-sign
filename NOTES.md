# Notes

Investigation notes, analyses, and proposals that aren't yet code. Once a finding is acted on, remove it from here.

## Arrival time reliability (2026-06-28)

Times displayed on the sign deviate from Google Maps and the MTA's own apps — generally reading higher (later) than reality, with occasional sudden jumps. Five compounding causes identified.

### 1. Stale minutes value (biggest visible issue)

`fetcher.py:43` computes `minutes` once at fetch time and stores the integer. `display.py` reuses it for up to 30 seconds without recalculating. A train fetched as "3m" displays "3m" the entire time it's actually counting down to "2m30s", "2m", "1m30s" — then jumps when the next fetch lands.

**Fix:** store the raw Unix arrival timestamp in the dict; compute minutes live inside `display.py:draw_train_row`.

### 2. `round()` overstates times

Python's `round()` rounds half to even, and more importantly rounds **up** at ≥30 seconds:
- Train 2m45s away → `round(2.75)` = 3 (MTA shows "2 min")
- Train 1m31s away → `round(1.52)` = 2 (MTA shows "1 min")

MTA convention floors: "2 min" means 2:00–2:59 away. Using `round()` puts our sign consistently 0–30s higher than everyone else.

**Fix:** `int((t - now) // 60)` instead of `round((t - now) / 60)`.

### 3. Cancelled / skipped trips counted as arrivals

The MTA feed marks trips with `trip.schedule_relationship == CANCELED` and individual stops with `schedule_relationship == SKIPPED`. The fetcher ignores both. A cancelled train can appear as "5m" and never come.

**Fix:** filter out CANCELED trips and SKIPPED stops in `get_arrivals`.

### 4. Reference clock skew

`fetcher.py:33` uses `time.time()` (local Pi clock) as "now", but feed predictions reference MTA server time. Pi Zero W NTP is unreliable (WiFi drops). The feed publishes its own reference at `feed.header.timestamp`.

**Fix:** use `feed.header.timestamp` as "now" inside `get_arrivals`.

### 5. Compounding fetch lag

MTA refreshes feeds ~every 30s. Our fetcher polls every 30s (random offset). Worst-case lag: ~30s (MTA delay) + ~30s (our poll miss) + ~30s (display freeze from #1) = ~90s.

**Fix:** drop `FETCH_INTERVAL` from 30 to 15. Doesn't help if #1 isn't fixed.

### Open question: direction of stop IDs

`fetcher.py:14-23` uses `G08N` for both E (to WTC) and R (to Bay Ridge) at Queens Plaza. Both are Manhattan-bound, which in MTA's GTFS convention is usually the `S` suffix. If the suffix is wrong, the sign would be showing trains going the *opposite* direction — which would explain large unexplained deviations.

Verify against MTA's GTFS stops.txt before changing. Source: `http://web.mta.info/developers/data/nyct/subway/google_transit.zip`.

### Priority order if implementing

1, 2, 3, 4 are tight, low-risk code changes — do together. 5 is a one-line constant. Direction check is research first, then code.
