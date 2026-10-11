# The environment every Pro sitting needs (E004's variables). Copy it OUTSIDE every checkout,
# e.g. to ~/.local/share/isle-wars-archaeology/iwp-env.sh, adjust the paths, and `source` it
# before a launcher, tools/wine-driver.sh or run_walk.py. A copy in /tmp is convenient but a WSL
# restart wipes /tmp (2026-10-11): keep the master copy outside it.
export IWP_DIR="/mnt/c/Program Files (x86)/Solsoft/Isle Wars Pro Game"   # the install F019 pins
export IWP_PREFIX="$HOME/.local/share/isle-wars-archaeology/iwp.wineprefix"
export E019_BUNDLES="$HOME/.local/share/isle-wars-archaeology/E019-bundles"
export E020_BUNDLES="$HOME/.local/share/isle-wars-archaeology/E020-bundles"
export IWP_MACHINE=local
# E021 (Session A) also needs:
export E021_BUNDLES="$HOME/.local/share/isle-wars-archaeology/E021-bundles"
export E021_TEMPLATES="/mnt/c/Temp/iwp-shots/wine/reader-templates.json"
