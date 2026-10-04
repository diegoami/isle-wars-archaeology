# iwp-2.0-de5a82a2: Isle Wars Pro 2.0 (unregistered), with its two runtime writes declared

The manifest is the third entry of [`../known.json`](../known.json). This set is
[`iwp-2.0-3694a782`](iwp-2.0-3694a782.md) with one more change: `xtras/Islepro.skr` is declared in
`runtime_writes` beside `xtras/Isledft.dat`, so both are left out of `files` and a copy that differs only
in them is the same artifact. Hashes and sizes only; the bytes stay on the user's machines (U2).

- **Why it exists**: E002 ([F003](../../findings/F003-iwp-observable-state-inventory.md)) saw the game
  change `xtras/Islepro.skr` from 13 to 14 bytes when a game was left in the middle with fewer than 10
  countries held (the scoreboard credits a loss). The first set already declared `xtras/Isledft.dat`, the
  file the Save as default button rewrites.
- **Shipped content of the declared files**: `xtras/Isledft.dat`, 15 bytes, sha256
  `1750f915ae4ea473d6b21493b7fe3d289fe45f2ea0d779f3cce3c40c309550df`; `xtras/Islepro.skr`, 13 bytes, sha256
  `50d86c5cdd758f4c65f21e2a2be78da433b39c96e4fefd1549820a68abb25b95`. Both are listed in
  [`iwp-2.0-996e86c5`](iwp-2.0-996e86c5.md).
- **Runs that use it**: runs whose action may click Save as default or credit a loss (every `opt-*` and
  `loss-*` arm of E002, and its `tour` arm). Runs that cannot write either file name an earlier set.
  `xtras/Islepro.dat` was written in no arm of E001 or E002, and stays a shipped file of the set.
- **Check a copy**: `python3 tools/register_artifact.py check <dir> iwp-2.0-de5a82a2`; the two uninstaller
  files, if present, are `unlisted:` and still pass.
