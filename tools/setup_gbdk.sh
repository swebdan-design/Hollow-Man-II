#!/bin/sh
# Downloads GBDK-2020 4.3.0 (Linux x64) into ./toolchain/gbdk and prints the GBDK_HOME to use.
set -e
DEST="${1:-toolchain}"
mkdir -p "$DEST"
URL=https://github.com/gbdk-2020/gbdk-2020/releases/download/4.3.0/gbdk-linux64.tar.gz
echo "Downloading $URL"
curl -sSL -o "$DEST/gbdk.tar.gz" "$URL"
tar xzf "$DEST/gbdk.tar.gz" -C "$DEST"
rm "$DEST/gbdk.tar.gz"
echo "Done. Build with:  make GBDK_HOME=$DEST/gbdk"
