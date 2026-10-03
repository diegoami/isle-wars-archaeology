# F004 DOS Isle Wars's own documents state version 3.1, and its executable is a PKLITE-packed DOS MZ program with seven overlay files, five of them starting with a PCX-style header

- **Status**: proposed
- **Question**: What version does the DOS Isle Wars artifact state for itself, and what do its executable, its overlay files and its archive dates say about what it is, so that later claims name the right artifact?
- **Tests claims**: none (identity facts; they feed W2b and W3b)
- **Experiment and runs**: none
- **Artifact**: set `iw-dos-3.1-30121376`, variant none
- **Basis**: `doc` (the game's own documents, read in place) and `static:bytes` (header and string reads; nothing decompiled, I1)
- **Max intervention**: I0
- **Tier reached**: V0 (files read in place; the game was not run)
- **Confidence**: not applicable as an outcome until review; the facts are direct reads of text and of header bytes, one reader, no run

## Answer

- The game's own documents give its version as 3.1: `ISLEWAR.DOC` lines 6 and 11 ("v3.1", "Version 3.1  Apr 1994"), `FILE_ID.DIZ` line 1 and `ISLE_REG.DOC` line 1. The label `iw-dos-3.1` rests on those lines.
- `ISLEWAR.EXE` is a DOS MZ executable (signature `MZ` at `0x0`) packed with PKLITE (the string "PKLITE Copr. 1990-92 PKWARE Inc. All Rights Reserved" at `0x1e`). No compiler or overlay-manager signature is visible, because the program is packed.
- Of the seven overlay files, `ISLEWAR.OV0`, `.OV1`, `.OV2`, `.OV3` and `.OV5` start with a PCX-style image header (the first four describe 640x350, the fifth 156x258), `ISLEWAR.OV6` is a second PKLITE-packed MZ executable, and `ISLEWAR.OV4` has no recognised header.
- The fourteen files that make up the game are all dated 1994-04-01 12:00 in the archive; three files, likely a later packager's additions, are dated July 1997. These are dates of the files. They are not a release date, and this finding does not settle the release year.
- The only unregistered-version limit a document states is that the registered version "greatly speeds up the loading and exiting" of the program (`ISLEWAR.DOC:370-371`, `ISLE_REG.DOC:8-9`).

## Method

Artifact: set `iw-dos-3.1-30121376` ([`artifacts/known.json`](../artifacts/known.json), [`artifacts/iw-dos/iw-dos-3.1-30121376.md`](../artifacts/iw-dos/iw-dos-3.1-30121376.md)), the shareware (unregistered) archive `islewr31.zip` downloaded on 2026-10-03 from the third-party archive dosgames.com (`https://dosgames.com/files/islewr31.zip`) and extracted with `unzip` into a read-only directory on the user's machine. The copy may differ from Soleau Software's own distribution.

No runtime and no run. The documents were read in place with `sed`/`grep -n`; line numbers below are lines of those files as stored (CRLF text; the line numbers count `\n`). A short Python 3 script, kept outside the repository, opened each binary read-only and unpacked its header fields with `struct`; strings were located with `strings -t x` and `grep -b`. Offsets are file offsets, in hexadecimal. Nothing was copied out of the copy, and no file was written to it.

## Observations

Documents (line numbers):

| File | Line | What it states |
| --- | --- | --- |
| `ISLEWAR.DOC` | 5-6 | the title "ISLE WARS GAME" and "v3.1" |
| `ISLEWAR.DOC` | 9-10 | "Programed by William Soleau" and "(c) 1991" |
| `ISLEWAR.DOC` | 11 | "Version 3.1  Apr 1994" |
| `ISLEWAR.DOC` | 14 | requirements: EGA graphics and a mouse |
| `ISLEWAR.DOC` | 17-20 | "Files Needed": `.ov0` to `.ov6`, `.dat` and `.jft` (of `Islewar`) |
| `ISLEWAR.DOC` | 26-27 | the player plays Blue and the computer plays the other three |
| `ISLEWAR.DOC` | 344-347 | a note that running the game from Windows may cause unexpected results |
| `ISLEWAR.DOC` | 365 | the game is distributed as Shareware |
| `ISLEWAR.DOC` | 370-371 | the registered version "greatly speeds up the loading and exiting of the program" |
| `ISLE_REG.DOC` | 1 | "ISLE WARS   v3.1  :  REGISTRATION FORM" |
| `ISLE_REG.DOC` | 7, 8-9 | the $15.00 fee; the registered version speeds loading and exiting |
| `FILE_ID.DIZ` | 1 | "ISLE WARS   v3.1  Requires EGA/VGA & MOUSE" |

Other documents: `CATALOG.TXT` line 1 reads "As of August 1997" and line 308 describes Isle Wars; `OMBUDSMN.TXT` is an Association of Shareware Professionals ombudsman notice; `AVEXTRA.TXT` is a contact notice; `SOLSOFT.DOC` is the publisher's notice and game list (its line 65 calls Blind Wars "this sequel to Soleau Software's popular Isle Wars").

`ISLEWAR.EXE` (83580 bytes), MZ header, 14 little-endian words at `0x0`:

| Offset | Field | Value |
| --- | --- | --- |
| `0x0` | signature | `MZ` |
| `0x2`, `0x4` | bytes in last page, pages | `0x7c`, `0xa4`; (164-1)*512 + 124 = 83580, the file size |
| `0x6` | relocation entries | 1 |
| `0x8` | header size, paragraphs | 6 (96 bytes) |
| `0xa`, `0xc` | min, max extra paragraphs | `0x110c`, `0xffff` |
| `0xe`, `0x10` | initial SS, SP | `0x1468`, `0x0200` |
| `0x12` | checksum | 0 |
| `0x14`, `0x16` | initial IP, CS | `0x0100`, `0xfff0` |
| `0x18` | relocation table offset | `0x52` |
| `0x1a` | overlay number | 0 |
| `0x1c` | word before the PKLITE text | `0x310f` |
| `0x1e` | "PKLITE Copr. 1990-92 PKWARE Inc. All Rights Reserved" | 52 bytes, ends at `0x51`, the byte before the relocation table |
| `0x78` | "Not enough memory" | the packer's stub message, in readable text |

`ISLEWAR.OV6` has the same layout (same CS:IP, same text at `0x1e`). The only readable text of six letters or more in the executable is that signature and the stub message; everything else `strings` prints is short byte noise, because the code and data are packed. The task's "any compiler or overlay-manager signature found by reading strings" is therefore: none found; the only tool named is PKLITE.

Overlay files (first bytes and header fields):

| File | Bytes | Start | Fields |
| --- | --- | --- | --- |
| `ISLEWAR.OV0` | 38948 | `0a 05 01 01` | PCX-style header: window 0,0 to 639,349 at `0x4`; planes 4 at `0x41`; bytes per line 80 at `0x42`; palette type 1 at `0x44` |
| `ISLEWAR.OV1` | 32588 | `0a 05 01 01` | same fields; the header's filler bytes hold the text "LE\ISLEWAR.OV1" from `0x46` |
| `ISLEWAR.OV2` | 53522 | `0a 05 01 01` | same fields |
| `ISLEWAR.OV3` | 33798 | `0a 05 01 01` | same fields |
| `ISLEWAR.OV4` | 2292 | `f3 ef ec f3` | no recognised header |
| `ISLEWAR.OV5` | 11455 | `0a 05 01 01` | PCX-style header: window 0,0 to 155,257; planes 4; bytes per line 20 |
| `ISLEWAR.OV6` | 58688 | `4d 5a 40 01` | MZ: bytes in last page `0x140`, pages `0x73` (114*512 + 320 = 58688, the file size); header 8 paragraphs; initial CS:IP `fff0:0100`; the word at `0x1c` is `0x210f`; "PKLITE Copr. 1990-92 PKWARE Inc. All Rights Reserved" at `0x1e`; "Not enough memory" at `0x98` |

In the PCX-style header the first four bytes are manufacturer `0x0a`, version 5, encoding 1 (RLE), 1 bit per pixel, followed by the window as four words at `0x4`, and the 16-entry colour palette at `0x10` whose bytes (`0x10` to `0x3f`) take the values `0x00`, `0x55`, `0xaa`, `0xdc` and `0xff` in all five files. The words at `0xc` and `0xe` read 300 and 300 in all five.

Readable fragments inside the packed `ISLEWAR.OV6`: "FINALS" at `0x314`, "PRINTF" at `0x1a82`, "SINPUT" at `0x20f5`. They are short and the file is packed; no tool is inferred from them.

Data files: `ISLEWAR.DAT` (2048 bytes) is ASCII text of comma-separated decimal numbers with CRLF line ends (it starts "19,96,29,136,30" and its only other bytes are CR, LF and space). `ISLEWAR.JFT` (8738 bytes) starts `0c 00 01 00 fe 00`, holds 6205 zero bytes, and has no recognised header.

Archive file dates (`unzip -l` and `unzip -Z`, zip times are local and unzoned):

| Dates | Files |
| --- | --- |
| 1994-04-01 12:00 | `ISLEWAR.EXE`, `.OV0` to `.OV6`, `.DAT`, `.JFT`, `.DOC`, `ISLE_REG.DOC`, `SOLSOFT.DOC`, `FILE_ID.DIZ` (14 files) |
| 1997-07-23 10:30 | `AVEXTRA.TXT` |
| 1997-07-24 21:24 | `CATALOG.TXT` |
| 1997-07-28 13:31 | `OMBUDSMN.TXT` |

The publisher's archived DOS page (`sources/web-soleau-dos-games.md`, T05) heads its entry "ISLE WARS v3.1" with the size "206kb". The dosgames.com page links the archive as "DOWNLOAD 212k"; the archive is 216924 bytes and its 17 files total 379611 bytes unpacked.

## Inferences

- From `ISLEWAR.DOC:6, :11`, `FILE_ID.DIZ:1`, `ISLE_REG.DOC:1` and the publisher's page: three documents of this archive and the publisher's own listing call the game v3.1. The label belongs to the documents, so a different build with the same documents would carry the same label; the set's hash tells them apart.
- From the MZ header and the PKLITE text (`ISLEWAR.EXE:0x0`, `:0x1e`): the program is a DOS real-mode executable packed with PKLITE. This is why no library or compiler string is readable. The compiler is unknown.
- From `ISLEWAR.DOC:17-20` and the file names: the seven overlay files, `.DAT` and `.JFT` are the files the program needs. No string in the executable shows how it loads them, because the executable is packed. The one in-file reference found is the path fragment "…LE\ISLEWAR.OV1" inside `ISLEWAR.OV1`'s header filler (`0x46`); it reads as residue of the tool that wrote the image, and is not shown to be a reference by the program.
- From the PCX-style header (`ISLEWAR.OV0:0x0` to `0x44`): `.OV0` to `.OV3` are 640x350 images with four 1-bit planes, a 16-colour picture at the size of the EGA 640x350 mode, which fits `ISLEWAR.DOC:14` (EGA graphics). That the files are used as screens is not shown; the files were not decoded. "PCX-style" is used because the byte layout matches the PCX header; the format was not otherwise confirmed.
- From `ISLEWAR.OV6:0x0` and `:0x1e`: `.OV6` is a second MZ executable, packed with the same tool. What it does is unknown.
- From the dates: the fourteen game files share one time to the minute, 12:00, although their kinds differ (programs, images, data, documents). A tool probably set one time on all of them; the date therefore reads as a packaging date, and it agrees in month and year with "Apr 1994" in `ISLEWAR.DOC:11`. It does not show that the files were built on that day.
- From `CATALOG.TXT:1` ("As of August 1997") and the 1997 dates of the three files: those three files were made in 1997 or later, so they were not in a 1994 package. Who added them to this archive is unconfirmed.
- From `ISLEWAR.DOC:370-371` and `ISLE_REG.DOC:8-9`: the unregistered version loads and exits more slowly than the registered one, in the author's words. What else registration unlocks is not stated for this game, and is `unknown`.

## Alternatives considered

- The version is something other than 3.1 because the document is stale: not excluded for the executable, whose strings are packed; excluded for the archive's three version statements and the publisher's page, which agree. The game may show its version on screen (W3b).
- The 1994 dates are the release date: not excluded and not supported. They are file dates, they are identical, and `ISLEWAR.DOC:10` says "(c) 1991" for the game as a whole. The knowledge map's year rows (1994 and 1991, both `unknown`) stay as they are.
- The three 1997 files belong to the publisher's package: not excluded; probably they do not (the dates, and `CATALOG.TXT:1`). They stay in the set so that the id can be reproduced from the zip.
- `ISLEWAR.OV1`'s path fragment is the program's own reference to the file: not excluded; not shown either.

## What this does not establish

- Anything about Isle Wars Pro; this finding is scoped to DOS Isle Wars (CLAUDE.md rule 19). `ISLEWAR.DOC:344-347` says Windows may cause unexpected results; it is not shown whether DOSBox-X is affected.
- The release year of version 3.1, the first release of the game, or whether the copy equals Soleau Software's own release (the source is a third-party archive).
- The compiler, the overlay mechanism, the roles of `ISLEWAR.OV4`, `ISLEWAR.OV6`, `ISLEWAR.DAT` and `ISLEWAR.JFT`, and whether the game writes any file. W3b measures runtime writes; the manifest's `runtime_writes` is `[]` because nothing has been observed.
- What the images show, the game's rules, or any behaviour; the game was not run and nothing was decoded.
- What registration unlocks beyond `ISLEWAR.DOC:370-371`.

## Where the evidence is

None beyond the committed manifest in [`artifacts/known.json`](../artifacts/known.json) and [`artifacts/iw-dos/iw-dos-3.1-30121376.md`](../artifacts/iw-dos/iw-dos-3.1-30121376.md). No run, so no evidence manifest or bundle.

## Reproduction

The bytes stay on the user's machine. With the extracted archive in `IW_DOS_DIR`, `python3 tools/register_artifact.py check "$IW_DOS_DIR" iw-dos-3.1-30121376 --strict` confirms the files are the ones read. The MZ fields are the standard 28-byte header (14 little-endian words at `0x0`); the PCX-style fields are at `0x0` to `0x44` as listed. The dates come from `unzip -Z islewr31.zip`.
