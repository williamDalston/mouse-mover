#!/bin/bash
# Build Mouse Mover into a standalone app
# Usage: ./build.sh
#
# Produces release-ready files that match the download links on the site:
#   Mac:     dist/MouseMover.zip  (contains Mouse Mover.app)
#   Windows: dist/MouseMover.exe

set -e

echo "Installing dependencies..."
pip install -r requirements.txt

echo ""
echo "Building Mouse Mover..."

if [[ "$OSTYPE" == "darwin"* ]]; then
    pyinstaller \
        --name "Mouse Mover" \
        --windowed \
        --onefile \
        --clean \
        mouse-mover-gui.py

    echo "Zipping for distribution..."
    cd dist
    zip -r MouseMover.zip "Mouse Mover.app"
    cd ..

    echo ""
    echo "Done! Upload this to a GitHub Release:"
    echo "  dist/MouseMover.zip"
else
    pyinstaller \
        --name "MouseMover" \
        --windowed \
        --onefile \
        --clean \
        mouse-mover-gui.py

    echo ""
    echo "Done! Upload this to a GitHub Release:"
    echo "  dist/MouseMover.exe"
fi
