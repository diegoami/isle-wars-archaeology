# F010 Isle Wars Pro is a Director 7.0 projector whose 213 Lingo scripts decompile with their handler names, and its SaveDefaults handler writes `Isledft.dat` as eight comma-ended fields in the order F003 observed; the DOS executable is a PKLITE 1.15 file packed with the extra and large settings (its unpacking, import and probe are not in this draft)

- **Status**: proposed
- **Question**: Can both executables be unpacked, loaded and read with open tools (U32, static first), what do the tools recover, and does a static reading agree with what the runs of F003, F007 and F009 observed? (T26, E008.) Feasibility probes: the code that writes `ISLEWAR.SAV` (DOS) and the handler that writes `Isledft.dat` (Pro).
- **Tests claims**: R001 to R007 (Pro, `Isledft.dat` and `Islepro.skr`; static agreement and, for R004 and R007, a static reading of what the runs left unknown). The DOS claims R009 to R024 (F007, F009) are not tested in this draft.
- **Experiment and runs**: E008 (static only; no run). Its measurements are in `experiments/E008-static-triage/measurements/`.
- **Artifact**: set `iwp-2.0-996e86c5` for Pro (`Islepro.exe`, sha256 `c4d7a248646454adeb48232e3ac7b3d2c0f08b290051a79d6fe6e47bb76b594e`, 7150739 bytes, the same file in all three registered Pro sets); set `iw-dos-3.1-30121376` for DOS (`ISLEWAR.EXE`, sha256 `88e934bb4fa0b074a926d53765bbca251cb38395da50337276aac7d08a5cde45`, 83580 bytes). Variant none.
- **Max intervention**: I0 (the originals were only read, in place; every derived file is a new file in a folder outside every checkout)
- **Tier reached**: V0 (static)
- **Confidence**: Pro, the layout, the counts and the probe: high, because the counts come from the tool's own chunk reading and the probe's field order is read directly from a short handler (the determinism of the output is for the re-run of Done-when 2 to show). It rests on one decompiler (ProjectorRays 0.2.0) and no run corroborates a *behaviour* (the offsets agree with F003, which is a corroboration of the file layout only). DOS packer: about 90%, on the header's PKLITE text and version bytes read as a published description gives them; nothing has unpacked the file yet.

## Answer

### Pro

