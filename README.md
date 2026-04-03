# Mouse Mover

A simple desktop app that keeps your computer active by moving your mouse automatically.

**[Download it here →](https://williamdalston.github.io/mouse-mover/)**

![Platform: Mac & Windows](https://img.shields.io/badge/platform-macOS%20%7C%20Windows-blue)
![License: MIT](https://img.shields.io/badge/license-MIT-green)

## What it does

- Moves your mouse randomly in the background so your computer stays awake
- Natural-looking movement with random speed, direction, and micro-adjustments
- One-click start/stop with a clean GUI
- Emergency stop: move your mouse to any screen corner

## Download

Go to the [landing page](https://williamdalston.github.io/mouse-mover/) or grab the latest release directly:

| Platform | Download |
|----------|----------|
| **Mac** | [MouseMover.dmg](https://github.com/williamDalston/mouse-mover/releases/latest/download/MouseMover.dmg) |
| **Windows** | [MouseMover.exe](https://github.com/williamDalston/mouse-mover/releases/latest/download/MouseMover.exe) |

The Mac build is code-signed and notarized with Apple — no Gatekeeper warnings.

## Running from source

If you'd rather run the Python script directly:

```bash
pip install pyautogui
python mouse-mover-gui.py
```

Requires Python 3.9+.

## Building from source

The build script handles everything — bundling, code signing (Mac), and notarization (Mac):

```bash
./build.sh
```

**Mac prerequisites:**
- A Developer ID Application certificate in your keychain
- Notarization credentials stored via: `xcrun notarytool store-credentials "notary-profile"`

**Windows prerequisites:**
- Just Python and pip

Output:
- Mac: `dist/MouseMover.dmg` (signed + notarized disk image)
- Windows: `dist/MouseMover.exe`

## Releasing

1. Commit your changes and push
2. Tag a version: `git tag v1.x.x && git push origin v1.x.x`
3. GitHub Actions builds the Windows `.exe` automatically
4. For Mac, run `./build.sh` locally (requires your signing certificate), then upload:
   ```bash
   gh release upload v1.x.x dist/MouseMover.dmg --clobber
   ```

## Project structure

```
mouse-mover-gui.py   # Main app — tkinter GUI + mouse control logic
build.sh             # Build, sign, and notarize script
requirements.txt     # Python dependencies
docs/index.html      # GitHub Pages landing page
.github/workflows/   # CI — builds Windows exe on version tags
```
