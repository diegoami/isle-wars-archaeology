# sourced by probe.sh: wait for the option box by pixels, capture it twice, then close the window.
P="python3 $HERE/pred.py"
ok=""
for i in $(seq 600); do import -window root -depth 8 rgb:- 2>/dev/null | $P menu && { ok=1; break; }; sleep 0.2; done
echo "menu ${ok:-timeout} t=$(echo "$(date +%s.%N) - $T0" | bc)" >> "$OUT/shots.txt"
grab before
sleep 1
grab before2
[ -n "${SAVE:-}" ] && { hk s; sleep 2; grab postsave; }
xdotool windowkill $W
