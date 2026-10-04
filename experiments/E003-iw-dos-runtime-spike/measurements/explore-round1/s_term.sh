# sourced: at the menu, try the game's own keys, then DOSBox-X's own ways out
sleep 22
W=$(xdotool search --class dosbox | head -1)
xdotool getwindowgeometry $W > "$OUT/geom.txt"
eval $(xdotool getwindowgeometry --shell $W)
xdotool mousemove $((X + 320)) $((Y + 200))
grab before
for k in ${KEYS:-Escape}; do
  xdotool key $k; sleep 3
  grab "k_$k"
  if kill -0 $DB 2>/dev/null; then echo "$k: alive" >> "$OUT/term.txt"; else echo "$k: exited" >> "$OUT/term.txt"; break; fi
done
if kill -0 $DB 2>/dev/null; then
  case "${HOW:-term}" in
    term) t0=$(date +%s.%N); kill -TERM $DB; wait $DB; echo "SIGTERM status $? after $(echo "$(date +%s.%N) - $t0" | bc)" >> "$OUT/term.txt";;
    hostq) hk ${HQ:-q}; sleep 3; kill -0 $DB 2>/dev/null && echo "host+${HQ:-q}: alive" >> "$OUT/term.txt" || { wait $DB; echo "host+${HQ:-q}: exited $?" >> "$OUT/term.txt"; };;
    close) xdotool windowkill $W; sleep 3; kill -0 $DB 2>/dev/null && echo "windowkill: alive" >> "$OUT/term.txt" || { wait $DB; echo "windowkill: exited $?" >> "$OUT/term.txt"; };;
  esac
else wait $DB; echo "game exit: dosbox status $?" >> "$OUT/term.txt"; fi
