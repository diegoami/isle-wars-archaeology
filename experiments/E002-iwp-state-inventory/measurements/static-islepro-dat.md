# xtras/Islepro.dat, read in place and summarised (static, I1; no run)

Read on 2026-10-04 from the install, in place, read-only; the bytes are not copied anywhere. Only counts
are recorded. The file's sha256 and size are in the artifact manifest (`artifacts/known.json`, set
`iwp-2.0-996e86c5`) and in every run record's `xtras/Islepro.dat` observation.

Command (the install's folder is `$IWP_DIR`):

```text
python3 -c "import sys;b=open(sys.argv[1],'rb').read();print(len(b),sum(32<=x<127 for x in b),b.count(b','),len(set(b)),min(b),max(b))" "$IWP_DIR/xtras/Islepro.dat"
```

Output (length, printable ASCII bytes, commas, distinct byte values, smallest byte, largest byte):

```text
190 185 0 20 13 119
```

Reading: 185 of 190 bytes are printable ASCII, none is a comma, and 20 distinct byte values occur, so it
is not the comma-separated decimal text of `Isledft.dat`, and not the shifted form of `Islepro.skr` (its
bytes are 13 to 119, and 13 is the carriage-return byte). Its
meaning is not established here. It was written in no run of E001 or E002 (every `xtras/Islepro.dat`
observation says "equals the install's file: yes").
