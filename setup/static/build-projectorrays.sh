#!/usr/bin/env bash
# Build ProjectorRays 0.2.0 from its tagged source into the tools folder (T26, U32). No sudo.
#
#   IWA_TOOLS   the tools folder (default $HOME/tools); it gets projectorrays-0.2.0/bin/projectorrays
#               and the unpacked build headers (boost-dev, mpg123-dev)
#
# Steps, each checked: download the two header packages with apt (no install) and compare each with
# its recorded sha256; unpack them below the tools folder; clone the source at its tag and compare the
# commit; build with make against those headers; copy the binary; print its sha256. Network: N3 (the
# Ubuntu archive and github.com). The binary links the system libmpg123.so.0 (the package
# libmpg123-0t64, which a desktop install already has). Never run it against an original.
set -eu
TOOLS=${IWA_TOOLS:-$HOME/tools}
COMMIT=8a3d3b4211575170276fc6be350b6b52e96d4750
BOOST_DEB_SHA=519ecf2c64308527e15b6582955681d192a832250baa4bc424967aaf7d02d68f
MPG_DEB_SHA=5fe2e9a221025ddd526baf2c2e3a0df5aacc8626f927d14fcb9585414a2d6d40
WORK=$TOOLS/src
mkdir -p "$WORK/debs" "$TOOLS/projectorrays-0.2.0/bin"

fetch() { # <package> <expected sha256> <unpack dir>
  (cd "$WORK/debs" && apt-get download "$1" >/dev/null)
  local deb
  deb=$(ls "$WORK"/debs/"$1"_*.deb)
  [ "$(sha256sum "$deb" | cut -d' ' -f1)" = "$2" ] || { echo "$1: the package is not the recorded one" >&2; exit 1; }
  dpkg-deb -x "$deb" "$3"
}
fetch libboost1.83-dev "$BOOST_DEB_SHA" "$TOOLS/boost-dev"
fetch libmpg123-dev "$MPG_DEB_SHA" "$TOOLS/mpg123-dev"
mkdir -p "$TOOLS/mpg123-dev/lib"
ln -sf /usr/lib/x86_64-linux-gnu/libmpg123.so.0 "$TOOLS/mpg123-dev/lib/libmpg123.so"

SRC=$WORK/ProjectorRays
[ -d "$SRC" ] || git clone -q --branch v0.2.0 --depth 1 https://github.com/ProjectorRays/ProjectorRays.git "$SRC"
[ "$(git -C "$SRC" rev-parse HEAD)" = "$COMMIT" ] || { echo "ProjectorRays: the checkout is not commit $COMMIT" >&2; exit 1; }
make -C "$SRC" release -j4 GIT_SHA=${COMMIT:0:7} \
  CPPFLAGS="-DVERSION_NUMBER=0.2.0 -DGIT_SHA=${COMMIT:0:7} -DRELEASE_BUILD -I$TOOLS/mpg123-dev/usr/include/x86_64-linux-gnu -I$TOOLS/boost-dev/usr/include" \
  LDFLAGS="-L$TOOLS/mpg123-dev/lib"
cp "$SRC/projectorrays" "$TOOLS/projectorrays-0.2.0/bin/projectorrays"
sha256sum "$TOOLS/projectorrays-0.2.0/bin/projectorrays"
echo "now: python3 setup/static/check_tools.py --only projectorrays (a rebuild with another compiler may differ in its sha256; compare the recorded one and say so)"
