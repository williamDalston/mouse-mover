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
        --onefile \
        --clean \
        --osx-bundle-identifier "$BUNDLE_ID" \
        mouse-mover-gui.py

    APP="dist/Mouse Mover.app"

    echo ""
    echo "Signing app..."
    codesign --deep --force --options runtime \
        --sign "$DEVELOPER_ID" \
        --timestamp \
        "$APP"

    echo "Verifying signature..."
    codesign --verify --verbose=2 "$APP"

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
