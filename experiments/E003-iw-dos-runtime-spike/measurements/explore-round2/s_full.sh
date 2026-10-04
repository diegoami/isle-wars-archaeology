# sourced by probe.sh: wait for the option box by pixels, capture twice, optionally save state,
# click Set level, wait for the dialog, optionally load state, then try TERMS (one way to stop).
P="python3 $HERE/pred.py"
ok=""
for i in $(seq 600); do import -window root -depth 8 rgb:- 2>/dev/null | $P menu && { ok=1; break; }; sleep 0.2; done
echo "menu ${ok:-timeout} t=$(echo "$(date +%s.%N) - $T0" | bc)" >> "$OUT/shots.txt"
grab before
sleep 1
grab before2
if [ -n "${SAVE:-}" ]; then hk s; sleep 2; grab postsave; ls -la /tmp/w/save >> "$OUT/save.txt"; fi
xdotool mousemove 140 132; sleep 0.5; grab hover
xdotool click 1
ok=""
for i in $(seq 100); do import -window root -depth 8 rgb:- 2>/dev/null | $P dialog && { ok=1; break; }; sleep 0.1; done
echo "dialog ${ok:-timeout} t=$(echo "$(date +%s.%N) - $T0" | bc)" >> "$OUT/shots.txt"
sleep 1
grab after
if [ -n "${SAVE:-}" ]; then hk l; sleep 3; grab restored; fi
if [ -n "${CAP:-}" ]; then hk p; sleep 1; fi
for t in ${TERMS:-}; do
  t1=$(date +%s.%N)
  case $t in
    term) kill -TERM $DB;;
    kill) kill -KILL $DB;;
    windowkill) xdotool windowkill $W;;
    *) hk $t;;
  esac
  for i in $(seq 150); do kill -0 $DB 2>/dev/null || break; sleep 0.1; done
  if kill -0 $DB 2>/dev/null; then echo "term $t: alive after 15 s" >> "$OUT/shots.txt"
  else echo "term $t: exited after $(echo "$(date +%s.%N) - $t1" | bc) s" >> "$OUT/shots.txt"; break; fi
done