- **`Islepro.exe` is a Director projector for Windows with one embedded Director movie.** A PE image of 162816 bytes (ends at file offset 0x27c00) is followed by a projector header `PJ00`, which points at a Director container (`APPL`) at offset 0x1b8ce8. The container's chunk map has 23 chunks: itself, an initial map, the map, a list, a dictionary and 18 embedded files. Seventeen are not Director files (their first bytes are neither `MZ` nor `XFIR`; not identified here) and one is the movie, 4522178 bytes at offset 0x281bce, codec `MV93`. `static:experiments/E008-static-triage/measurements/iwp-extract-pro-r1.json`, field `layout` and `embedded_files`, binary sha256 above.
- **ProjectorRays 0.2.0 reads the movie and reports Director 7.0.** It reads 1504 chunks, 650 cast members (389 bitmaps, 121 scripts, 57 text, 19 sounds, 2 shapes, and 62 of types 14 and 15, which the tool does not name) and writes the movie back as a 4687621-byte `.dir`. The projector's own map says version field 1406; the tool maps the movie's own config value to 7.0. `static:experiments/E008-static-triage/measurements/iwp-extract-pro-r1.json`, field `movies[0]`.
- **213 scripts and 230 handlers decompile, names intact.** 34 movie scripts, 87 behaviour scripts and 92 cast-member scripts, 7358 lines of decompiled text (counted, not kept here), with no error marker in any. Handler names survive (`SaveDefaults`, `Getdefaults`, `MakeComputerMove`, `Computerattack`, `RollDice`, `CheckCardMatch` and so on; the table of all of them is in the record), and so do global and local variable names. The script context lists 274 scripts; the 61 that no cast member points at are not written by the tool and were not read. `static:experiments/E008-static-triage/measurements/iwp-extract-pro-r1.json`, fields `scripts`, `script_count`, `handler_count`, `scripts_without_a_cast_member`.
- **Probe: `SaveDefaults` (script `MovieScript 458 - getdefaults`, cast member 458) writes `xtras\Isledft.dat`.** It builds one string of eight items, each followed by a comma: first the four opponent flags (`opp`, `1` or `0` each), then the speed, the frequency, the starting armies and the strength, in that order, then writes the string with the file Xtra. The reader `Getdefaults` (same script) takes items 1 to 4 as the four flags, item 5 as speed, 6 as frequency, 7 as starting armies and 8 as strength, and falls back to 2, 2, 3 and 2 for a zero. The button script `CastScript 602 - SAVEDEFAULT2` calls `SaveDefaults` on mouse down. `static:decompile`, `Islepro.exe` sha256 above, `MovieScript 458` handlers `Getdefaults` and `SaveDefaults`, `CastScript 602`.
- **The static reading agrees with F003 and answers two of its open rows.** See the table in Observations: eight comma-ended items (R001), speed at offset 8 (R002), level at offset 14 (R003), and the six items F003 never saw change, whose meanings the reader gives (R004: flags at offsets 0, 2, 4 and 6, frequency at offset 10, starting armies at offset 12). For the scoreboard file `Islepro.skr`, the writer `writescores` adds the won and lost counts to a pair of items chosen by the level (items 5 and 6 at level 1, 3 and 4 at level 2, 1 and 2 at level 3), then writes seven items each followed by a comma, after adding the constant 94 (0x5e) to the code of every character (`CIPHER`, `MovieScript 480 - checkupg`). That agrees with R005 and R006, and it answers R007's untested idea (offset 2 is the lost count of level 3, which F003 calls EASY). `static:decompile`, `MovieScript 455`, `MovieScript 480`.
- **The start handler explains the shipped files.** On every start `startMovie` (`MovieScript 1`) creates each of `Islepro.dat`, `Islepro.skr` and `Isledft.dat` that is missing; for `Isledft.dat` it writes the eight items without the last comma (15 bytes, the shipped size, R001), for `Islepro.skr` seven items of zero (13 bytes, the shipped size). `SaveDefaults` and `writescores` append a comma after the last item, which is the 16 and 14 bytes F003 saw after a write. `static:decompile`, `MovieScript 1`, `MovieScript 455`, `MovieScript 458`.
- **Why the locked controls never moved.** `Getdefaults` resets the opponent flags, the frequency and the starting armies to their defaults when the global `UPG` is 0. F003 found these controls locked in the unregistered build and no run could change those items. That is the reason the six items stayed unchanged, read from code and not shown by a run. `static:decompile`, `MovieScript 458`, handler `Getdefaults`, last block.

### DOS

- **`ISLEWAR.EXE` is a PKLITE 1.15 executable, with the extra-compression and large-codebook flags.** The MZ header has 164 pages, one relocation, initial CS:IP `fff0:0100`, and 96 header bytes; the PKLITE text sits at offset 30 and the version bytes at offsets 28 and 29 read `0f 31`. Read as the PKLITE format notes give them, that is version 1.15, flag 0x10 (extra) and flag 0x20 (large), copyright years 1990-92. `static:experiments/E008-static-triage/measurements/dos-identify-r1.json`, binary sha256 above. Confidence about 90%: the evidence is the header and the published description; nothing has unpacked the file.
- **Ghidra 12.1.4 loads the packed file as an old-style DOS executable in 16-bit real mode and finds one function.** The import exits 0 (the whole run took 4.28 s), with 81 instructions, a code block `1000:0000` of 83484 bytes and a data block `2000:461c` of 69824 bytes (the compressed data). That is the packed stub, not the game. `static:experiments/E008-static-triage/measurements/ghidra-dos-packed-r1.json`.
- **The compiler, the import of the unpacked image, the function count and the `ISLEWAR.SAV` probe are not established in this draft** (the unpacker is the missing step: see "What this does not establish").

