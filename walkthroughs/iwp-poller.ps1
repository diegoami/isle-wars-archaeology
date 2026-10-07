# iwp-poller.ps1 — file-based command poller for T28 C3 step.
# Polls C:\Temp\iwp-cmd\ for cmd-*.json files, executes each, writes result-*.json.
#
# Commands (one per file, JSON):
#   {"cmd": "screenshot", "path": "C:\\Temp\\iwp-shots\\shot.png"}
#   {"cmd": "click", "x": 100, "y": 585, "button": "left"}
#   {"cmd": "move", "x": 100, "y": 585}
#   {"cmd": "key", "key": "Return"}
#   {"cmd": "wait", "ms": 1000}
#   {"cmd": "find_window", "title": "Isle"}
#   {"cmd": "is_window", "title": "Isle"}
#   {"cmd": "set_focus", "hwnd": 12345}
#   {"cmd": "shutdown"}
#
# Run (in an elevated PowerShell):
#   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
#   .\iwp-poller.ps1

$CmdDir = "C:\Temp\iwp-cmd"
if (-not (Test-Path $CmdDir)) { New-Item -ItemType Directory -Path $CmdDir -Force | Out-Null }

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
    [DllImport("user32.dll")]
    public static extern IntPtr FindWindowEx(IntPtr parent, IntPtr child, string cls, string title);
    [DllImport("user32.dll", CharSet = CharSet.Auto)]
    public static extern int GetWindowText(IntPtr hWnd, System.Text.StringBuilder lpString, int nMaxCount);
    [DllImport("user32.dll", CharSet = CharSet.Auto)]
    public static extern int GetClassName(IntPtr hWnd, System.Text.StringBuilder lpString, int nMaxCount);
    [DllImport("user32.dll")]
    public static extern bool GetWindowRect(IntPtr hWnd, out RECT lpRect);
    [DllImport("user32.dll")]
    public static extern bool SetForegroundWindow(IntPtr hWnd);
    [DllImport("user32.dll")]
    public static extern bool IsWindowVisible(IntPtr hWnd);
    [DllImport("user32.dll")]
    public static extern bool SetWindowPos(IntPtr hWnd, IntPtr hWndInsertAfter, int X, int Y, int cx, int cy, uint uFlags);
    [DllImport("user32.dll")]
    public static extern bool EnumWindows(EnumWindowsProc enumProc, IntPtr lParam);
    [DllImport("user32.dll")]
    public static extern bool IsWindowVisible(IntPtr hWnd);
    [DllImport("user32.dll")]
    public static extern int GetWindowThreadProcessId(IntPtr hWnd, out int processId);
    public delegate bool EnumWindowsProc(IntPtr hWnd, IntPtr lParam);
    [StructLayout(LayoutKind.Sequential)]
    public struct RECT { public int Left, Top, Right, Bottom; }
}
"@

