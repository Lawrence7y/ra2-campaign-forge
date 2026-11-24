#!/usr/bin/env python3
"""W128n: A/B behavioural test of the guard, on the real game.

Idea: call the patched routine with ecx = 0 from a remote thread and see what
happens. This is decisive both ways:

  control  (no hooks): FUN_00724730 with this=NULL executes
                       `mov eax,[ebp+0x250]` -> AV reading 0x250
                       => the game dies with Eip:00724737, i.e. we REPRODUCE the
                          user's crash on demand, for the first time under control.
  patched  (hooks)   : entry is `test ecx,ecx / jz` -> the stub does `ret 4`
                       => the thread returns to our trampoline, game stays alive.

Trampoline (code we own, 32-bit, position independent):
    push 0               6A 00          ; the routine's 1 dword stack arg
    xor  ecx,ecx         31 C9          ; this = NULL
    mov  eax,<fn>        B8 imm32
    call eax             FF D0
    mov  dword [mark],1  C7 05 imm32 01 00 00 00
    jmp  $               EB FE          ; spin; we TerminateThread afterwards

Everything is read-only except (a) our own trampoline page and (b) the hook
bytes, which are installed/reverted through apply_hooks.py.
"""
import argparse
import ctypes
import json
import os
import re
import struct
import subprocess
import sys
import time
from ctypes import wintypes as wt
from pathlib import Path

HERE = Path(__file__).resolve().parent
SANDBOX = Path(r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W110_crash\out\sandbox_game")
EXCEPT = SANDBOX / "except.txt"
PY = sys.executable

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
                                   ctypes.c_void_p, ctypes.c_void_p, wt.DWORD,
                                   ctypes.c_void_p]

PROCESS_ALL = 0x001F0FFF
TARGET_FN = 0x00724730   # overridden by --fn


def say(s):
    print(s, flush=True)


def game_pids():
    r = subprocess.run(["powershell", "-NoProfile", "-Command",
                        "Get-Process gamemd -ErrorAction SilentlyContinue | "
                        "Select-Object -ExpandProperty Id"],
                       capture_output=True, text=True, timeout=60)
    return [int(x) for x in (r.stdout or "").split() if x.strip().isdigit()]


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


def kill_all():
    for p in game_pids():
        subprocess.run(["taskkill", "/F", "/T", "/PID", str(p)],
                       capture_output=True, text=True, timeout=60)
    time.sleep(2.0)
    return game_pids()


class Proc:
    def __init__(self, pid):
        self.pid = pid
        self.h = k32.OpenProcess(PROCESS_ALL, False, pid)
        if not self.h:
            raise OSError("OpenProcess failed %d" % ctypes.get_last_error())

    def alloc(self, n):
        return int(k32.VirtualAllocEx(self.h, None, n, 0x3000, 0x40))

    def wr(self, va, data):
        got = ctypes.c_size_t(0)
        buf = ctypes.create_string_buffer(data, len(data))
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

    def thread(self, start, param=0):
        t = k32.CreateRemoteThread(self.h, None, 0, ctypes.c_void_p(start),
                                   ctypes.c_void_p(param), 0, None)
        if not t:
            raise OSError("CreateRemoteThread failed %d" % ctypes.get_last_error())
        return t


def build_trampoline(fn, arg_placeholder=0):
    """push arg; xor ecx,ecx; mov eax,fn; call eax; mov [mark],1; jmp $"""
    code = bytearray()
    code += b"\x6A" + bytes([arg_placeholder & 0xFF])       # push imm8
    code += b"\x31\xC9"                                    # xor ecx,ecx
    code += b"\xB8" + struct.pack("<I", fn)                # mov eax, imm32
    code += b"\xFF\xD0"                                    # call eax
    mark_off = len(code) + 2                               # after C7 05
    code += b"\xC7\x05\x00\x00\x00\x00" + b"\x01\x00\x00\x00"   # mov [mark],1
    code += b"\xEB\xFE"                                    # jmp $
    return bytes(code), mark_off