### Per area: can this source answer it? (estimates, not claims, rule 22)

| Area | DOS Isle Wars | Isle Wars Pro | Why (Pro; `static:experiments/E008-static-triage/measurements/iwp-extract-pro-r1.json`, `scripts`) |
| --- | --- | --- | --- |
| Setup | not estimated: the file is not unpacked | about 90%: yes | `Getdefaults`, `SaveDefaults` and the option-button scripts (`startingnumarmybehavior`, `FREQbehavior`, `SPEEDbehavior`, `STRENGTHbehavior`) |
| Players | not estimated | about 85%: yes | the flag list in `Getdefaults`, `HumanH` and `ComputerC` cast scripts |
| Map and topology | not estimated | about 75%: probably | `startMovie` holds 12 long numeric list lines, and `BehaviorScript 400`'s `mouseDown` (401 lines) mentions adjacency; which lists are the map was not read |
| Starting state, turn sequence | not estimated | about 85%: yes | `Newgame`, `Putinboard`, `WHOGOESFIRST`, `CheckTurn` |
| Reinforcement and resources, bonuses (cards) | not estimated | about 85%: yes | `CheckNumberofArmies` (287 lines), `GetvalidArmys`, `CheckCardMatch`, `PUTINCARDS`, `SELECTACARD`, `Reordercards` |
| Movement, combat, ownership change | not estimated | about 85%: yes | `RollDice`, `ATTACKHIM`, `mouseDown` scripts of the board |
| Production centres, hazards | not estimated | about 80%: yes | `Putinproductioncenters`, `addtoproductioncenter`, `putinflood`, `putinrebellion` (an earthquake handler was not named; it may be inside another) |
| AI | not estimated | about 80%: yes, the area where static-first pays most | `computerplacearmies` (903 lines), `MakeComputerMove` (315), `ComputerRollDice` (285), `Computerattack` (186), `CompCheckCardMatch`, `CompCards`; whether the decompiled text is faithful needs a corroborating run |
| Randomness | not estimated | about 55%: partly | the scripts show where a random number is drawn and how it is used; the generator itself is inside Director's runtime, not in the Lingo |
| Victory, loss, surrender | not estimated | about 80%: yes | `Lostit`, `writescores`, the `reset2` cast script |
| User interface (layout, timing, feedback) | not estimated | about 45%: behaviour yes, layout and look only in part | the 62 `mouseDown` and 39 `mouseUp` handlers give behaviour; the picture, positions and tempo are in cast members and the score (`VWSC`), which this tool does not decode |
| Registration (what it unlocks; how a code is entered) | not estimated | about 80%: what the unregistered build gates, yes | the global `UPG`, `CHECKUPG`, `WRITEUPG`; this reading is not a licence-check study and none is planned |
| In-game text | not estimated | about 70%: yes for text in scripts and fields | 57 text members and the string literals; the text members were not extracted here |

## Method

