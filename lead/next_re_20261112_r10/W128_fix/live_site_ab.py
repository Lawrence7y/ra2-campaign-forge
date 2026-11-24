#!/usr/bin/env python3
"""W128o: behavioural A/B for the THIRD defect's 3 null-safe helpers.

The defect's trigger is `[obj+0xAC] == 0`, which needs no game state at all: we
allocate a zeroed fake object in the target and run the *original* 12-byte
sequence vs the *installed* helper against it.

  control : mov edx,[ecx+0xAC] ; mov al,[edx+0x155]   with ecx=fake
            -> edx = 0 -> read [0x155] -> AV (0xC0000005)
  patched : call <helper from the site's E8>          with ecx=fake
            -> helper loads edx=0, tests, takes the null path, al=0, returns
            -> we then store al and a mark, thread spins, process stays alive

The patched arm calls the helper **through the installed site patch**, so it
tests the real installed artifact, not a copy.
"""
import argparse
import ctypes
import re
import struct
import subprocess
import sys
import time
from ctypes import wintypes as wt
from pathlib import Path

HERE = Path(__file__).resolve().parent
SANDBOX = Path(r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W110_crash\out\sandbox_game")
SITE = 0x006F409C          # site #1 (offset +0x155)

k32 = ctypes.WinDLL("kernel32", use_last_error=True)
k32.OpenProcess.restype = wt.HANDLE
k32.VirtualAllocEx.restype = ctypes.c_void_p
k32.VirtualAllocEx.argtypes = [wt.HANDLE, ctypes.c_void_p, ctypes.c_size_t, wt.DWORD, wt.DWORD]
k32.WriteProcessMemory.argtypes = [wt.HANDLE, ctypes.c_void_p, ctypes.c_void_p,
                                   ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]
k32.ReadProcessMemory.argtypes = [wt.HANDLE, ctypes.c_void_p, ctypes.c_void_p,
                                  ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]
k32.CreateRemoteThread.restype = wt.HANDLE
k32.CreateRemoteThread.argtypes = [wt.HANDLE, ctypes.c_void_p, ctypes.c_size_t,
                                   ctypes.c_void_p, ctypes.c_void_p, wt.DWORD, ctypes.c_void_p]
PROCESS_ALL = 0x001F0FFF
PY = sys.executable


def say(s):
    print(s, flush=True)


def game_pids():
    r = subprocess.run(["powershell", "-NoProfile", "-Command",
                        "Get-Process gamemd -ErrorAction SilentlyContinue | "
                        "Select-Object -ExpandProperty Id"],
                       capture_output=True, text=True, timeout=60)
    return [int(x) for x in (r.stdout or "").split() if x.strip().isdigit()]


def kill_all():
    for p in game_pids():
        subprocess.run(["taskkill", "/F", "/T", "/PID", str(p)],
                       capture_output=True, text=True, timeout=60)
    time.sleep(2.0)
    return game_pids()


def launch():
    ps = ("$r = Invoke-CimMethod -ClassName Win32_Process -MethodName Create "
          "-Arguments @{CommandLine='cmd.exe /c cd /d \"%s\" && start \"\" \"gamemd.exe\"'}; "
          "Write-Output ('{0}|{1}' -f $r.ProcessId, $r.ReturnValue)" % SANDBOX)
    subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                   capture_output=True, text=True, timeout=120)
    t0 = time.time()
    while time.time() - t0 < 120:
        p = game_pids()
        if p:
            return p[0]
        time.sleep(1.0)
    raise RuntimeError("gamemd did not start")


class Proc:
    def __init__(self, pid):
        self.pid = pid
        self.h = k32.OpenProcess(PROCESS_ALL, False, pid)
        if not self.h:
            raise OSError("OpenProcess failed")

    def alloc(self, n):
        return int(k32.VirtualAllocEx(self.h, None, n, 0x3000, 0x40))

    def wr(self, va, data):
        got = ctypes.c_size_t(0)
        buf = ctypes.create_string_buffer(bytes(data), len(data))
        return bool(k32.WriteProcessMemory(self.h, ctypes.c_void_p(va), buf, len(data),
                                          ctypes.byref(got))) and got.value == len(data)

    def rd(self, va, n):
        b = ctypes.create_string_buffer(n)
        got = ctypes.c_size_t(0)
        if not k32.ReadProcessMemory(self.h, ctypes.c_void_p(va), b, n,
                                     ctypes.byref(got)) or got.value != n:
            return None
        return b.raw

    def u32(self, va):
        b = self.rd(va, 4)
        return None if b is None else struct.unpack("<I", b)[0]

    def thread(self, start):
        t = k32.CreateRemoteThread(self.h, None, 0, ctypes.c_void_p(start),
                                   None, 0, None)
        if not t:
            raise OSError("CreateRemoteThread failed")
        return t


