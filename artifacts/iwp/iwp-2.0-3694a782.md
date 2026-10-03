# iwp-2.0-3694a782: Isle Wars Pro 2.0 (unregistered), with its runtime write declared

The manifest is the second entry of [`../known.json`](../known.json). This set is
[`iwp-2.0-996e86c5`](iwp-2.0-996e86c5.md) with one change: `xtras/Isledft.dat` is declared in
`runtime_writes`, so it is left out of `files` and a copy that differs only there is the same artifact.
Hashes and sizes only; the bytes stay on the user's machines (U2).

- **Why it exists**: E001 ([F002](../../findings/F002-iwp-runtime-wine-xvfb.md)) saw the game change
  `xtras/Isledft.dat` from 15 to 16 bytes when the Save as default button of the Options screen was
  clicked. No other arm of E001 changed a file of the set.
- **Shipped content of the declared file**: 15 bytes, sha256
  `1750f915ae4ea473d6b21493b7fe3d289fe45f2ea0d779f3cce3c40c309550df`, as listed in the first set.
- **Runs that use it**: only runs whose action may write that file (the save-default arm of E001). Runs that
  cannot write it name the first set.
- **Check a copy**: `python3 tools/register_artifact.py check <dir> iwp-2.0-3694a782`; the two uninstaller
  files, if present, are `unlisted:` and still pass.