- **Artifact and tools.** The two executables were read in place, after each was hashed and matched to its registered sha256 (`tools/static/static_common.py`, `original`). Tools and their identities are in `docs/environment.md`, "Static analysis tools", and `setup/static/tools.json`: ProjectorRays 0.2.0 (commit 8a3d3b4, built from source, binary sha256 `d1c2235bd5f32f4a268a2cd09d2260e143b8caf51124e0da8d9f54fd113c0ea3`), Ghidra 12.1.4 PUBLIC with JDK Temurin 21.0.12.1+1-LTS, and the scripts under `tools/static/`. The version word of PKLITE is read as Entropymine's notes describe it.
- **Pro.** `tools/static/iwp_extract.py` reads the PE image end, the `PJ00` header and the container's chunk map, carves the movie, and gives ProjectorRays a work copy that keeps the movie at its original file offset (the first 44 bytes at offset 0, the movie again at its offset, zeros between): the movie's internal offsets are those of the executable, and ProjectorRays reads them as offsets in the file it is given. It then runs `decompile --dump-scripts -v` and a second run with `--dump-json`, and counts. `--probe NAME` lists the handlers that mention a file name and whether each reads or writes a file. The probe's field order was read from the decompiled handlers in the machine-local folder; nothing of it is kept here. Run `pro-r1`; the record is `iwp-extract-pro-r1.json`.
- **DOS.** `tools/static/dos_identify.py` reads the MZ header and the PKLITE version word in place (`dos-identify-r1.json`). `tools/static/ghidra_import.py` imports the file with `analyzeHeadless -processor "x86:LE:16:Real Mode" -cspec default` and the post-script `tools/static/ghidra/T26Report.java` (`ghidra-dos-packed-r1.json`). Ghidra ran on the packed original in place.
- **What is tracked.** Hashes, sizes, counts, addresses and identifier names. The carved movie, the work copy, the rebuilt `.dir`, the decompiled scripts and Ghidra's project stay in a folder outside every checkout (rule 18). `tools/static/check_derived_hashes.py` checks that no tracked file is one of them.

## Observations

### Pro, the probe against F003

| Item of the string | Offset in the file | Static reading (`Getdefaults`, `SaveDefaults`) | F003 and the spec rows |
| --- | --- | --- | --- |
| 1 to 4 | 0, 2, 4, 6 | the four opponent flags `opp`; default `1,0,0,0` | R004: unchanged in every run, meaning unknown; the screen's defaults match (F003 P4) |
| 5 | 8 | speed; default 2 | R002: offset 8 is the speed, 1 FAST, 2 NORMAL, 3 SLOW |
| 6 | 10 | frequency; default 2 | R004 (F003: "not tested and not claimed") |
| 7 | 12 | starting armies; default 3 | R004 (as above); the screen's default is 3 starting armies |
| 8 | 14 | strength, the level; default 2 | R003: offset 14 is the starting level, 1 HARD, 2 NORMAL, 3 EASY |
| after each item | | a comma, so 16 bytes; the start handler writes the eight items without the last comma | R001: the shipped file is 15 bytes, a write leaves 16 |

### Pro, other numbers

