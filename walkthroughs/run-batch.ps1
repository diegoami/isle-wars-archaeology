# run-batch.ps1 — PowerShell walkthrough runner for T28 C3 step.
# Drives the *Isle Wars Pro* game natively on Windows, takes screenshots at
# each key state, saves to a date-stamped directory. No poller, no WSL
# click-driving — this script does everything on the Windows side.
#
# Usage (in an elevated PowerShell, from the walkthroughs dir):
#   .\run-batch.ps1 -Batch f011-combat -Games 3
#
# What it does (F011 combat, per game):
#   1. Verifies the game is running (looks for "Islepro" window).
#   2. Clicks "New Game" (100, 585) then "Play Game" (565, 532).
#   3. Waits 4s for the board.
#   4. Screenshots the board (board-<n>.png).
#   5. Tries to place armies on a Blue country (clicks the centre and ALL,
#      then PLACE). If the country isn't Blue, the place is ignored —
#      the screenshot still shows the board state.
#   6. Screenshots after placement (placement-<n>.png).
#   7. Clicks ATTACK, screenshots (attack-<n>.png).
#   8. Clicks QUIT ATTACK, then PASS.
#   9. Waits 5s for the computer to play, screenshots (after-pass-<n>.png).
#  10. Repeats from step 2 for the requested number of games.
#
# Each run produces <shots-dir>\<batch>\<YYYYMMDD-HHMMSS>\*.png.
#
# The main session on WSL reads the screenshots and writes the per-arm-count
# records to runs/E018/combat/<run-id>.json.

param(
    [string]$Batch = "f011-combat",
    [int]$Games = 3,
    [string]$ShotsRoot = "C:\Temp\iwp-shots"
)

$ErrorActionPreference = "Stop"

# ---- Win32 P/Invoke (mouse, window, screenshot) ----
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
Add-Type @"
using System;
using System.Runtime.InteropServices;
public class Win32 {
    [DllImport("user32.dll")]
    public static extern void mouse_event(int dwFlags, int dx, int dy, int dwData, int dwExtra);
    [DllImport("user32.dll")]
    public static extern bool SetCursorPos(int X, int Y);
    [DllImport("user32.dll")]
    public static extern IntPtr FindWindow(string lpClassName, string lpWindowName);
    [DllImport("user32.dll", CharSet = CharSet.Auto)]
    public static extern int GetWindowText(IntPtr hWnd, System.Text.StringBuilder lpString, int nMaxCount);
    [DllImport("user32.dll")]
    public static extern bool GetWindowRect(IntPtr hWnd, out RECT lpRect);
    [DllImport("user32.dll")]
    public static extern bool SetForegroundWindow(IntPtr hWnd);
    public delegate bool EnumWindowsProc(IntPtr hWnd, IntPtr lParam);
    [DllImport("user32.dll")]
    public static extern bool EnumWindows(EnumWindowsProc enumProc, IntPtr lParam);
    [DllImport("user32.dll")]
    public static extern int GetWindowThreadProcessId(IntPtr hWnd, out int processId);
    [DllImport("user32.dll")]
    public static extern uint GetWindowThreadProcessId(IntPtr hWnd, IntPtr processId);
    [DllImport("user32.dll")]
    public static extern bool MoveWindow(IntPtr hwnd, int x, int y, int cx, int cy, bool repaint);
    [DllImport("user32.dll", SetLastError = true)]
    public static extern IntPtr SetWinEventHook(uint eventMin, uint eventMax, IntPtr hmodWinEventProc, IntPtr pfnWinEventProc, uint idProcess, uint idThread, uint dwFlags);
    [DllImport("user32.dll", CharSet = CharSet.Auto, SetLastError = true)]
    public static extern bool UnhookWinEvent(IntPtr hWinEventHook);
    [StructLayout(LayoutKind.Sequential)]
    public struct RECT { public int Left, Top, Right, Bottom; }
}
"@

# ---- Helpers ----
$GameHwnd = [IntPtr]::Zero

function Get-GameWindow {
    foreach ($title in @("Islepro", "Isle Wars Pro", "Isle Wars Pro Game")) {
        $h = [Win32]::FindWindow($null, $title)
        if ($h -ne [IntPtr]::Zero) { return [int64]$h }
    }
    return 0
}

function Get-WindowRect {
    param([IntPtr]$hwnd)
    $r = New-Object Win32+RECT
    [Win32]::GetWindowRect($hwnd, [ref]$r) | Out-Null
    return @{ x = $r.Left; y = $r.Top; w = ($r.Right - $r.Left); h = ($r.Bottom - $r.Top) }
}

