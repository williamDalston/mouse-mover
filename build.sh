#!/bin/bash
# Build Mouse Mover into a standalone app
# Usage: ./build.sh
#
# Mac:     Builds, signs, notarizes, and zips → dist/MouseMover.zip
# Windows: Builds → dist/MouseMover.exe

set -e

DEVELOPER_ID="Developer ID Application: William Alston (AYZ9SP42W8)"
TEAM_ID="AYZ9SP42W8"
BUNDLE_ID="com.williamalston.mousemover"

echo "Installing dependencies..."
pip install -r requirements.txt

echo ""
echo "Building Mouse Mover..."

if [[ "$OSTYPE" == "darwin"* ]]; then
    pyinstaller \
        --name "Mouse Mover" \
        --windowed \
        --clean \
        --osx-bundle-identifier "$BUNDLE_ID" \
        mouse-mover-gui.py

    APP="dist/Mouse Mover.app"

    echo ""
    echo "Cleaning resource forks and dot-underscore files..."
    dot_clean "$APP"
    find "$APP" -name '._*' -delete

    echo "Fixing Python.framework structure..."
    # macOS requires embedded frameworks to have a proper structure:
    # only Versions/ and symlinks at the top level — no loose files
    PYFW="$APP/Contents/Frameworks/Python.framework"
    if [ -d "$PYFW" ]; then
        # Remove anything that isn't a symlink or the Versions directory
        find "$PYFW" -maxdepth 1 -not -name "Versions" -not -name "Python" \
            -not -name "Resources" -not -path "$PYFW" -exec rm -rf {} \;
    fi

    echo "Signing all binaries inside the app..."

    # Sign every .so, .dylib, and framework binary inside the bundle
    find "$APP" -type f \( -name "*.so" -o -name "*.dylib" \) -exec \
        codesign --force --options runtime --sign "$DEVELOPER_ID" --timestamp {} \;

    # Sign the Python framework binary if present
    find "$APP" -path "*/Python.framework/Versions/*/Python" -exec \
        codesign --force --options runtime --sign "$DEVELOPER_ID" --timestamp {} \;

    # Sign the Python.framework as a whole
    if [ -d "$PYFW" ]; then
        codesign --force --options runtime --sign "$DEVELOPER_ID" --timestamp "$PYFW"
    fi

    # Sign the main executable
    codesign --force --options runtime --sign "$DEVELOPER_ID" --timestamp \
        "$APP/Contents/MacOS/Mouse Mover"

    # Sign the whole .app bundle
    codesign --deep --force --options runtime \
        --sign "$DEVELOPER_ID" \
        --timestamp \
        "$APP"

    echo "Verifying signature..."
    codesign --verify --verbose=2 --deep "$APP"

    echo ""
    echo "Zipping for notarization..."
    cd dist
    rm -f MouseMover.zip
    /usr/bin/ditto -c -k --keepParent "Mouse Mover.app" MouseMover.zip
    cd ..

    echo ""
    echo "Submitting for notarization (this may take a few minutes)..."
    xcrun notarytool submit dist/MouseMover.zip \
        --keychain-profile "notary-profile" \
        --wait

    echo ""
    echo "Stapling notarization ticket..."
    xcrun stapler staple "$APP"

    echo ""
    echo "Re-zipping with stapled ticket..."
    cd dist
    rm -f MouseMover.zip
    /usr/bin/ditto -c -k --keepParent "Mouse Mover.app" MouseMover.zip
    cd ..

    echo ""
    echo "Done! Signed + notarized. Upload to GitHub Release:"
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
