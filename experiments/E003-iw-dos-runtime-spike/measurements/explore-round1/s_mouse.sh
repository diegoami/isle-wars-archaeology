# sourced: wait for the menu, move onto SET LEVEL, capture, click, capture
sleep 22
W=$(xdotool search --class dosbox | head -1)
xdotool getwindowgeometry $W > "$OUT/geom.txt"
eval $(xdotool getwindowgeometry --shell $W)
grab before
xdotool mousemove $((X + ${CX:-60})) $((Y + ${CY:-32}))
sleep 1
grab hover
xdotool mousemove $((X + ${CX:-60} + 5)) $((Y + ${CY:-32} + 3))
sleep 1
grab hover2
xdotool click 1
sleep 3
grab after
