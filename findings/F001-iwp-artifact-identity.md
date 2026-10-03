# F001 Isle Wars Pro's own document states version 2.0, and its executable is an i386 Macromedia Director 7.0.2r85 projector with three Xtras

- **Status**: proposed
- **Question**: What version does the Isle Wars Pro artifact state for itself, and what do its executable and Xtras say they are, so that later claims name the right artifact?
- **Tests claims**: none (identity facts; they feed W2a and W3a)
- **Experiment and runs**: none
- **Artifact**: set `iwp-2.0-996e86c5`, variant none
- **Max intervention**: I0
- **Tier reached**: V0 (files read in place; the game was not run)
- **Confidence**: not applicable as an outcome until review; the facts are direct reads of a document and of header and resource bytes, one reader, no run

## Answer

- The game's own document gives its version as 2.0 (`Islepro.txt` line 2). The label `iwp-2.0` rests on that line only.
- `Islepro.exe` is a PE32 image for i386 (machine type `0x014c`, at offset `0xcc`), linked 1999-05-23 23:32:34 UTC (timestamp `0x37489012`, at offset `0xd0`).
- The version resource inside `Islepro.exe` describes Macromedia Director Player 7.0.2r85, not the game. It is recorded here and is not the game's version.
- The install has three Xtras (`DTTurnTable.x32`, `FileIo.x32`, `PMatic.x32`), each a PE32 i386 DLL (machine type at `0xe4`, `0xc4` and `0x84` respectively; PE32 magic and DLL flag in the table under Observations) whose internal strings name the Xtra.

## Method

Artifact: set `iwp-2.0-996e86c5` ([`artifacts/known.json`](../artifacts/known.json)), an unregistered install made by the user on 2026-10-02 from an installer downloaded from a third-party mirror (myabandonware.com, game page `isle-wars-pro-ovz`). The copy may differ from Soleau Software's own distribution. The installer's own sha256 is not recorded.

No runtime and no run. A short Python 3 script, kept outside the repository, opened each file read-only and read the DOS header's `e_lfanew` (offset `0x3c`), the COFF header, the optional header's section table, the resource directory and the version resource; strings were located by exact byte search (UTF-16-LE in the version resource, ASCII in the Xtras). Offsets below are file offsets. Nothing was copied out of the install.

## Observations

Document (`Islepro.txt`, sha256 `f1e71098a0fb83c17891ed7a5d95acd0a129e1a0712cba3e8148f70c5ca7b4b7`):

| Line | What it states |
| --- | --- |
| 1 | the title, "ISLE WARS PRO GAME DIRECTIONS" |
| 2 | "Version 2.0" |
| 3 | the author, "by Soleau Software, Inc." |
| 21-23, 66-67 | in the unregistered version the player plays Blue and the computer plays the other three opponents |
| 221-224 | the registered version allows up to four human players |

`Islepro.exe` (sha256 `c4d7a248646454adeb48232e3ac7b3d2c0f08b290051a79d6fe6e47bb76b594e`, 7150739 bytes):

| Offset | Field | Value |
| --- | --- | --- |
| `0x0` | DOS signature | `MZ` |
| `0x3c` | `e_lfanew` | `0xc8`; `PE\0\0` there |
| `0xcc` | COFF machine | `0x014c` (i386) |
| `0xce` | number of sections | 4: `.text`, `.rdata`, `.data`, `.rsrc` |
| `0xd0` | COFF `TimeDateStamp` | `0x37489012` = 1999-05-23 23:32:34 UTC |
| `0xde` | COFF characteristics | `0x010f` (executable image, 32-bit machine; the DLL bit `0x2000` is not set) |
| `0xe0`, `0xe2` | optional header magic and linker version | magic `0x10b` (PE32), linker 5.10 |
| `0x124`, `0x110` | subsystem, subsystem version | 2 (Windows GUI), 4.0 |
| `0x24c`, `0x248` | `.rsrc` section header: raw data pointer and raw size | `0x1a800` and `0xd400`; their sum, `0x27c00`, is the first byte after the last section's raw data |
| `0x27c00` to end of file | bytes after the last section | 6987923 bytes (file size 7150739, from the filesystem); not decoded here |
| `0x25be8` | start of the version resource (1748 bytes, from its resource data entry) | see below |
| `0x25c10` | `VS_FIXEDFILEINFO` signature `0xfeef04bd` | present |
| `0x25c18` | its file version (two DWORDs) | 7.0.2.85 |
| `0x25c20` | its product version (two DWORDs) | 7.0.2.85 |

The version resource strings (UTF-16-LE, two identical blocks; first block offsets):

| String name | Value | Offset |
| --- | --- | --- |
| CompanyName | Macromedia, Inc. | `0x25ca0` |
| FileDescription | Director Player | `0x25cec` |
| FileVersion | 7.0.2r85 | `0x25d2c` |
| InternalName | OTTO | `0x25d60` |
| OriginalFilename | Otto.exe | `0x25ee4` |
| ProductName | Macromedia Director | `0x25f18` |
| ProductVersion | 7.0.2 | `0x25f64` |

Xtras. Each starts with `MZ` at `0x0`. PE header fields, as file offsets (`e_lfanew` is read at `0x3c`; the machine type is at `e_lfanew + 4`):