function Click-Stage {
    param([int]$sx, [int]$sy, [string]$button = "left")
    if ($GameHwnd -eq [IntPtr]::Zero) { throw "GameHwnd not set" }
    $r = Get-WindowRect $GameHwnd
    $dx = $r.x + $sx
    $dy = $r.y + $sy
    [Win32]::SetCursorPos($dx, $dy) | Out-Null
    Start-Sleep -Milliseconds 30
    $down = if ($button -eq "right") { 0x0008 } else { 0x0002 }
    $up = $down -bor 0x0004
    [Win32]::mouse_event($down, 0, 0, 0, 0) | Out-Null
    [Win32]::mouse_event($up, 0, 0, 0, 0) | Out-Null
}

function Send-Key {
    param([string]$key)
    [System.Windows.Forms.SendKeys]::SendWait($key)
}

function Take-Shot {
    param([string]$path)
    $dir = Split-Path $path
    if ($dir -and -not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
    $bounds = [System.Windows.Forms.SystemInformation]::VirtualScreen
    $bmp = New-Object System.Drawing.Bitmap $bounds.Width, $bounds.Height
    $g = [System.Drawing.Graphics]::FromImage($bmp)
    $g.CopyFromScreen($bounds.X, $bounds.Y, 0, 0, $bmp.Size)
    $bmp.Save($path, [System.Drawing.Imaging.ImageFormat]::Png)
    $g.Dispose(); $bmp.Dispose()
    return $path
}

# ---- Main ----
$GameHwnd = [IntPtr]::new([int64](Get-GameWindow))
if ($GameHwnd -eq [IntPtr]::Zero) {
    Write-Host "Islepro window not found. Launch the game first."
    exit 1
}
[Win32]::SetForegroundWindow($GameHwnd) | Out-Null
$rect = Get-WindowRect $GameHwnd
Write-Host ("game window: hwnd={0} pos=({1},{2}) size=({3}x{4})" -f $GameHwnd, $rect.x, $rect.y, $rect.w, $rect.h)

$Stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$OutDir = Join-Path $ShotsRoot $Batch $Stamp
New-Item -ItemType Directory -Path $OutDir -Force | Out-Null
Write-Host "shots -> $OutDir"

# ---- Visit options screen (Q-SET-04) once ----
Write-Host "`n[Q-SET-04] visit options"
Click-Stage 320 585         # Options
Start-Sleep -Milliseconds 800
Take-Shot (Join-Path $OutDir "q-set-04-options.png")
Click-Stage 388 516         # Return
Start-Sleep -Milliseconds 800

# ---- Play $Games games ----
for ($g = 1; $g -le $Games; $g++) {
    Write-Host "`n[Game $g of $Games]"

    Write-Host "  click New Game (100, 585)"
    Click-Stage 100 585
    Start-Sleep -Milliseconds 600

    Write-Host "  click Play Game (565, 532)"
    Click-Stage 565 532
    Start-Sleep -Milliseconds 4000          # the computer players take their turns first

    $boardPath = Join-Path $OutDir ("game-{0:D2}-board.png" -f $g)
    Take-Shot $boardPath
    Write-Host "  shot board -> $boardPath"

    Write-Host "  place armies: click country, ALL, PLACE"
    Click-Stage 200 300                    # try a board-centre country
    Start-Sleep -Milliseconds 300
    Click-Stage 307 543                    # ALL
    Start-Sleep -Milliseconds 300
    Click-Stage 497 543                    # PLACE
    Start-Sleep -Milliseconds 600

    $placePath = Join-Path $OutDir ("game-{0:D2}-placement.png" -f $g)
    Take-Shot $placePath
    Write-Host "  shot placement -> $placePath"

    Write-Host "  attack: click attack, then attack neighbours via click-until, then attack + quit"
    Click-Stage 337 531                    # ATTACK panel
    Start-Sleep -Milliseconds 400
    Click-Stage 200 300                    # try a target (the game ignores invalid ones)
    Start-Sleep -Milliseconds 400
    $attackPath = Join-Path $OutDir ("game-{0:D2}-attack.png" -f $g)
    Take-Shot $attackPath
    Write-Host "  shot attack -> $attackPath"

    Write-Host "  quit attack and pass turn"
    Click-Stage 456 531                    # QUIT ATTACK
    Start-Sleep -Milliseconds 400
    Click-Stage 417 530                    # PASS
    Start-Sleep -Milliseconds 500

    Write-Host "  wait for computer to play (6 s)"
    Start-Sleep -Milliseconds 6000

    $afterPath = Join-Path $OutDir ("game-{0:D2}-after-pass.png" -f $g)
    Take-Shot $afterPath
    Write-Host "  shot after-pass -> $afterPath"
}

Write-Host "`nDone. $Games games played, screenshots in $OutDir"
Write-Host "Next: the main session on WSL reads the screenshots and writes runs/E018/combat/*.json"
