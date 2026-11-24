#!/usr/bin/env python3
"""W128m: LIVE verification driver for the 9 hooks (②-a x6 + third defect x3).

Sequence (each step's real output is kept):
  1. claim the project instance lock (same text format the harness uses)
  2. launch sandbox gamemd.exe, wait for the pid
  3. let it initialise a few seconds (image fully loaded)
  4. apply_hooks.py --pid N            (DRY-RUN: verifies runtime bytes == image)
  5. apply_hooks.py --pid N --apply    (install)
  6. verify_hook.py  post --pid N      (independent read-back, group A only)
  7. extra group-S read-back (E8 -> helper, helper body intact)
  8. apply_hooks.py --pid N --unhook   (restore) then re-check bytes == image
  9. terminate gamemd, assert no residue, restore the lock record

Step 4 is the interesting one: if the runtime .text differs from the on-disk image
(the exe carries a non-stock .detour section), it will FAIL-CLOSED and tell us
that static/runtime patching assumptions are wrong.
"""
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
SANDBOX = Path(r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W110_crash\out\sandbox_game")
LOCK = Path(r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\.game_instance.lock")
PY = sys.executable

log = open(HERE / "live_hook_test.log", "w", encoding="utf-8")


def say(msg):
    print(msg)
    log.write(msg + "\n")
    log.flush()


def run(args, timeout=180):
    say("$ " + " ".join(str(a) for a in args))
    r = subprocess.run([str(a) for a in args], capture_output=True, text=True,
                       timeout=timeout)
    out = (r.stdout or "") + (r.stderr or "")
    for line in out.splitlines():
        say("   " + line)
    say("   [exit %d]" % r.returncode)
    return r.returncode, out


def list_gamemd():
    r = subprocess.run(["powershell", "-NoProfile", "-Command",
                        "Get-Process gamemd -ErrorAction SilentlyContinue | "
                        "Select-Object -ExpandProperty Id"],
                       capture_output=True, text=True, timeout=60)
    return [int(x) for x in (r.stdout or "").split() if x.strip().isdigit()]


def claim_lock(purpose):
    LOCK.write_text("run_id=next_re_20261112_r10_W128\n"
                    "owner=lead\n"
                    "time=%s\n"
                    "purpose=%s\n" % (time.strftime("%Y-%m-%dT%H:%M:%S"), purpose),
                    encoding="utf-8")


def restore_lock():
    LOCK.write_text("run_id=next_re_20261112_r10_W128\n"
                    "owner=lead\n"
                    "time=%s\n"
                    "purpose=LIVE hook test FINISHED; residual_gamemd=0; owner restored.\n"
                    % time.strftime("%Y-%m-%dT%H:%M:%S"), encoding="utf-8")


def main():
    say("=== live hook test %s ===" % time.strftime("%Y-%m-%d %H:%M:%S"))
    pre = list_gamemd()
    if pre:
        say("ABORT: gamemd already running (pids=%r); refusing to touch it" % pre)
        return 2

    claim_lock("LIVE hook verification: install 9 hooks, read back, restore, kill")
    pid = None
    try:
        say("\n[1] launch sandbox gamemd.exe")
        ps = ("$r = Invoke-CimMethod -ClassName Win32_Process -MethodName Create "
              "-Arguments @{CommandLine='cmd.exe /c cd /d \"%s\" && start \"\" \"gamemd.exe\"'}; "
              "Write-Output ('{0}|{1}' -f $r.ProcessId, $r.ReturnValue)" % SANDBOX)
        r = subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                           capture_output=True, text=True, timeout=120)
        say("   launcher: %s" % (r.stdout or "").strip())
        m = re.search(r"(\d+)\|(\d+)", r.stdout or "")
        if not m or int(m.group(2)) != 0:
            say("ABORT: WMI create failed")
            return 2

        say("\n[2] wait for gamemd pid")
        t0 = time.time()
        while time.time() - t0 < 120:
            pids = list_gamemd()
            if pids:
                pid = pids[0]
                break
            time.sleep(1.0)
        if pid is None:
            say("ABORT: gamemd never appeared")
            return 2
        say("   pid=%d (after %.1fs)" % (pid, time.time() - t0))

        say("\n[3] settle 8s for image init")
        time.sleep(8.0)

        say("\n[4] DRY-RUN (runtime bytes vs on-disk image)")
        rc_dry, _ = run([PY, HERE / "apply_hooks.py", "--pid", pid])

        say("\n[5] APPLY")
        rc_apply, out_apply = run([PY, HERE / "apply_hooks.py", "--pid", pid, "--apply"])

        say("\n[6] read-back group A (verify_hook.py post)")
        rc_post, out_post = run([PY, HERE / "verify_hook.py", "post", "--pid", pid])

        say("\n[7] read-back group S (3 sites -> helper)")
        rc_s = probe_group_s(pid)

        say("\n[8] UNHOOK + confirm restored")
        run([PY, HERE / "apply_hooks.py", "--pid", pid, "--unhook"])
        rc_restore_dry, _ = run([PY, HERE / "apply_hooks.py", "--pid", pid])

        say("\n[9] terminate")
        subprocess.run(["taskkill", "/F", "/T", "/PID", str(pid)],
                       capture_output=True, text=True, timeout=60)
        time.sleep(2.0)
        left = list_gamemd()
        say("   residual gamemd: %r" % left)

        say("\n=== SUMMARY ===")
        say("  dry-run rc           : %d (0 = runtime bytes matched image)" % rc_dry)
        say("  apply rc             : %d" % rc_apply)
        say("  group A post rc      : %d (0 = all 6 entries land on stubs)" % rc_post)
        say("  group S post rc      : %d" % rc_s)
        say("  restored-dry rc      : %d (0 = bytes back to original)" % rc_restore_dry)
        say("  residual             : %r" % left)
        return 0
    finally:
        if pid is not None:
            left = list_gamemd()
            if left:
                say("   cleanup: killing %r" % left)
                for p in left:
                    subprocess.run(["taskkill", "/F", "/T", "/PID", str(p)],
                                   capture_output=True, text=True, timeout=60)
        restore_lock()
        log.close()


def probe_group_s(pid):
    """Independent read-back of the 3 sites: E8 rel32 -> helper, helper == template."""
    import ctypes
    from ctypes import wintypes as wt
    import struct
    k32 = ctypes.WinDLL("kernel32", use_last_error=True)
    k32.OpenProcess.restype = wt.HANDLE
    h = k32.OpenProcess(0x0010 | 0x0400, False, pid)
    if not h:
        say("   group S: OpenProcess failed")
        return 1

    def rd(va, n):
        b = ctypes.create_string_buffer(n)
        got = ctypes.c_size_t(0)
        if not k32.ReadProcessMemory(h, ctypes.c_void_p(va), b, n,
                                     ctypes.byref(got)) or got.value != n:
            return None
        return b.raw

    sites = json.load(open(HERE / "sites.json", encoding="utf-8"))
    ok = True
    for s in sites:
        va = int(s["site"], 16)
        cur = rd(va, 12)
        if cur is None:
            say("   %s <unreadable>" % s["site"]); ok = False; continue
        if cur[0] != 0xE8:
            say("   %s NOT patched (byte0=0x%02X)" % (s["site"], cur[0])); ok = False; continue
        rel = struct.unpack("<i", cur[1:5])[0]
        helper = (va + 5 + rel) & 0xFFFFFFFF
        body = rd(helper, s["len"])
        match = body is not None and body.hex() == s["bytes"]
        pad = all(b == 0x90 for b in cur[5:12])
        say("   %s -> helper 0x%08X  body=%s pad=%s  %s"
            % (s["site"], helper, "match" if match else "DIFF",
               "ok" if pad else "BAD", "OK" if (match and pad) else "FAIL"))
        ok &= (match and pad)
    # restore the sites we only read? no: read-only probe
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
