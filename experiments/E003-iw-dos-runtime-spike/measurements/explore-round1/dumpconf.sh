#!/bin/bash
set -u
EX=<EXPLORE>
mount -t tmpfs -o mode=1777 tmpfs /tmp
mkdir -p <TMPHOME> /tmp/w
export HOME=<TMPHOME> XDG_CONFIG_HOME=<TMPHOME>/.config SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy
cd /tmp/w
timeout 20 dosbox-x -nogui -nomenu -fastlaunch -c "config -all -wc full.conf" -c exit > "$EX/userconf.log" 2>&1
find /tmp/w <TMPHOME> -type f > "$EX/userconf.list"
cp /tmp/w/full.conf "$EX/full.conf"
