# sourced by probe.sh: let the DOS shell print (exploration only, a fixed wait), capture the
# text screen, close the window.
sleep ${WAIT:-4}
grab text
convert -size 800x600 -depth 8 rgb:"$OUT/text.rgb" "$OUT/text.png"
xdotool windowkill $W
