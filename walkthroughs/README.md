# Walkthroughs — T28 C3 step and similar

A playbook for running the C3 (recorded-play) step of T28 (and future
T-stats) on the native Windows install, driven by the user on Windows and
orchestrated by the main session on WSL. The current Linux + Wine + namespace
path is blocked (the seal requires a read-only mount, which requires a user
namespace, which breaks Wine's connection to the X server on the user's
desktop). The native Windows path avoids all of that.

## The split

- **Windows side (you)**: runs the PowerShell poller, launches the game, and
  follows the walkthrough steps the main session posts.
- **WSL side (the main session)**: sends commands, receives screenshots and
  results, runs the per-question analysis, fills F020's per-claim section.

The two sides exchange data through a shared directory:
`C:\Temp\iwp-cmd\` (on Windows) and `/mnt/c/Temp/iwp-cmd/` (from WSL).

## Setup

### One-time (on Windows, in an elevated PowerShell)

```powershell
# Create the shared directory
New-Item -ItemType Directory -Path C:\Temp\iwp-cmd -Force | Out-Null
New-Item -ItemType Directory -Path C:\Temp\iwp-shots -Force | Out-Null

# Allow PowerShell to run unsigned scripts this session
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

### Per session (on Windows)

```powershell
# Copy the poller from the walkthroughs directory
Copy-Item -Path '\\wsl$\Ubuntu\home\diego\.local\share\isle-wars-archaeology\walkthroughs\iwp-poller.ps1' -Destination 'C:\Temp\iwp-poller.ps1' -Force

# Run the poller (this is a blocking job)
cd C:\Temp
.\iwp-poller.ps1
```

You should see:
```
iwp-poller watching C:\Temp\iwp-cmd (pid <number>)
```

### Per session (on WSL)

The main session connects via the file-based client at
`walkthroughs/iwp_client.py` — it writes `cmd-<uuid>.json` and reads
`result-<uuid>.json` from the shared directory. No TCP, no firewall, no
PowerShell async quirks.

## Commands the poller accepts

Each command is one JSON object per file, with a unique id in the filename:

| Command | Args | Effect |
| --- | --- | --- |
| `screenshot` | `path` | Captures the primary screen to `path` (Windows path). |
| `click` | `x, y, button` | Mouse click. `button` is `left` (default) or `right`. |
| `move` | `x, y` | Mouse move only. |
| `key` | `key` | SendKeys string (e.g. `Return`, `Escape`, `space`). |
| `wait` | `ms` | Sleep. |
| `find_window` | `title` | Returns `{hwnd, title, rect, visible}`. |
| `is_window` | `title` | Returns `{present: true/false}`. |
| `set_focus` | `hwnd` | Bring window to front. |
| `set_window_pos` | `hwnd, x, y, w?, h?` | Move/resize window. |
| `list_windows` | (none) | Returns all top-level windows. |
| `launch_game` | `path, x?, y?, w?, h?` | Start the game executable and optionally position it. |
| `shutdown` | (none) | Stop the poller. |

## A typical T28 F011 walkthrough

1. Main session on WSL calls `launch_game("C:\\Program Files (x86)\\Solsoft\\Isle Wars Pro Game\\Islepro.exe", x=1920, y=0, w=800, h=600)`.
   The game opens on the second monitor (or off-screen if there's no second monitor — the user can drag it).
2. Poller finds the "Islepro" window and returns its hwnd.
3. Main session calls `screenshot("C:\\Temp\\iwp-shots\\01-title.png")` to confirm the title screen.
4. Main session reads the F011 plan from `walkthroughs/f011-questions.md` and decides which game states to set up.
5. For each question:
   a. Start a new game: `click 100 585`, `click 565 532` (from the E002 tour).
   b. Wait for the board: `wait 4000`.
   c. Set up the position needed (play armies, attack/move).
   d. `screenshot` at each key state (board, battle, after-attack, after-pass).
   e. Post the screenshots back to the repo under `evidence/E018/combat/<run>/`.
6. When the C3 step is done for a batch, main session resumes the implementer
   to fill F020's F011 section and re-run the four Done-when checks.

## Coordinates (from E002 tour)

The game's stage is 800×600. The proven coordinate set from
`experiments/E002-iwp-state-inventory/scripts/tour.steps`:

| Action | Coordinates | Comment |
| --- | --- | --- |
| New Game (title) | `click 100 585` | |
| Play Game | `click 565 532` | |
| EASY level | `click 533 311` | |
| Place on a Blue country | `click-until 168 168 168 24 1000 <coords...>` | See `coordinates.md` for the 46-country list. |
| ALL | `click 307 543` | |
| PLACE | `click 497 543` | |
| ATTACK | `click 337 531` | |
| QUIT ATTACK / DONE | `click-until 0 192 64 16 600 456 531 495 540` | |
| PASS | `click 417 530` | |
| CONTINUE (after card) | `click-any? 402 531` | |

These are the **stage** coordinates. If the game window is positioned at
`(1920, 0)` on the desktop, the actual mouse positions are
`(1920 + stage_x, 0 + stage_y)`. The `set_window_pos` command with
`x=1920, y=0` puts the window at the top-left of the second monitor; the
E002 tour was recorded with the window at the stage's origin.

## What to leave out vs. do (per the owner's choice, 2026-10-07)

- **Human boundary tests** (Q-CMB-01/02/03): do all 16+7 cases. Play many
  games until the specific army-count positions come up naturally. Q-CMB-01
  (16 cases) and Q-CMB-02 (4 cases) can be hit in 10–30 games; Q-CMB-03
  (3 cases) usually within 5. The record uses the per-question count target
  from `f011-questions.md`.
- **Stack-size specifics** (Q-MOV-02, Q-OWN-01): try the small stacks (2, 3, 5).
  Stacks of 10+ are rare; mark those narrowed if not reached.
- **Q-CMB-12** (100 attacks per ratio band + 20 games where one seat never
  attacks): drop for now. The "never attacks" condition is rare. Static-only
  or narrowed in the per-claim section.

## What the per-question record looks like

The poller returns screenshots (PNG). The main session saves them at
`evidence/E018/combat/<run-id>/<state>.png` with a record at
`runs/E018/combat/<run-id>.json` shaped like:

```json
{
  "schema": "e018-record/1",
  "run_id": "E018-r0001",
  "experiment": "E018",
  "batch": "combat",
  "question_id": "Q-CMB-01",
  "claim_id": "C-CMB-01",
  "count_target": 16,
  "per_arm_counts": {},
  "screenshot_path": "C:\\Temp\\iwp-shots\\E018-r0001-after-attack.png",
  "screenshot_sha256": "<sha256>",
  "seal_ok": true,
  "elapsed_seconds": 12.3,
  "outcome": "pending",
  "status": "completed",
  "extra": {"attacker_armies": [2,4,8,12], "defender_armies": [1,3,5,6,10,14]}
}
```

The `outcome` and `per_arm_counts` are filled by the main session from the
screenshots. The poller only writes the structure; the analysis is the main
session's job (it has the per-arm count targets from the findings).

## What this playbook replaces

The recorder `experiments/E018-pro-corroboration/record_f011.py` from
PR #102 is a **scaffold** — its `_body` methods are stubs
(`wait_for_screen("title")` + a few `observe("static", ...)` calls). The
playbook replaces the recorder's stubs with the user-driven walkthroughs,
and the Python client is the lightweight glue.