def code_control(obj, mark):
    """mov edx,[ecx+0xAC]; mov al,[edx+0x155]; mov [mark],1; jmp $"""
    c = bytearray()
    c += b"\x31\xC9"                                       # xor ecx,ecx
    c += b"\x8B\x0D" + struct.pack("<I", 0)                # placeholder: mov ecx,imm32
    c[-6:] = b"\xB9" + struct.pack("<I", obj)              # mov ecx, obj
    c += b"\x8B\x91\xAC\x00\x00\x00"                       # mov edx,[ecx+0xAC]
    c += b"\x8A\x82\x55\x01\x00\x00"                       # mov al,[edx+0x155]
    c += b"\xC7\x05" + struct.pack("<I", mark) + b"\x01\x00\x00\x00"
    c += b"\xEB\xFE"
    return bytes(c)


def code_patched(obj, helper, mark, mark_al):
    """mov ecx,obj; call helper; mov [mark_al],al; mov [mark],1; jmp $"""
    c = bytearray()
    c += b"\xB9" + struct.pack("<I", obj)                  # mov ecx, obj
    call_at = len(c)
    c += b"\xE8" + b"\x00\x00\x00\x00"                     # call rel32 -> patched below
    c += b"\xA2" + struct.pack("<I", mark_al)              # mov [mark_al], al
    c += b"\xC7\x05" + struct.pack("<I", mark) + b"\x01\x00\x00\x00"
    c += b"\xEB\xFE"
    return bytes(c), call_at


def run_arm(label, patched):
    say("\n============ SITE ARM: %s ============" % label)
    if game_pids():
        kill_all()
    pid = launch()
    say("  pid=%d" % pid)
    time.sleep(8.0)

    helper = None
    if patched:
        r = subprocess.run([PY, HERE / "apply_hooks.py", "--pid", str(pid),
                            "--apply", "--group", "s"],
                           capture_output=True, text=True, timeout=180)
        say("  apply group s rc=%d" % r.returncode)
        for ln in (r.stdout or "").splitlines():
            say("    " + ln)

    p = Proc(pid)
    fake = p.alloc(0x2000)          # zeroed page => [fake+0xAC] == 0
    p.wr(fake, b"\x00" * 0x2000)
    page = p.alloc(0x200)
    mark = page + 0x100
    mark_al = page + 0x108

    if patched:
        cur = p.rd(SITE, 12)
        if cur is None or cur[0] != 0xE8:
            say("  site not patched; abort")
            kill_all()
            return None
        helper = (SITE + 5 + struct.unpack("<i", cur[1:5])[0]) & 0xFFFFFFFF
        say("  site 0x%08X -> helper 0x%08X" % (SITE, helper))
        code, call_at = code_patched(fake, helper, mark, mark_al)
        code = bytearray(code)
        code[call_at + 1:call_at + 5] = struct.pack(
            "<I", (helper - (page + call_at + 5)) & 0xFFFFFFFF)
        code = bytes(code)
    else:
        code = code_control(fake, mark)

    if not p.wr(page, code):
        say("  FAILED writing code page")
        kill_all()
        return None
    say("  fake obj @0x%08X ([obj+0xAC] = 0)   code @0x%08X  mark @0x%08X"
        % (fake, page, mark))

    t = p.thread(page)
    code_out = None
    for _ in range(20):
        time.sleep(0.5)
        ec = wt.DWORD(0)
        if k32.GetExitCodeThread(t, ctypes.byref(ec)):
            code_out = ec.value
            if code_out != 259:
                break

    alive = pid in game_pids()
    got_mark = p.u32(mark) if alive else None
    got_al = p.rd(mark_al, 1) if alive else None
    say("  thread exit : 0x%08X%s" % ((code_out or 0),
                                      "  (259=STILL_ACTIVE)" if code_out == 259 else ""))
    say("  alive       : %s" % alive)
    say("  mark        : %s" % got_mark)
    say("  al          : %s" % (None if got_al is None else "0x%02X" % got_al[0]))

    try:
        k32.TerminateThread(t, 0)
    except Exception:
        pass
    left = kill_all()
    say("  residual    : %r" % left)
    return {"exit": code_out, "alive": alive, "mark": got_mark,
            "al": None if got_al is None else got_al[0]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", choices=["both", "control", "patched"], default="both")
    a = ap.parse_args()
    out = {}
    if a.arm in ("both", "control"):
        out["control"] = run_arm("control(original 12 bytes)", patched=False)
    if a.arm in ("both", "patched"):
        out["patched"] = run_arm("patched(installed helper)", patched=True)

    say("\n============ SITE A/B VERDICT ============")
    AV = 0xC0000005
    c, p = out.get("control"), out.get("patched")
    if c:
        say("  control: exit=0x%08X alive=%s mark=%s"
            % ((c["exit"] or 0) & 0xFFFFFFFF, c["alive"], c["mark"]))
    if p:
        say("  patched: exit=%s alive=%s mark=%s al=%s"
            % (p["exit"], p["alive"], p["mark"], p["al"]))
    if c and p:
        cc = ((c["exit"] or 0) & 0xFFFFFFFF) == AV and not c["alive"]
        ps = p["alive"] and p["mark"] == 1 and p["al"] == 0
        say("  control AV        : %s" % cc)
        say("  patched safe(al=0): %s" % ps)
        say("  => helper prevents the crash: %s" % ("YES" if (cc and ps) else "NO/INCONCLUSIVE"))
        return 0 if (cc and ps) else 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
