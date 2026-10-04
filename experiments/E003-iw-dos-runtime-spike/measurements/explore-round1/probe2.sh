#!/bin/bash
# exploration only (not a record); runs inside unshare -rmpfn --mount-proc --kill-child
set -u
EX=<EXPLORE>
OUT=$EX/out/${TAG:-q1}
rm -rf "$OUT"; mkdir -p "$OUT"
mount -t tmpfs -o mode=1777 tmpfs /tmp
mkdir -p /tmp/.X11-unix <TMPHOME> /tmp/w/cap /tmp/w/save
chmod 1777 /tmp/.X11-unix
export HOME=<TMPHOME> XDG_CONFIG_HOME=<TMPHOME>/.config DISPLAY=:77 SDL_AUDIODRIVER=dummy
Xvfb :77 -screen 0 ${SCREEN:-640x350x24} -nolisten tcp >/dev/null 2>&1 &
for i in $(seq 50); do xdpyinfo >/dev/null 2>&1 && break; sleep 0.1; done
cat > /tmp/w/dosbox.conf <<CONF
[sdl]
fullscreen=false
output=surface
autolock=${AUTOLOCK:-false}
mouse_emulation=${MOUSEEMU:-integration}
mapperfile=/tmp/w/mapper.map
[dosbox]
captures=/tmp/w/cap
savefile=/tmp/w/save/state.sav
saveremark=false
synchronize time=false
${EXTRA_DOSBOX:-}
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
${PREMOUNT:-}
mount c $EX/game
c:
${PRE:-}
${GAME:-ISLEWAR}
exit
CONF
cd /tmp/w
dosbox-x -conf /tmp/w/dosbox.conf -nogui -nomenu -fastlaunch -nopromptfolder ${ARGS:-} > "$OUT/dosbox.log" 2>&1 &
DB=$!
hk() { xdotool keydown F12; sleep 0.15; xdotool keydown $1; sleep 0.15; xdotool keyup $1; sleep 0.15; xdotool keyup F12; }
grab() { import -window root -depth 8 rgb:"$OUT/$1.rgb"; convert -size $(xdpyinfo | awk '/dimensions/{print $2}') -depth 8 rgb:"$OUT/$1.rgb" "$OUT/$1.png"; }
if [ -n "${SCRIPT:-}" ]; then source "$SCRIPT"; else
for i in $(seq ${SHOTS:-10}); do sleep ${STEP:-2}; grab s$i; done
fi
for w in $(xdotool search --class dosbox 2>/dev/null); do xdotool getwindowname $w; xdotool getwindowgeometry $w; done >> "$OUT/wid.txt" 2>&1
cp /tmp/w/dosbox.conf "$OUT/"
ls -laR /tmp/w <TMPHOME> > "$OUT/files.txt" 2>&1
cp -r /tmp/w/cap /tmp/w/save "$OUT/" 2>/dev/null
kill $DB 2>/dev/null
sleep 1
