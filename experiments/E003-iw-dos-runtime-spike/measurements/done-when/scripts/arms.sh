#!/bin/bash
# E003's probe arms, one run each (the debugger arm twice), through dw.sh.
D=$(dirname "$0")
a() { bash "$D/dw.sh" arm "$@" 2>&1 | grep -E '^\{|^exit|ABORT|png:|option box|reset:|exit status|equals|savestate|^\+'; }
a --arm clock-host --clock host
a --arm speed-max --cycles max
a --arm speed-30000 --cycles fixed-30000
a --arm savestate --probe savestate
a --arm debugger --probe memory
a --arm debugger --probe memory
a --arm dosbox-capture --probe dosbox-capture
a --arm term-kill --terminate kill
a --arm term-close --terminate close
