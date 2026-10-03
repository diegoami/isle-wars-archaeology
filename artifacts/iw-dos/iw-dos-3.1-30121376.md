# iw-dos-3.1-30121376: Isle Wars 3.1 (DOS shareware, unregistered), as acquired

The manifest is the third entry of [`../known.json`](../known.json). It lists every file of the archive
`islewr31.zip` as acquired, 17 files. Hashes and sizes only; the bytes stay on the user's machines (U2).
Facts about the files are in [F004](../../findings/F004-iw-dos-artifact-identity.md).

- **Version**: 3.1, as the game's own documents state it (`ISLEWAR.DOC:6` and `:11`, `FILE_ID.DIZ:1`,
  `ISLE_REG.DOC:1`). The label rests on those lines.
- **Source**: `https://dosgames.com/files/islewr31.zip`, linked from the game page
  `https://dosgames.com/game/isle-wars/` as "DOWNLOAD 212k"; downloaded and extracted with `unzip` on
  2026-10-03 at 22:35 UTC. The archive is 216924 bytes, sha256
  `9789a8569104607e46df3e9b1992d24d4fc285957cd6fbad8b9d7cb32eb82812`. dosgames.com is a third-party archive, so
  the copy may differ from Soleau Software's own distribution. The page calls the game "Shareware ($15)".
- **Release**: the shareware (unregistered) release. What registration unlocks is `unknown`, apart from the
  one difference the documents state, faster loading and exiting (see F004).
- **Runtime writes**: `[]`. Nothing has been observed; W3b measures it. `ISLEWAR.DAT` is an untested candidate.
- **Check a copy**: `python3 tools/register_artifact.py check <dir> iw-dos-3.1-30121376 --strict`. The `--strict`
  flag makes any file outside the manifest a failure; there is no uninstaller to excuse, because the set is
  an unpacked archive.

## Files and their roles

Sizes from the manifest. The role is read from the file's content or the document that names it; the
overlay row says what the bytes look like, not what the program does with them (see F004).

| File | Bytes | Role | Archive date |
| --- | --- | --- | --- |
| `ISLEWAR.EXE` | 83580 | program: a DOS MZ executable packed with PKLITE | 1994-04-01 12:00 |
| `ISLEWAR.OV0` | 38948 | overlay (`ISLEWAR.DOC:18-20` names `.OV0` to `.OV6`); starts with a PCX-style header, 640x350 | 1994-04-01 12:00 |
| `ISLEWAR.OV1` | 32588 | overlay; PCX-style header, 640x350 | 1994-04-01 12:00 |
| `ISLEWAR.OV2` | 53522 | overlay; PCX-style header, 640x350 | 1994-04-01 12:00 |
| `ISLEWAR.OV3` | 33798 | overlay; PCX-style header, 640x350 | 1994-04-01 12:00 |
| `ISLEWAR.OV4` | 2292 | overlay; no recognised header | 1994-04-01 12:00 |
| `ISLEWAR.OV5` | 11455 | overlay; PCX-style header, 156x258 | 1994-04-01 12:00 |
| `ISLEWAR.OV6` | 58688 | overlay; a second PKLITE-packed MZ executable | 1994-04-01 12:00 |
| `ISLEWAR.DAT` | 2048 | data: comma-separated decimal numbers as CRLF text; named by `ISLEWAR.DOC:20` | 1994-04-01 12:00 |
| `ISLEWAR.JFT` | 8738 | data: binary, no recognised header; named by `ISLEWAR.DOC:20` | 1994-04-01 12:00 |
| `ISLEWAR.DOC` | 17370 | document: the game directions | 1994-04-01 12:00 |
| `ISLE_REG.DOC` | 2290 | document: the registration form | 1994-04-01 12:00 |
| `SOLSOFT.DOC` | 6683 | document: the publisher's notice and game list | 1994-04-01 12:00 |
| `FILE_ID.DIZ` | 401 | document: a short description of the game (`FILE_ID.DIZ:1-10`) | 1994-04-01 12:00 |
| `AVEXTRA.TXT` | 336 | 1997-dated addition (provenance unconfirmed): contact notice | 1997-07-23 10:30 |
| `OMBUDSMN.TXT` | 2156 | 1997-dated addition (provenance unconfirmed): ASP ombudsman notice | 1997-07-28 13:31 |
| `CATALOG.TXT` | 24718 | 1997-dated addition (provenance unconfirmed): list of Soleau games, "As of August 1997" (`CATALOG.TXT:1`) | 1997-07-24 21:24 |

The three 1997-dated files are not among the "Files Needed" in `ISLEWAR.DOC:17-20`, and their archive
timestamps are three years after the others. Whether the publisher added them is unconfirmed. They are in the set anyway, so the id is reproducible from the same zip.

## What the archive dates show

- Fourteen files carry the same time, 1994-04-01 12:00, to the minute. The times are identical on files of
  different kinds; why is unknown.
- Three files carry 1997-07-23, 1997-07-24 and 1997-07-28 times.
- The times are local and unzoned (zip format), and they are dates of the files. They are not a release
  date. `ISLEWAR.DOC:11` says "Apr 1994" for the version, which agrees with the month of the fourteen
  files; the agreement does not show that the files were built that day.

## Re-hash

On any machine, the listing the check reads is `<sha256>  <bytes>  <relative/path>`. With Python:
`python3 tools/register_artifact.py check "$IW_DOS_DIR" iw-dos-3.1-30121376 --strict`.

On Windows, with `$dir` set to the copy (a path through `\\wsl.localhost\<distro>\…`, or a fresh extraction of
the same zip):

```powershell
$r=(Resolve-Path $dir).ProviderPath; gci -LiteralPath $r -Recurse -File | % { '{0}  {1}  {2}' -f (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLower(), $_.Length, $_.FullName.Substring($r.Length+1).Replace('\','/') }
```

Save the output to a file and run `python3 tools/register_artifact.py check --list <file> iw-dos-3.1-30121376`.
The output has 17 lines.
