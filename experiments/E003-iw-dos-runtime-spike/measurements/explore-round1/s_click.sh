# sourced by probe1.sh: wait for the menu, capture, click DEFAULT, capture
sleep 22
W=$(xdotool search --class dosbox | head -1)
xdotool getwindowgeometry $W > "$OUT/geom.txt"
import -window $W -depth 8 rgb:"$OUT/before.rgb"
# DOSBox-X's own capture: host key + p
xdotool keydown F12; sleep 0.15; xdotool keydown p; sleep 0.15; xdotool keyup p; sleep 0.15; xdotool keyup F12
sleep 1
eval $(xdotool getwindowgeometry --shell $W)
xdotool mousemove $((X + ${CX:-133})) $((Y + ${CY:-32}))
sleep 0.5
import -window $W -depth 8 rgb:"$OUT/hover.rgb"
xdotool click 1
sleep 3
import -window $W -depth 8 rgb:"$OUT/after.rgb"
import -window $W "$OUT/after.png"
import -window $W -depth 8 rgb:"$OUT/after2.rgb"
xdotool keydown F12; sleep 0.15; xdotool keydown p; sleep 0.15; xdotool keyup p; sleep 0.15; xdotool keyup F12
sleep 1
xdotool keydown F12; sleep 0.15; xdotool keydown s; sleep 0.15; xdotool keyup s; sleep 0.15; xdotool keyup F12
sleep 3
ls -la /tmp/w <TMPHOME> >> "$OUT/files2.txt" 2>&1
find / -xdev -newer /tmp/w/dosbox.conf -name "*.sav" 2>/dev/null >> "$OUT/files2.txt"
