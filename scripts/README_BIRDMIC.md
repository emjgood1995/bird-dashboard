# BirdMic / BirdNET-Pi Helper Scripts

These scripts are standalone operational tools for running on the Raspberry Pi.
They are not imported by `app.py`.

## Files

- `scripts/birdmic_sync_to_repo.sh`
  - Detects or accepts the source BirdNET-Pi database path.
  - Calls `scripts/push_birds_db.sh` to update `birds_lfs.db`, commit, and push.

- `scripts/birdmic_cleanup_wavs.sh`
  - Finds old `.wav` files in `BirdSongs` and optionally deletes them.
  - Default mode is dry-run.

- `scripts/install_birdmic_cron.sh`
  - Installs two cron jobs:
    - DB sync/push
    - WAV cleanup

## Quick Start

1. Make sure SSH auth to GitHub works on the Pi:

```bash
ssh -T git@github.com
```

2. Test DB sync manually:

```bash
cd /path/to/bird-dashboard
./scripts/birdmic_sync_to_repo.sh /home/birdnet/BirdNET-Pi/birds.db
```

3. Test WAV cleanup (dry-run first):

```bash
cd /path/to/bird-dashboard
./scripts/birdmic_cleanup_wavs.sh /home/birdnet/BirdNET-Pi/BirdSongs 14
```

4. Install cron jobs:

```bash
cd /path/to/bird-dashboard
./scripts/install_birdmic_cron.sh /home/birdnet/BirdNET-Pi/birds.db
```

## Cron defaults

- DB sync: `15 2 * * *`
- WAV cleanup: `45 2 * * *`
- Cleanup threshold: files older than 14 days

You can override schedules/env vars when running `install_birdmic_cron.sh`.
