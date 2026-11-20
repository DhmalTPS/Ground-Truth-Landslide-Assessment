"""Temporary Windows Firewall opening for phones on the same Wi-Fi (python src/app.py --lan).

Why: Windows makes inbound *Block* rules for python.exe when its first "Allow access?" popup is cancelled, and on a
Public network (hostel/campus Wi-Fi, a new hotspot) those rules stop phones from reaching the app.

How (one UAC popup per run): an elevated PowerShell *guardian* is started that
  1. first undoes anything left over from an earlier run (power loss / shutdown),
  2. writes the list of Block rules it will pause to a state file, THEN pauses them (disabled, not deleted),
  3. adds one Allow rule: TCP on the app's ports, only from the local subnet, only for the Python that listens,
  4. waits until the app asks to stop (Ctrl+C) or the app's process is gone (crash, kill, window closed),
  5. removes the Allow rule and re-enables exactly the paused Block rules, then writes done.txt.
Because the guardian watches the process itself, the revert does not depend on Python's own cleanup running.
Only a power loss can skip it; the state file then stays, a normal start warns, and --lan-restore undoes it.
"""
import os
import sys
import time

GROUP = "Landslide app LAN (temporary)"

HELPER = r"""param([string]$Mode, [int]$AppPid, [string]$Exe, [string]$Ports, [string]$Dir, [switch]$Dry)
$ErrorActionPreference = 'Stop'
$G = 'Landslide app LAN (temporary)'
$state = Join-Path $Dir 'state.json'; $ready = Join-Path $Dir 'ready.txt'; $stop = Join-Path $Dir 'stop.txt'
$done = Join-Path $Dir 'done.txt'; $log = Join-Path $Dir 'guardian.log'
function Log($m) { Add-Content -Path $log -Value ('{0:yyyy-MM-dd HH:mm:ss} {1}' -f (Get-Date), $m) }
function Act($what, [scriptblock]$do) { if ($Dry) { Log "DRY $what" } else { & $do; Log $what } }
function Restore {
  $ok = $true
  try { $r = @(Get-NetFirewallRule -Group $G -ErrorAction SilentlyContinue)
        foreach ($x in $r) { Act "allow rule removed: $($x.DisplayName)" { Remove-NetFirewallRule -Name $x.Name } } }
  catch { $ok = $false; Log "remove failed: $_" }
  if (Test-Path $state) {
    $s = Get-Content $state -Raw | ConvertFrom-Json
    foreach ($n in @($s.paused)) { if ($n) { try { Act "block rule re-enabled: $n" { Enable-NetFirewallRule -Name $n } }
                                             catch { $ok = $false; Log "re-enable failed: $n : $_" } } }
    if ($ok) { Remove-Item $state }
  }
  $left = if ($Dry) { 0 } else { @(Get-NetFirewallRule -Group $G -ErrorAction SilentlyContinue).Count }
  Set-Content $done ('restored ok=' + $ok + ' allow_rules_left=' + $left)
}
try {
  Log "start mode=$Mode pid=$AppPid exe=$Exe ports=$Ports dry=$Dry"
  Restore                                   # leftovers from an earlier run that never got reverted
  if ($Mode -eq 'restore') { exit 0 }
  Remove-Item $done -ErrorAction SilentlyContinue
  $blocks = @(Get-NetFirewallApplicationFilter | Where-Object { $_.Program -ieq $Exe } | Get-NetFirewallRule |
              Where-Object { $_.Direction -eq 'Inbound' -and $_.Action -eq 'Block' -and $_.Enabled -eq 'True' })
  # the state is written BEFORE anything changes, so even a crash half-way can be undone exactly
  @{ paused = @($blocks | ForEach-Object { $_.Name }); app_pid = $AppPid } | ConvertTo-Json | Set-Content $state
  foreach ($b in $blocks) { Act "block rule paused: $($b.DisplayName) [$($b.Profile)]" { Disable-NetFirewallRule -Name $b.Name } }
  Act "allow rule added: TCP $Ports from LocalSubnet for $Exe" {
    New-NetFirewallRule -DisplayName 'Landslide app (LAN, removed on exit)' -Group $G -Direction Inbound -Action Allow `
      -Protocol TCP -LocalPort ($Ports -split ',') -Program $Exe -RemoteAddress LocalSubnet -Profile Any | Out-Null }
  Set-Content $ready ('ok paused=' + $blocks.Count)
  while (-not (Test-Path $stop) -and (Get-Process -Id $AppPid -ErrorAction SilentlyContinue)) { Start-Sleep -Milliseconds 400 }
  Log ('stopping: ' + $(if (Test-Path $stop) { 'Ctrl+C / normal exit' } else { 'app process ended' }))
}
catch { Log "error: $_"; Set-Content $ready ('error ' + $_) }
finally { Restore; Log 'closed' }
"""