- Container: 23 chunks (18 `File`, 1 each of `RIFX`, `imap`, `mmap`, `List`, `Dict`), file lengths 14752 to 4522178 bytes; the `File` chunk of the movie says 4522177 bytes and the movie's own length field 4522178.
- Movie chunks by kind: `BITD` 389, `CASt` 650, `Lscr` 274, `STXT` 57, `XMED` 56, `snd ` 19 (with `sndH`, `sndS` 19 each), others 1 or 2 (the record's `chunks_by_kind`).
- Scripts by kind: `MovieScript` 34, `CastScript` 92, `BehaviorScript` 87; no `ParentScript`. Handlers: 230, of which `exitFrame` 77, `mouseDown` 62, `mouseUp` 39.
- Largest handlers by decompiled lines: `computerplacearmies` 903, `mouseDown` of `BehaviorScript 400` 401, `MakeComputerMove` 315, `CheckNumberofArmies` 287, `ComputerRollDice` 285.
- Ghidra on the packed DOS file: 1 function, 81 instructions, 3 memory blocks.

## Inferences

- The projector can be read with open tools and the Lingo comes back as readable source with names: from the counts and the absence of error markers in `iwp-extract-pro-r1.json`. That the *behaviour* the source describes is what the game does is not shown by this reading; F003's offsets agreeing is the one corroboration, and it covers a file layout.
- The offsets and order agree with F003 on every row F003 had (R001 to R003, R005, R006), from the table above and the `writescores` reading. Two independent methods (runs, and a static reading) now name offsets 8 and 14 the same, which is the independence `vocabulary/basis.md` asks for before `corroborated`.
- The six items that no run could move are the opponent flags, the frequency and the starting armies, from the reader's own naming and its reset when `UPG` is 0. That `UPG` is 0 in the unregistered build is a reading of the start handler and was not observed.
- A static answer to R007's untested idea (offset 2 is a lost count) exists in the writer's pairing of items with levels; no run produced an Easy loss, so this is the one place a run is still owed, if the claim is to be promoted.
- DOS: the file is packed with a known packer; whether the unpacked image shows a compiler or runtime, and whether the order of the `ISLEWAR.SAV` fields can be read from it, is unknown here.

## Alternatives considered

- **The decompiler invented the handler order or the names.** Not excluded by a second decompiler (only ProjectorRays 0.2.0 was used). Made unlikely by the names being the movie's own name table (`Lnam`), by 213 scripts decompiling without an error marker, and by the order of items agreeing with F003 at offsets 8 and 14.
- **The scripts that no cast member points at (61) hold the real write.** The probe's handler is in a script a cast member points at, and its output agrees with the runs, so excluded for this file; for any other question the 61 are unread.
- **The agreement with F003 is by construction (the same defaults).** Excluded for offsets 8 and 14 (the runs changed them and the reader says which item they are) and not excluded for the default values, which both sources could take from the same shipped file.
- **For DOS, the PKLITE reading is a coincidence of bytes.** Not excluded until an unpacker returns an image; the signature text, the copyright years and the header's initial CS:IP are the usual shape of a PKLITE file.

## What this does not establish

- **Nothing about the DOS game's code.** The unpacked image, its compiler or runtime, the Ghidra function count after unpacking and the `ISLEWAR.SAV` probe (and so the comparison with F007 and F009) are not done in this draft. The step that stopped is installing a PKLITE unpacker (the permission to fetch and build one was refused in the implementer's session). A missing tool is a step to finish, never a reason to fall back to runs (U32).
- **Any game rule.** The area estimates are estimates. No handler was read to learn a rule, and none is claimed.
- **The registered builds, the other Pro sets, other versions**, and what registration unlocks beyond what the unregistered build's code gates.
- **The 61 scripts without a cast member, the 17 other embedded files, the cast members' pictures and text, the score (`VWSC`) and the sounds.** Counted or ignored, never read.
- **That the decompiled Lingo is faithful in every handler.** One decompiler, no corroborating run for any behaviour.
- **Ghidra's and the JDK's archives.** Both were installed by the owner; their files are identified by hash, and the archives' published checksums were not compared (Ghidra's is recorded as published).

## Where the evidence is

- Measurements, all tracked: `experiments/E008-static-triage/measurements/iwp-extract-pro-r1.json`, `dos-identify-r1.json`, `ghidra-dos-packed-r1.json`. No evidence bundle and no run record exist (no run was made). Everything derived from an original is in a machine-local folder and recorded by sha256 and size.

## Reproduction

On the machine that has the originals and the tools (`python3 setup/static/check_tools.py` prints `ready`), in a clean clone:

```bash
IWA_STATIC=<folder outside every checkout> IWP_DIR=<the Pro install> \
  python3 tools/static/iwp_extract.py --run <id> --probe Isledft.dat --probe Islepro.skr
IW_DOS_DIR=<the DOS copy> python3 tools/static/dos_identify.py
IWA_STATIC=<folder> IW_DOS_DIR=<the DOS copy> python3 tools/static/ghidra_import.py --original iw-dos --run <id>
python3 tools/static/check_derived_hashes.py
```

The extraction should print 213 scripts and 230 handlers, and the carved movie's sha256 and the rebuilt `.dir`'s should equal those in `iwp-extract-pro-r1.json`.
