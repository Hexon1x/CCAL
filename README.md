# CCAL — Colorful Terminal Calendar (TUI)

CCAL is a lightweight, colorful, keyboard-driven calendar for your terminal, built with Python's standard `calendar` and `curses` modules. It focuses on speed, clarity, and a smooth keyboard experience.

## Highlights

- Month and Week views with weekend highlighting
- Fast keyboard navigation for days and months
- Toggle the first day of the week (Mon/Sun)
- Minimal, distraction-free interface (no popups/help overlays)
- Cross-platform: Linux/macOS natively; Windows via `windows-curses`

## What CCAL is (and is not)

- CCAL is a quick, interactive calendar viewer for your terminal.
- It is not a planner or task manager. There is no event storage, theming, or help overlay.

## Installation

- Python 3.10+ is recommended.
- Linux/macOS: `curses` is included by default.
- Windows: install the `curses` port.

```powershell
pip install -r requirements.txt
```

If you prefer manual install on Windows:

```powershell
pip install windows-curses
```

## Run

```powershell
python .\ccal.py
```

## Keyboard Shortcuts

- Arrows / HJKL: Move selection by 1 day (Left/Right) or 7 days (Up/Down)
- PgUp / PgDn: Change month (back/forward)
- T: Jump to today
- W: Toggle week start (Mon/Sun)
- V: Toggle Month/Week view
- Q: Quit

Note: Year navigation is available via month navigation (PgUp/PgDn across December/January boundaries). Shift+PgUp/PgDn and "Go to date" are intentionally not included to keep the UI minimal.

## UI Overview

- Header: current month and year centered on the first line.
- Hint line: compact list of available keys.
- Main area: either Month grid or Week list.
  - Month: days are arranged in a grid; weekends are highlighted; today and the selected day are emphasized.
  - Week: 7-day list starting from the configured first day of week.
- Status bar: shows feedback (e.g., "Next month", "Week starts on Monday").

## Configuration

CCAL stores a tiny configuration file under your home directory:

- Path: `~/.ccal/config.json`
- Keys:
  - `first_weekday`: `"mon"` or `"sun"`

Example:

```json
{
  "first_weekday": "mon"
}
```

You can change the first weekday in-app with the `W` key. Changes are saved automatically.

## Tips

- Terminal too small? CCAL will ask you to resize if it can't render properly (min ~36x10).
- Many terminals support both arrow keys and Vim-style `HJKL` for movement.
- If your terminal doesn't pass PageUp/PageDown, map them in your terminal settings or use the menu keys of your terminal emulator.

## Troubleshooting

- Windows error about curses: ensure `windows-curses` is installed.
- Rendering errors (e.g., `addnstr() returned ERR`): resize your terminal larger; CCAL clamps writes but very small windows may still limit the view.
- Locale: CCAL uses your environment locale to render month/day names from Python's `calendar`.

## Roadmap (optional)

- Optional help overlay
- Customizable key bindings
- Daily/hourly view
- Packaging with `pipx`/`pyinstaller`

Contributions and suggestions are welcome!
