#!/bin/bash
# Exploration, round 2 (not a run record). Usage: probe.sh TAG [VAR=value ...]
#   IW_DOS_DIR  the copy (read only; bound read-only here too)
#   OUTROOT     machine-local output folder, outside every checkout
# Runs DOSBox-X in private user, mount, PID and network namespaces, from a copy of the game made
# on the namespace's own tmpfs (nothing of the game is written anywhere else), and sources
# STEPS (a script of xdotool steps) once the window exists. VARs: CYCLES, ARGS (extra DOSBox-X
# flags), PRE (autoexec lines before the game), GAME (default ISLEWAR), EXTRA (extra config lines).
set -u
TAG=$1; shift
for kv in "$@"; do export "$kv"; done
HERE=$(cd "$(dirname "$0")" && pwd)
OUT=$OUTROOT/$TAG
mkdir -p "$OUT"
export OUT HERE
exec timeout "${TMO:-150}" unshare -rmpfn --mount-proc --kill-child bash -c '
set -u
mount --bind "$IW_DOS_DIR" "$IW_DOS_DIR" && mount -o remount,bind,ro "$IW_DOS_DIR"
mount -t tmpfs -o mode=1777 tmpfs /tmp
mkdir -p /tmp/.X11-unix /tmp/w/h /tmp/w/cap /tmp/w/save /tmp/w/game
cp -p "$IW_DOS_DIR"/* /tmp/w/game/
chmod 644 /tmp/w/game/*
export HOME=/tmp/w/h XDG_CONFIG_HOME=/tmp/w/h/.config DISPLAY=:61 SDL_AUDIODRIVER=dummy
Xvfb :61 -screen 0 800x600x24 -nolisten tcp >/dev/null 2>&1 &
for i in $(seq 100); do xdpyinfo >/dev/null 2>&1 && break; sleep 0.1; done
cat > /tmp/w/dosbox.conf <<CONF
[sdl]
fullscreen=false
output=surface
autolock=false
mouse_emulation=never
mapperfile=/tmp/w/mapper.map
[dosbox]
captures=/tmp/w/cap
savefile=/tmp/w/save/state.sav
saveremark=false
quit warning=false
synchronize time=${SYNC:-true}
${EXTRA:-}
[cpu]
cycles=${CYCLES:-fixed 3000}
[mixer]
nosound=true
[speaker]
pcspeaker=false
[sblaster]
sbtype=none
[gus]
gus=false
[midi]
mpu401=none
mididevice=none
[serial]
serial1=disabled
serial2=disabled
serial3=disabled
serial4=disabled
[parallel]
parallel1=disabled
parallel2=disabled
parallel3=disabled
[printer]
printer=false
[ipx]
ipx=false
[ne2000]
ne2000=false
[dos]
startcmd=false
automountall=false
[autoexec]
mount c /tmp/w/game
${PRE:-}
c:
${GAME:-ISLEWAR}
exit
CONF
cd /tmp/w
T0=$(date +%s.%N)
dosbox-x -conf /tmp/w/dosbox.conf -nogui -nomenu -fastlaunch -nopromptfolder ${ARGS:-} > "$OUT/dosbox.log" 2>&1 &
DB=$!
grab() { import -window root -depth 8 rgb:"$OUT/$1.rgb"; echo "$1 $(sha256sum < "$OUT/$1.rgb" | cut -c1-16) t=$(echo "$(date +%s.%N) - $T0" | bc)" >> "$OUT/shots.txt"; }
hk() { xdotool keydown F12; sleep 0.15; xdotool keydown $1; sleep 0.15; xdotool keyup $1; sleep 0.15; xdotool keyup F12; }
for i in $(seq 100); do W=$(xdotool search --class dosbox 2>/dev/null | head -1); [ -n "$W" ] && break; sleep 0.1; done
echo "window ${W:-none} t=$(echo "$(date +%s.%N) - $T0" | bc)" >> "$OUT/shots.txt"
[ -n "${STEPS:-}" ] && source "$STEPS"
for w in $(xdotool search --class dosbox 2>/dev/null); do xdotool getwindowname $w; xdotool getwindowgeometry $w; done >> "$OUT/wid.txt" 2>&1
cp /tmp/w/dosbox.conf "$OUT/"
ls -la --time-style=+%H:%M:%S /tmp/w/game /tmp/w/cap /tmp/w/save /tmp/w/h > "$OUT/files.txt" 2>&1
(cd /tmp/w/game && sha256sum * > "$OUT/game.sha256")
cp -r /tmp/w/cap /tmp/w/save "$OUT/" 2>/dev/null
if kill -0 $DB 2>/dev/null; then echo "dosbox alive at end; SIGKILL" >> "$OUT/shots.txt"; kill -KILL $DB; fi
wait $DB; echo "dosbox status $?" >> "$OUT/shots.txt"
'
