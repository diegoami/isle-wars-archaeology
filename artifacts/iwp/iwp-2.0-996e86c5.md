# iwp-2.0-996e86c5: Isle Wars Pro 2.0 (unregistered)

The set's manifest is the entry in [`../known.json`](../known.json). This file says what each file
is and how to re-hash a copy. Hashes and sizes only; the bytes stay on the user's machines (U2).

- **Acquired**: user-supplied install, 2026-10-02. Installed from an installer the user downloaded
  from myabandonware.com (game page `isle-wars-pro-ovz`). That is a third-party mirror, so the copy
  may differ from Soleau Software's own distribution.
- **Version**: 2.0, as `Islepro.txt` line 2 states it. The projector's PE version resource says
  Director Player 7.0.2r85; that describes Director, not the game ([F001](../../findings/F001-iwp-artifact-identity.md)).
- **Left out of the set**: `unins000.exe` and `unins000.dat`, the Inno Setup uninstaller pair.
  `unins000.dat` records the install itself, so it would make the id depend on the machine.
- **Runtime writes**: none listed; this set is the files as shipped. W3a observed one runtime write, `xtras/Isledft.dat` (the Save as default button of the Options screen; [F002](../../findings/F002-iwp-runtime-wine-xvfb.md)), and declared it in the successor set [`iwp-2.0-3694a782`](iwp-2.0-3694a782.md).

## The files

The roles of the Xtras and data files come from their names and, for the Xtras, from the strings
in them (F001); a role marked "unconfirmed" is a guess from the name only.

| Path | Bytes | Role |
| --- | --- | --- |
| `Islepro.exe` | 7150739 | The game: a PE32 (i386) Macromedia Director projector (F001, header offsets `0xcc`, `0xe0`, version resource `0x25be8`). |
| `Islepro.txt` | 10572 | Document: the game directions, "Version 2.0" (line 2). |
| `Order.txt` | 3081 | Document: the Soleau Software order form (line 1). |
| `Isleord.url` | 58 | Installer shortcut to the vendor's order page (`URL=` on line 2). |
| `Islepro.url` | 47 | Installer shortcut to the vendor's home page (`URL=` on line 2). |
| `xtras/DTTurnTable.x32` | 61440 | Xtra: DirectTransition Xtra ("Turn Table" transition); strings at `0xd04c` and `0xd150`. |
| `xtras/FileIo.x32` | 25088 | Xtra: Macromedia FileIO; string at `0x4bfc`. |
| `xtras/PMatic.x32` | 351744 | Xtra: PrintOMatic (printing); string at `0x38f4f`. |
| `xtras/PMATIC.reg` | 19 | Data beside the PrintOMatic Xtra; unconfirmed: its registration record. |
| `xtras/Isledft.dat` | 15 | Game data, printable ASCII over its whole length; unconfirmed: default settings. Changed by the Save as default button (F002); see the successor set `iwp-2.0-3694a782`. |
| `xtras/Islepro.dat` | 190 | Game data, printable ASCII over its whole length; unconfirmed: scoreboard or settings. Candidate runtime write. |
| `xtras/Islepro.skr` | 13 | Game data, not text; role unknown. |

## Re-hash a copy on Windows

In PowerShell, set `$dir` to the install directory, then run the one-liner. It prints
`<sha256>  <bytes>  <relative/path>` lines, one per file, with no absolute path. It lists the two
uninstaller files too; `check` reports them as `unlisted:` and still passes. `ProviderPath` also
makes the one-liner work when `$dir` is a UNC path through `\\wsl.localhost\<distro>\…`, where
`Path` would give a provider-qualified string and break the relative path.

```powershell
$r=(Resolve-Path $dir).ProviderPath; gci -LiteralPath $r -Recurse -File | % { '{0}  {1}  {2}' -f (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLower(), $_.Length, $_.FullName.Substring($r.Length+1).Replace('\','/') }
```

Save the output to a file and check it against the set, from the repository:

```text
python3 tools/register_artifact.py check --list <that file> iwp-2.0-996e86c5
```

On a machine where the install is a directory, `python3 tools/register_artifact.py check <dir> iwp-2.0-996e86c5`
does the same. It exits 0 when every listed file matches; the only `unlisted:` lines are the two
uninstaller files.