function Cmd-Screenshot($req) {
    $path = $req.path
    if (-not $path) { return @{ok=$false; error="missing path"} }
    $dir = Split-Path $path
    if ($dir -and -not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
    $bounds = [System.Windows.Forms.SystemInformation]::VirtualScreen
    $bmp = New-Object System.Drawing.Bitmap $bounds.Width, $bounds.Height
    $g = [System.Drawing.Graphics]::FromImage($bmp)
    $g.CopyFromScreen($bounds.X, $bounds.Y, 0, 0, $bmp.Size)
    $bmp.Save($path, [System.Drawing.Imaging.ImageFormat]::Png)
    $g.Dispose(); $bmp.Dispose()
    return @{ok=$true; path=$path; w=$bounds.Width; h=$bounds.Height}
}

function Cmd-Click($req) {
    [Win32]::SetCursorPos([int]$req.x, [int]$req.y) | Out-Null
    Start-Sleep -Milliseconds 30
    $btn = if ($req.button -eq "right") { 0x08 } else { 0x02 }
    [Win32]::mouse_event($btn, 0, 0, 0, 0) | Out-Null
    [Win32]::mouse_event($btn -bor 0x04, 0, 0, 0, 0) | Out-Null
    return @{ok=$true}
}

function Cmd-Move($req) {
    [Win32]::SetCursorPos([int]$req.x, [int]$req.y) | Out-Null
    return @{ok=$true}
}

function Cmd-Key($req) {
    [System.Windows.Forms.SendKeys]::SendWait([string]$req.key)
    return @{ok=$true}
}

function Cmd-Wait($req) {
    Start-Sleep -Milliseconds ([int]$req.ms)
    return @{ok=$true}
}

function Cmd-FindWindow($req) {
    $hwnd = [Win32]::FindWindow($null, [string]$req.title)
    if ($hwnd -eq [IntPtr]::Zero) { return @{ok=$true; hwnd=0; present=$false} }
    $sb = New-Object System.Text.StringBuilder 256
    [Win32]::GetWindowText($hwnd, $sb, 256) | Out-Null
    $title = $sb.ToString()
    $r = New-Object Win32+RECT
    [Win32]::GetWindowRect($hwnd, [ref]$r) | Out-Null
    return @{
        ok=$true; hwnd=[int64]$hwnd; title=$title; present=$true
        rect=@{x=$r.Left; y=$r.Top; w=($r.Right - $r.Left); h=($r.Bottom - $r.Top)}
        visible=[Win32]::IsWindowVisible($hwnd)
    }
}

function Cmd-IsWindow($req) {
    $hwnd = [Win32]::FindWindow($null, [string]$req.title)
    return @{ok=$true; present=($hwnd -ne [IntPtr]::Zero)}
}

function Cmd-SetFocus($req) {
    $ok = [Win32]::SetForegroundWindow([IntPtr]::new([int64]$req.hwnd))
    return @{ok=$ok}
}

function Cmd-SetWindowPos($req) {
    $hwnd = [IntPtr]::new([int64]$req.hwnd)
    $x = [int]$req.x; $y = [int]$req.y
    $w = if ($req.w) { [int]$req.w } else { 0 }
    $h = if ($req.h) { [int]$req.h } else { 0 }
    $SWP_NOZORDER = 0x0004; $SWP_NOSIZE = 0x0001; $SWP_SHOWWINDOW = 0x0040
    $flags = $SWP_NOZORDER -bor $SWP_SHOWWINDOW
    if (-not $req.w) { $flags = $flags -bor $SWP_NOSIZE }
    $ok = [Win32]::SetWindowPos($hwnd, [IntPtr]::Zero, $x, $y, $w, $h, $flags)
    return @{ok=$ok}
}

function Cmd-ListWindows($req) {
    $results = New-Object System.Collections.ArrayList
    $callback = {
        param($hwnd, $lparam)
        $sb = New-Object System.Text.StringBuilder 256
        [Win32]::GetWindowText($hwnd, $sb, 256) | Out-Null
        $title = $sb.ToString()
        $sb2 = New-Object System.Text.StringBuilder 256
        [Win32]::GetClassName($hwnd, $sb2, 256) | Out-Null
        $cls = $sb2.ToString()
        $pid = 0
        [Win32]::GetWindowThreadProcessId($hwnd, [ref]$pid) | Out-Null
        if ($title -or $cls) {
            $r = New-Object Win32+RECT
            [Win32]::GetWindowRect($hwnd, [ref]$r) | Out-Null
            $results.Add(@{
                hwnd=[int64]$hwnd; title=$title; cls=$cls; pid=$pid
                visible=[Win32]::IsWindowVisible($hwnd)
                rect=@{x=$r.Left; y=$r.Top; w=($r.Right - $r.Left); h=($r.Bottom - $r.Top)}
            }) | Out-Null
        }
        return $true
    }
    [Win32]::EnumWindows($callback, [IntPtr]::Zero) | Out-Null
    return @{ok=$true; windows=$results}
}

function Cmd-LaunchGame($req) {
    $path = $req.path
    if (-not $path) { return @{ok=$false; error="missing path"} }
    $args = $req.args
    $proc = if ($args) { Start-Process -FilePath $path -ArgumentList $args -PassThru }
            else { Start-Process -FilePath $path -PassThru }
    Start-Sleep -Seconds 2
    $hwnd = [IntPtr]::Zero
    foreach ($title in @("Islepro", "Isle Wars Pro", "Isle Wars Pro Game", "Macromedia Projector")) {
        $hwnd = [Win32]::FindWindow($null, $title)
        if ($hwnd -ne [IntPtr]::Zero) { break }
    }
    # Move window to requested position if given
    if ($req.x -ne $null -and $req.y -ne $null -and $hwnd -ne [IntPtr]::Zero) {
        $SWP_NOZORDER = 0x0004; $SWP_NOSIZE = 0x0001
        $flags = $SWP_NOZORDER
        if (-not $req.w -or -not $req.h) { $flags = $flags -bor $SWP_NOSIZE }
        [Win32]::SetWindowPos($hwnd, [IntPtr]::Zero, [int]$req.x, [int]$req.y,
            [int]($req.w), [int]($req.h), $flags) | Out-Null
    }
    return @{ok=$true; pid=$proc.Id; hwnd=[int64]$hwnd}
}

function Process-Command($req) {
    switch ($req.cmd) {
        "screenshot"   { return Cmd-Screenshot $req }
        "click"        { return Cmd-Click $req }
        "move"         { return Cmd-Move $req }
        "key"          { return Cmd-Key $req }
        "wait"         { return Cmd-Wait $req }
        "find_window"  { return Cmd-FindWindow $req }
        "is_window"    { return Cmd-IsWindow $req }
        "set_focus"    { return Cmd-SetFocus $req }
        "shutdown"     { Write-Host "shutdown requested"; return @{ok=$true} }
        "set_window_pos" { return Cmd-SetWindowPos $req }
        "list_windows" { return Cmd-ListWindows $req }
        "launch_game"  { return Cmd-LaunchGame $req }
        default        { return @{ok=$false; error="unknown cmd: $($req.cmd)"} }
    }
}

Write-Host "iwp-poller watching $CmdDir (pid $PID)"
$Shutdown = $false
while (-not $Shutdown) {
    Get-ChildItem -Path $CmdDir -Filter "cmd-*.json" -ErrorAction SilentlyContinue | ForEach-Object {
        $cmdFile = $_.FullName
        $id = $_.BaseName -replace '^cmd-', ''
        $resultFile = Join-Path $CmdDir ("result-" + $id + ".json")
        try {
            $text = Get-Content -Path $cmdFile -Raw -Encoding UTF8
            $req = $text | ConvertFrom-Json
            $resp = Process-Command $req
            if ($req.cmd -eq "shutdown") { $Shutdown = $true }
        } catch {
            $resp = @{ok=$false; error=$_.Exception.Message}
        }
        try {
            $resp | ConvertTo-Json -Compress -Depth 5 | Set-Content -Path $resultFile -Encoding UTF8
            Remove-Item -Path $cmdFile -Force -ErrorAction SilentlyContinue
        } catch {}
    }
    Start-Sleep -Milliseconds 100
}
Write-Host "iwp-poller stopped"