| File | `e_lfanew` | Machine type | Characteristics | Optional header magic |
| --- | --- | --- | --- | --- |
| `xtras/DTTurnTable.x32` | `0xe0` | `0x014c` at `0xe4` | `0x210e` at `0xf6` (DLL bit `0x2000` set) | `0x10b` at `0xf8` |
| `xtras/FileIo.x32` | `0xc0` | `0x014c` at `0xc4` | `0x210e` at `0xd6` (DLL bit set) | `0x10b` at `0xd8` |
| `xtras/PMatic.x32` | `0x80` | `0x014c` at `0x84` | `0x210e` at `0x96` (DLL bit set) | `0x10b` at `0x98` |

Link timestamps and name strings:

| File | sha256 | PE link timestamp (offset) | Name strings (offset) |
| --- | --- | --- | --- |
| `xtras/DTTurnTable.x32` | `7634fe4328290980898ced48bbb6547d0147a2c0f4555aa5ce09b772e6518c12` | `0x38333d08` = 1999-11-17 23:40:56 UTC (`0xe8`) | "DTTURNTABLE.x32" (`0xc00a`), "DirectTransition Xtra" (`0xd04c`), "Turn Table" (`0xd150`) |
| `xtras/FileIo.x32` | `61c9f235459a10dd44e5fe76f48c39e55124bb758fe100b298971d97cf1e4f57` | `0x37489058` = 1999-05-23 23:33:44 UTC (`0xc8`) | "FILEIO.x32" (`0x485a`), "FileIO for Director 7.0.2.r85 (May 23 1999)" (`0x4bfc`) |
| `xtras/PMatic.x32` | `ba707c9c395c41baec327f0bb1d8b7aa9dffcaf50165befe76c0eaed773a628e` | `0x37e92b8e` = 1999-09-22 19:18:38 UTC (`0x88`) | "PrintOMatic Xtra" (`0x38f4f`) |

The `DTTurnTable.x32` and `PMatic.x32` binaries also hold strings saying an unregistered copy of that Xtra prints a notice or does not work; those belong to the Xtras' own licensing, not to the game's (`0xd1a4` in `DTTurnTable.x32`, `0x38f36` in `PMatic.x32`).

File dates in the install are filesystem metadata, not a field in any file: `Islepro.exe` is dated 2012-07-04 and `Islepro.txt` 2012-07-01; the Xtras are dated 1999-2002 (read-only listing, 2026-10-02).

## Inferences

- From `Islepro.txt` line 2: the vendor's own document calls this build version 2.0. The version belongs to the document, so a different build with the same document text would carry the same label; the id's hash is what tells them apart.
- From the version resource (`FileDescription` at `0x25cec`, `InternalName` at `0x25d60`, `OriginalFilename` at `0x25ee4`): the executable is a Director 7.0.2 projector, and the bytes after the last section (observed above) would be the game's content. This is the usual Director layout, not shown here; the appended region is not decoded. The link timestamp (1999-05-23) is older than the file date (2012-07-04), which fits a projector shell built in 1999 around content added later.
- From the link timestamp of `FileIo.x32` (`0xc8`, 1999-05-23, 70 seconds after the projector's at `0xd0`) and its string "May 23 1999" (`0x4bfc`): the projector shell and FileIO come from the same Director 7.0.2r85 release.
- From the machine type `0x014c` (`0xcc`) and the PE32 magic `0x10b` (`0xe0`): the game executable is a 32-bit x86 program, as a 32-bit Windows game would be.

## Alternatives considered

- The version is 7.0.2: the PE resource says so. Excluded by the resource's own text (Director Player, Macromedia, `Otto.exe`), which names a different product.
- The version is something other than 2.0 because the document is stale (it is dated 2012-07-01, three days before the executable): not excluded. The executable's own game version string has not been located; W3a may see it on screen.
- The link timestamp is the date of the game: excluded in part; it equals the Director Player's build date, so it dates the projector shell, not the game content. Whether the 2012 file date is the game's build date is not excluded.

## What this does not establish

- Anything about DOS *Isle Wars*; this finding is scoped to Isle Wars Pro (CLAUDE.md rule 19).
- What registration changes beyond `Islepro.txt` lines 221-228, and whether the copy equals Soleau Software's own release (the source is a third-party mirror).
- The roles of `PMATIC.reg`, `Isledft.dat`, `Islepro.dat` and `Islepro.skr`, and whether the game writes any file. W3a measures runtime writes.
- The content appended to the projector, the game's rules, or any behaviour; the game was not run.

## Where the evidence is

None beyond the committed manifest in [`artifacts/known.json`](../artifacts/known.json) and [`artifacts/iwp/iwp-2.0-996e86c5.md`](../artifacts/iwp/iwp-2.0-996e86c5.md). No run, so no evidence manifest or bundle.

## Reproduction

The bytes stay on the user's machine. With the install directory in `IWP_DIR`, `python3 tools/register_artifact.py check "$IWP_DIR" iwp-2.0-996e86c5` confirms the files are the ones read. The offsets above are standard PE header and resource-directory fields: read `e_lfanew` at `0x3c`, then the COFF header, then the `.rsrc` directory for resource type 16 (version).
