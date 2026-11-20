# Golden Cookie Catcher

Automatically catch golden cookies in Cookie Clicker (Steam and browser).

A small Windows utility that watches the game window, finds golden cookies on
screen and clicks them for you. Optional big-cookie autoclicker, hotkeys,
system tray.

> **Not affiliated with Dashnet or Orteil.** Cookie Clicker and its artwork
> belong to their respective owners. The sprite used for detection is a crop of
> the game's own asset. The code in this repository is MIT licensed.

## Features

- Watches only the selected game window, never the whole desktop
- Two reaction modes: click on sight, or wait until the cookie fully opens
- Optional autoclicker for the big cookie with adjustable rate, double clicks
  and point offset
- Global hotkeys: start/stop, and a separate one for the autoclicker
- Ignores a dead zone you mark yourself (achievements toasts, banners)
- Sound notification, adjustable threshold, tray icon
- Clicks stop when the game loses focus, so they never land in other windows
- Steam and browser versions supported

## Requirements

- Windows 10 or 11, 64-bit
- Cookie Clicker running in a Steam window, or in a foreground browser tab
- No admin rights needed

## Usage

1. Launch the game, pick **Steam** or **Browser** on the **Catch** tab
2. Press **Pick point (3 s)** and hover the cursor over the big cookie
3. Press **START**

The window can be minimized to tray afterwards. `F8` toggles catching, `F9`
toggles the autoclicker.

**Browser mode** finds the game by its tab title, so the tab has to be the
active one. **Steam mode** finds the game by process name.

Reaction modes:

- **On sight** — clicks the moment the cookie appears
- **When fully open** — waits until the cookie stops growing, fewer misses on
  slow machines

## Build

1. `pip install -r requirements.txt`
2. Icon → `assets/icon_src.png`
3. Sprite → `assets/cookie_src.png` (optional, otherwise a crop from the icon is used)
4. `build.bat`

The result is `dist\GoldenCookieCatcher.exe`, a single portable file. An
installer can be produced with `iscc installer.iss` if Inno Setup is installed.

To test a release build, run the produced exe rather than `python app.py`: the
onefile build unpacks into `%TEMP%` and behaves differently from a source run.

## Changing the sprite

Drop your own crop into `assets/cookie_src.png` and rebuild.

Requirements: tight crop around the cookie only, 40-70 px per side, PNG, no
glow or halo around it, no UI elements in frame. Loose crops and glow make
matching worse, not better.

Update the sprite if a game patch changes the artwork, otherwise detection
quality drops.

## Settings

`settings.json` is stored next to the exe. If the folder is read-only, the app
falls back to `%APPDATA%\GoldenCookieCatcher`. The generated `chime.wav` lives
in the same folder and can be replaced with any WAV file of the same name.

## If it doesn't start

`debug.bat` — will show a traceback. Errors are also written to `crash.log` in
the settings folder.

Other common cases:

- **"Game window not found"** — the game is not running, or in browser mode the
  tab is not the active one
- **Cookie is not detected** — lower the threshold to 0.6-0.65, or check the
  sprite against the current game art
- **Nothing happens on START** — check the Journal tab; the log line will name
  the reason
- **SmartScreen warning** — the exe is unsigned; "More info" → "Run anyway"

## Known limitations

- Detection is visual, so a heavy overlay, a window partially off-screen or an
  unusual zoom level can break it
- The browser mode depends on the tab title and stops working if the tab is
  switched away
- Unsigned binary, so antivirus engines occasionally flag it
- Windows only

## Project structure
app.py main application
build.spec PyInstaller spec
build.bat build script
installer.iss Inno Setup installer
tools/ asset preparation
assets/ icon and sprite sources


## Related

A JavaScript Workshop mod with the same purpose lives in
"github.com/anorexianeedscode/Golden-Cookie-Catcher". The mod needs no external program but only
works inside the game window; this utility works with the game in the
background.

## License
MIT, see `LICENSE`. Cookie Clicker artwork belongs to Dashnet.