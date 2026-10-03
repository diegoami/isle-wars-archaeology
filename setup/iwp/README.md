# setup/iwp/

The `iwp-runtime` bootstrap profile (W3a draft), for the Wine + Xvfb + xfwm4 path ([F002](../../findings/F002-iwp-runtime-wine-xvfb.md)).

- `iwp-runtime.sh`: idempotent; installs nothing and uses no sudo. Needs `IWP_PREFIX` (the Wine prefix, outside every checkout) and `IWP_DIR` (the install, read and hashed only). It checks the system packages and names the missing one, builds the prefix, removes `Z:` and the home-folder links, makes the game copy in the prefix equal to the registered set, and then runs every token check of [`capabilities.json`](../../capabilities.json). It prints `ready` and exits 0 only if all of them pass. Its exit code is never trusted on its own (game-archaeologist ADR-004).
- `prefix.py`: the prefix steps (`build`, `sync-game`, `strip-links`, `baseline`, `check`).
- `token_check.py`: the checks behind the `iwp` tokens. When the generic preflight (H3) lands, the script's last step becomes `preflight --tokens <the tokens of capabilities.json>`, the generic tokens move to it, and only `facility:iwp-prefix` stays here.
