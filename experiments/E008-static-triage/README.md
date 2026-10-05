# E008 static-triage

Copied from the research task's contract when the experiment was created. After the first
measurement this file is append-only. A changed design is a new experiment, or `v2/`.

- **Task**: T26 (#76). U32 (static first), game-archaeologist `9a224a3`, CLAUDE.md rule 24.
- **Question**: Can both executables be unpacked, identified and loaded with open tools, what do the tools recover, and does a static reading agree with what the runs of F003, F007 and F009 observed? Method: static only. No run of either game is made.
- **Hypotheses**:
  - H0: the originals cannot be read with open tools to the point of naming the writer of a file the game saves.
  - H1: for each artifact, an open tool recovers the program (the unpacked DOS image; the Lingo scripts of the Pro movie), and the code that writes a saved file can be found and its field order read.
- **Artifacts**: `iw-dos-3.1-30121376` (`ISLEWAR.EXE`), `iwp-2.0-996e86c5` (`Islepro.exe`). Variant none. Both are only read, in place, after their sha256 equals the registered one.
- **Tools**: Ghidra 12.1.4 headless, JDK Temurin 21, ProjectorRays 0.2.0, and a PKLITE unpacker; each with its version and sha256 in `docs/environment.md`, "Static analysis tools".
- **Design**:
  - DOS: identify the packer from the header; unpack into `$IWA_STATIC`; identify the compiler or runtime from the unpacked image; import into Ghidra as 16-bit real mode and count the functions; find the code that writes `ISLEWAR.SAV` from the references to its name, and compare the field order with F009.
  - Pro: extract the Director movie from the projector; decompile the Lingo; count scripts and handlers; find the handler that writes `Isledft.dat` and compare with F003 (R001 to R003).
  - for each knowledge-map area, a first estimate of whether this source can answer it.
- **Measurements**: hashes, sizes, counts, addresses and identifier names, as JSON records in `measurements/`. Every output derived from an original (the unpacked executable, the carved movie, the decompiled scripts, Ghidra's projects, the tools' logs) is written to `$IWA_STATIC`, a folder outside every checkout, and is never tracked (rule 18).
- **Outputs**: `findings/F010-static-triage-both-executables.md`, status `proposed`; `measurements/`.

## Scripts

All in `tools/static/`; each refuses to run when `IWA_STATIC` is unset or inside a checkout, and when an original does not match its registered sha256.

- `iwp_extract.py`: Pro. Carves the Director movie, runs ProjectorRays, counts, lists the handlers that mention a file name (`--probe`).
- `dos_identify.py`: DOS. Reads the MZ header and the PKLITE version word, in place.
- `ghidra_import.py`: either executable. Ghidra headless import and `ghidra/T26Report.java`.
- `check_derived_hashes.py`: no tracked file is an output whose hash a measurement lists.
- `static_common.py`: the refusals and the record writer.

## Measurements

- `measurements/iwp-extract-pro-r1.json`: Pro, run `pro-r1`: the projector's layout, the embedded files, the movie's chunks, cast members and scripts, the probe's hits.
- `measurements/dos-identify-r1.json`: DOS, the header and the PKLITE version word.
- `measurements/ghidra-dos-packed-r1.json`: DOS, Ghidra's import of the packed file (1 function: the stub).
- `measurements/done-when/`: the outputs of the Done-when lines.

A re-run writes new files beside these, never over them.