def run_arm(label, install_hooks):
    say("\n================ ARM: %s ================" % label)
    pre = game_pids()
    if pre:
        say("  (killing leftover %r)" % pre)
        kill_all()
    bak_holder = {"path": None}
    if EXCEPT.exists():
        bak = EXCEPT.with_suffix(".txt.pre_ab_%s" % label)
        os.replace(EXCEPT, bak)
        bak_holder["path"] = bak
        say("  moved old except.txt -> %s" % bak.name)

    pid = launch()
    say("  pid=%d" % pid)
    time.sleep(8.0)

    if install_hooks:
        r = subprocess.run([PY, HERE / "apply_hooks.py", "--pid", str(pid), "--apply",
                            "--group", "a"], capture_output=True, text=True, timeout=180)
        say("  apply group a rc=%d" % r.returncode)
        for ln in (r.stdout or "").splitlines():
            say("    " + ln)

    p = Proc(pid)
    page = p.alloc(0x100)
    code, mark_off = build_trampoline(TARGET_FN)
    mark = page + 0x80
    code = bytearray(code)
    code[code.find(b"\xC7\x05") + 2:code.find(b"\xC7\x05") + 6] = struct.pack("<I", mark)
    if not p.wr(page, bytes(code)):
        say("  FAILED writing trampoline")
        return None
    say("  trampoline @0x%08X  mark @0x%08X  (call 0x%08X with ecx=0)"
        % (page, mark, TARGET_FN))

    t = p.thread(page)
    say("  remote thread created; polling 10s")
    code_out = None
    for _ in range(20):
        time.sleep(0.5)
        ec = wt.DWORD(0)
        if k32.GetExitCodeThread(t, ctypes.byref(ec)):
            code_out = ec.value
            if code_out != 259:      # STILL_ACTIVE
                break

    # look for an engine error dialog / any window of the process
    w = subprocess.run(["powershell", "-NoProfile", "-Command",
                        "(Get-Process -Id %d -ErrorAction SilentlyContinue | "
                        "Select-Object -ExpandProperty MainWindowTitle)" % pid],
                       capture_output=True, text=True, timeout=60)
    title = (w.stdout or "").strip().replace("\n", " | ")

    alive = pid in game_pids()
    got_mark = p.u32(mark) if alive else None
    crashed = EXCEPT.exists()
    say("  thread exit code: %s%s"
        % (code_out, "  (259=STILL_ACTIVE)" if code_out == 259 else ""))
    say("  main window     : %r" % title)
    say("  process alive   : %s" % alive)
    say("  marker written  : %s" % got_mark)
    say("  except.txt made : %s" % crashed)
    sig = None
    if crashed:
        txt = EXCEPT.read_bytes().decode("latin-1", "replace")
        eip = re.search(r"Eip\s*[:=]\s*([0-9A-Fa-f]{8})", txt)
        acc = re.search(r"Access address\s*[:=]\s*([0-9A-Fa-f]{8})", txt, re.I)
        sig = (eip.group(1).upper() if eip else None, acc.group(1).upper() if acc else None)
        say("  SIGNATURE       : Eip=%s Access=%s" % sig)

    try:
        k32.TerminateThread(t, 0)
    except Exception:
        pass
    left = kill_all()
    say("  residual: %r" % left)
    # leave the sandbox as we found it: if our run produced no new except.txt,
    # put the previous one back (the harness/next session expects it in place)
    if not EXCEPT.exists() and bak_holder.get("path") and bak_holder["path"].exists():
        os.replace(bak_holder["path"], EXCEPT)
        say("  restored previous except.txt")
    bak_holder["path"] = None
    return {"alive": alive, "mark": got_mark, "crash": crashed, "sig": sig,
            "thread_exit": code_out, "title": title}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", choices=["both", "control", "patched"], default="both")
    ap.add_argument("--fn", default="0x00724730",
                    help="target routine entry to call with ecx=0 (default 0x724730)")
    a = ap.parse_args()
    global TARGET_FN
    TARGET_FN = int(a.fn, 16)
    say("target function: 0x%08X" % TARGET_FN)

    out = {}
    if a.arm in ("both", "control"):
        out["control"] = run_arm("control(no hooks)", install_hooks=False)
    if a.arm in ("both", "patched"):
        out["patched"] = run_arm("patched(group a)", install_hooks=True)

    say("\n================ A/B VERDICT ================")
    AV = 0xC0000005
    c, p = out.get("control"), out.get("patched")
    if c:
        say("  control: thread_exit=0x%08X alive=%s mark=%s except=%s"
            % ((c["thread_exit"] or 0) & 0xFFFFFFFF, c["alive"], c["mark"], c["crash"]))
    if p:
        say("  patched: thread_exit=%s alive=%s mark=%s except=%s"
            % (p["thread_exit"], p["alive"], p["mark"], p["crash"]))
    if c and p:
        control_crashed = ((c["thread_exit"] or 0) & 0xFFFFFFFF) == AV and not c["alive"]
        patched_survived = p["alive"] and (p["mark"] == 1)
        ok = control_crashed and patched_survived
        say("  control crashed with AV (0xC0000005) : %s" % control_crashed)
        say("  patched returned safely (mark==1)    : %s" % patched_survived)
        say("  => guard prevents the crash: %s" % ("YES" if ok else "NO/INCONCLUSIVE"))
        return 0 if ok else 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
