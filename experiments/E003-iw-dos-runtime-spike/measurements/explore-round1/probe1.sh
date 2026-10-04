#!/bin/bash
# exploration only (not a record); runs inside unshare -rmpfn --mount-proc --kill-child
set -u
EX=<EXPLORE>
OUT=$EX/out/${TAG:-p1}
rm -rf "$OUT"; mkdir -p "$OUT"
mount -t tmpfs -o mode=1777 tmpfs /tmp
mkdir -p /tmp/.X11-unix <TMPHOME> /tmp/w/cap
chmod 1777 /tmp/.X11-unix
export HOME=<TMPHOME> XDG_CONFIG_HOME=<TMPHOME>/.config DISPLAY=:77 SDL_AUDIODRIVER=dummy
cat /proc/net/dev > "$OUT/net.txt"
Xvfb :77 -screen 0 1024x768x24 -nolisten tcp >/dev/null 2>&1 &
for i in $(seq 50); do xdpyinfo >/dev/null 2>&1 && break; sleep 0.1; done
cat > /tmp/w/dosbox.conf <<CONF
[sdl]
fullscreen=false
output=surface
mapperfile=/tmp/w/mapper.map
[mixer]
nosound=true
[dosbox]
captures=/tmp/w/cap
${EXTRA_DOSBOX:-}
[cpu]
cycles=${CYCLES:-fixed 3000}
[autoexec]
mount c $EX/game
c:
${PRE:-}
${GAME:-ISLEWAR}
exit
CONF
cd /tmp/w
dosbox-x -conf /tmp/w/dosbox.conf -nogui -nomenu -fastlaunch -nopromptfolder ${ARGS:-} > "$OUT/dosbox.log" 2>&1 &
DB=$!
if [ -n "${SCRIPT:-}" ]; then source "$SCRIPT"; else
for i in $(seq ${SHOTS:-10}); do
  sleep ${STEP:-2}
  import -window root "$OUT/s$i.png" 2>/dev/null
done
fi
xdotool search --class dosbox > "$OUT/wid.txt" 2>&1
for w in $(xdotool search --class dosbox 2>/dev/null); do xdotool getwindowname $w; xdotool getwindowgeometry $w; done >> "$OUT/wid.txt" 2>&1
cp /tmp/w/dosbox.conf "$OUT/"
ls -laR /tmp/w <TMPHOME> > "$OUT/files.txt" 2>&1
cp -r /tmp/w/cap "$OUT/cap" 2>/dev/null
kill $DB 2>/dev/null
sleep 1