def _dir():
    from common import DATA
    d = DATA.parent / ".cache" / "lan"
    d.mkdir(parents=True, exist_ok=True)
    return d


def listening_exe():
    """Path of the program that really opens the port. On Windows the venv's python.exe is only a launcher that
    starts the base Python as a child process, and the firewall matches that child's path."""
    try:
        import ctypes
        from ctypes import wintypes
        k = ctypes.windll.kernel32
        k.GetCurrentProcess.restype = wintypes.HANDLE
        k.QueryFullProcessImageNameW.argtypes = [wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR,
                                                 ctypes.POINTER(wintypes.DWORD)]
        buf, n = ctypes.create_unicode_buffer(32768), wintypes.DWORD(32768)
        if k.QueryFullProcessImageNameW(k.GetCurrentProcess(), 0, buf, ctypes.byref(n)):
            return buf.value
    except (AttributeError, OSError):
        pass
    return getattr(sys, "_base_executable", sys.executable)


def _launch(mode, ports="", dry=False):
    """Start the guardian elevated (one UAC popup). dry=True runs it unelevated and changes nothing (tests)."""
    d = _dir()
    for f in ("ready.txt", "stop.txt", "done.txt"):
        (d / f).unlink(missing_ok=True)
    ps1 = d / "guardian.ps1"
    ps1.write_text(HELPER, encoding="utf-8-sig")
    params = (f'-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "{ps1}" -Mode {mode} -AppPid {os.getpid()} '
              f'-Exe "{listening_exe()}" -Ports "{ports}" -Dir "{d}"' + (" -Dry" if dry else ""))
    import ctypes
    rc = ctypes.windll.shell32.ShellExecuteW(None, "open" if dry else "runas", "powershell.exe", params, None, 0)
    return d if rc > 32 else None


def _wait(path, seconds):
    t0 = time.time()
    while time.time() - t0 < seconds:
        if path.exists():
            time.sleep(.1)
            return path.read_text(encoding="utf-8", errors="replace").strip()
        time.sleep(.25)
    return None


def network_note():
    """Name and category of the current network, e.g. 'NEW_HOSTEL (Public)' (read-only, no admin needed)."""
    import subprocess
    try:
        r = subprocess.run(["powershell", "-NoProfile", "-Command",
                            "Get-NetConnectionProfile | ForEach-Object { $_.Name + ' (' + $_.NetworkCategory + ')' }"],
                           capture_output=True, text=True, timeout=15)
        return ", ".join(x.strip() for x in r.stdout.splitlines() if x.strip())
    except (OSError, subprocess.SubprocessError):
        return ""


def open_lan(ports, dry=False):
    """Open the firewall for the app's ports. Returns a handle for close_lan, or None (nothing was changed)."""
    if os.name != "nt":
        print("  --lan only changes Windows Firewall; nothing to do on this system")
        return None
    print("  --lan: Windows asks for permission (UAC) to open the firewall while the app runs...")
    d = _launch("open", ",".join(str(p) for p in ports), dry)
    if not d:
        print("  --lan: permission not given, firewall unchanged; phones on the Wi-Fi cannot reach the app")
        return None
    r = _wait(d / "ready.txt", 120)
    if not r or not r.startswith("ok"):
        print(f"  --lan: firewall NOT opened ({r or 'no answer from the guardian'}); details in {d / 'guardian.log'}")
        close_lan(d)
        return None
    paused = r.split("paused=")[-1]
    print(f"  --lan: firewall open for TCP {', '.join(map(str, ports))} from this Wi-Fi only "
          f"({paused} Python block rule(s) paused); it is restored when the app stops (Ctrl+C)")
    net = network_note()
    if net:
        print(f"  network: {net}")
    return d


def close_lan(d):
    """Ask the guardian to restore the firewall and confirm it. Safe to call more than once."""
    if not d:
        return
    if (d / "done.txt").exists() and not (d / "state.json").exists():
        return
    (d / "stop.txt").write_text("stop", encoding="utf-8")
    r = _wait(d / "done.txt", 30)
    if r and "ok=True" in r and "allow_rules_left=0" in r:
        print("  --lan: firewall restored (allow rule removed, paused block rules re-enabled)")
    else:
        print(f"  --lan: could NOT confirm the firewall was restored ({r or 'no answer'}). "
              f"Run: python src/app.py --lan-restore   (log: {d / 'guardian.log'})")


def restore_now():
    """--lan-restore: undo a run that never got reverted (power loss)."""
    if os.name != "nt":
        return
    d = _launch("restore")
    if not d:
        print("permission not given; nothing changed")
        return
    r = _wait(d / "done.txt", 120)
    print("firewall restored" if r and "ok=True" in r else f"restore not confirmed ({r or 'no answer'}); see {d / 'guardian.log'}")


def leftover():
    """True when an earlier --lan run never restored the firewall (state file still there)."""
    try:
        return os.name == "nt" and (_dir() / "state.json").exists()
    except OSError:
        return False
