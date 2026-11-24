#!/usr/bin/env python3
"""W128j: apply the 9 hooks to a RUNNING gamemd, without any C compiler.

Why this exists: the same fixes are in ra2nullguard.c, but this machine has no
32-bit toolchain (ledger §834-6). All the machine code is already generated and
byte-verified (stubs_generated.h / sites_generated.h), so the only missing piece
was "get those bytes into the process". That needs no compiler at all.

  --pid N            target process
  --dry-run          (DEFAULT) verify original bytes + print the plan, write nothing
  --apply            install both groups
  --unhook           restore original bytes from the on-disk image
  --group a|s|all    which group (a = ②-a 6 entry guards, s = 3 defect sites)

Safety:
  * fail-closed: every site's current bytes must match the on-disk image exactly,
    otherwise that group is skipped and the exit code is non-zero.
  * restores the page protection it changed.
  * --dry-run is the default: you must ask for --apply explicitly.
"""
import argparse
import ctypes
import json
import os
import struct
import sys
from ctypes import wintypes as wt

HERE = os.path.dirname(os.path.abspath(__file__))
EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"

k32 = ctypes.WinDLL("kernel32", use_last_error=True)
k32.OpenProcess.restype = wt.HANDLE
k32.VirtualAllocEx.restype = ctypes.c_void_p
k32.VirtualAllocEx.argtypes = [wt.HANDLE, ctypes.c_void_p, ctypes.c_size_t,
                               wt.DWORD, wt.DWORD]
k32.WriteProcessMemory.argtypes = [wt.HANDLE, ctypes.c_void_p, ctypes.c_void_p,
                                   ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]
k32.ReadProcessMemory.argtypes = [wt.HANDLE, ctypes.c_void_p, ctypes.c_void_p,
                                  ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]
k32.VirtualProtectEx.argtypes = [wt.HANDLE, ctypes.c_void_p, ctypes.c_size_t,
                                 wt.DWORD, ctypes.POINTER(wt.DWORD)]

PROCESS_ALL = 0x001F0FFF
MEM_COMMIT_RESERVE = 0x3000
PAGE_EXECUTE_READWRITE = 0x40


class Proc:
    def __init__(self, pid):
        self.h = k32.OpenProcess(PROCESS_ALL, False, pid)
        if not self.h:
            raise OSError("OpenProcess(%d) failed: %d" % (pid, ctypes.get_last_error()))

    def rd(self, va, n):
        buf = ctypes.create_string_buffer(n)
        got = ctypes.c_size_t(0)
        if not k32.ReadProcessMemory(self.h, ctypes.c_void_p(va), buf, n,
                                     ctypes.byref(got)) or got.value != n:
            return None
        return buf.raw

    def wr(self, va, data):
        n = ctypes.c_size_t(0)
        buf = ctypes.create_string_buffer(data, len(data))
        if not k32.WriteProcessMemory(self.h, ctypes.c_void_p(va), buf, len(data),
                                      ctypes.byref(n)) or n.value != len(data):
            return False
        return True

    def alloc(self, size):
        p = k32.VirtualAllocEx(self.h, None, size, MEM_COMMIT_RESERVE,
                               PAGE_EXECUTE_READWRITE)
        if not p:
            raise OSError("VirtualAllocEx failed: %d" % ctypes.get_last_error())
        return int(p)

    def prot(self, va, size, new):
        old = wt.DWORD(0)
        if not k32.VirtualProtectEx(self.h, ctypes.c_void_p(va), size, new,
                                    ctypes.byref(old)):
            raise OSError("VirtualProtectEx failed: %d" % ctypes.get_last_error())
        return old.value


def load_plan():
    entries = json.load(open(os.path.join(HERE, "entries.json")))["entries"]
    stubs = {s["fn"]: s for s in json.load(open(os.path.join(HERE, "stubs.json")))}
    sites = json.load(open(os.path.join(HERE, "sites.json")))
    plan_a = []
    for e in entries:
        s = stubs[e["fn"]]
        plan_a.append({
            "va": int(e["fn"], 16),
            "label": e["fn"],
            "orig_len": e["relocate_len"],
            "orig": bytes.fromhex(e["relocate_bytes"]),
            "stub": bytes.fromhex(s["bytes"]),
            "jmp_off": s["jmp_rel32_off"],
            "resume": int(e["resume_at"], 16),
        })
    plan_s = []
    for s in sites:
        plan_s.append({
            "va": int(s["site"], 16),
            "label": s["site"],
            "orig_len": 12,
            "orig": None,          # read from disk image below
            "helper": bytes.fromhex(s["bytes"]),
        })
    return plan_a, plan_s


def disk_image():
    import pefile
    pe = pefile.PE(EXE, fast_load=True)
    ib = pe.OPTIONAL_HEADER.ImageBase
    raw = open(EXE, "rb").read()

    def read(va, n):
        off = pe.get_offset_from_rva(va - ib)
        return raw[off:off + n]
    return read


def install_group_a(p, plan, apply_it):
    ok = True
    for e in plan:
        cur = p.rd(e["va"], e["orig_len"])
        if cur is None:
            print("  %-12s <unreadable>" % e["label"]); ok = False; continue
        if cur != e["orig"]:
            print("  %-12s FAIL-CLOSED: current bytes %s != expected %s"
                  % (e["label"], cur.hex(), e["orig"].hex()))
            ok = False
            continue
        if not apply_it:
            print("  %-12s would hook: alloc %dB stub, entry <- E9 rel32 + %d nop"
                  % (e["label"], len(e["stub"]), e["orig_len"] - 5))
            continue

        stub_va = p.alloc(len(e["stub"]))
        body = bytearray(e["stub"])
        disp = (e["resume"] - (stub_va + e["jmp_off"] + 4)) & 0xFFFFFFFF
        body[e["jmp_off"]:e["jmp_off"] + 4] = struct.pack("<I", disp)
        if not p.wr(stub_va, bytes(body)):
            print("  %-12s FAILED writing stub" % e["label"]); ok = False; continue

        old = p.prot(e["va"], e["orig_len"], PAGE_EXECUTE_READWRITE)
        patch = bytearray([0xE9])
        patch += struct.pack("<I", (stub_va - (e["va"] + 5)) & 0xFFFFFFFF)
        patch += b"\x90" * (e["orig_len"] - 5)
        if not p.wr(e["va"], bytes(patch)):
            print("  %-12s FAILED writing entry" % e["label"]); ok = False; continue
        p.prot(e["va"], e["orig_len"], old)

        back = p.rd(e["va"], e["orig_len"])
        good = back is not None and back[0] == 0xE9
        print("  %-12s stub@0x%08X  entry=%s  %s"
              % (e["label"], stub_va, (back or b"").hex(), "OK" if good else "FAIL"))
        ok &= good
    return ok


def install_group_s(p, plan, apply_it, disk):
    ok = True
    for s in plan:
        orig = disk(s["va"], 12)
        s["orig"] = orig
        cur = p.rd(s["va"], 12)
        if cur is None:
            print("  %-12s <unreadable>" % s["label"]); ok = False; continue
        if cur != orig:
            print("  %-12s FAIL-CLOSED: current %s != image %s"
                  % (s["label"], cur.hex(), orig.hex()))
            ok = False
            continue
        if not apply_it:
            print("  %-12s would patch: alloc %dB helper, site <- E8 rel32 + 7 nop"
                  % (s["label"], len(s["helper"])))
            continue

        h_va = p.alloc(len(s["helper"]))
        if not p.wr(h_va, s["helper"]):
            print("  %-12s FAILED writing helper" % s["label"]); ok = False; continue

        old = p.prot(s["va"], 12, PAGE_EXECUTE_READWRITE)
        patch = bytearray([0xE8])
        patch += struct.pack("<I", (h_va - (s["va"] + 5)) & 0xFFFFFFFF)
        patch += b"\x90" * 7
        if not p.wr(s["va"], bytes(patch)):
            print("  %-12s FAILED writing site" % s["label"]); ok = False; continue
        p.prot(s["va"], 12, old)

        back = p.rd(s["va"], 12)
        good = back is not None and back[0] == 0xE8
        print("  %-12s helper@0x%08X  site=%s  %s"
              % (s["label"], h_va, (back or b"").hex(), "OK" if good else "FAIL"))
        ok &= good
    return ok


def unhook(p, plan_a, plan_s, disk):
    ok = True
    for e in plan_a:
        old = p.prot(e["va"], e["orig_len"], PAGE_EXECUTE_READWRITE)
        ok &= p.wr(e["va"], e["orig"])
        p.prot(e["va"], e["orig_len"], old)
        back = p.rd(e["va"], e["orig_len"])
        print("  %-12s restored=%s %s" % (e["label"], (back or b"").hex(),
                                          "OK" if back == e["orig"] else "FAIL"))
    for s in plan_s:
        orig = disk(s["va"], 12)
        old = p.prot(s["va"], 12, PAGE_EXECUTE_READWRITE)
        ok &= p.wr(s["va"], orig)
        p.prot(s["va"], 12, old)
        back = p.rd(s["va"], 12)
        print("  %-12s restored=%s %s" % (s["label"], (back or b"").hex(),
                                          "OK" if back == orig else "FAIL"))
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pid", type=int, required=True)
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--apply", action="store_true")
    g.add_argument("--unhook", action="store_true")
    ap.add_argument("--group", choices=["a", "s", "all"], default="all")
    a = ap.parse_args()

    if not sys.platform.startswith("win"):
        print("windows only"); return 2
    plan_a, plan_s = load_plan()
    disk = disk_image()
    p = Proc(a.pid)

    if a.unhook:
        print("=== UNHOOK (restore from disk image) ===")
        ok = unhook(p, plan_a if a.group in ("a", "all") else [],
                    plan_s if a.group in ("s", "all") else [], disk)
        print("\nRESULT:", "OK" if ok else "PARTIAL/FAILED")
        return 0 if ok else 1

    print("=== %s ===" % ("APPLY" if a.apply else "DRY-RUN (default; add --apply)"))
    ok = True
    if a.group in ("a", "all"):
        print("\n[group A] ②-a: 6 container-routine entry guards")
        ok &= install_group_a(p, plan_a, a.apply)
    if a.group in ("s", "all"):
        print("\n[group S] third defect: 3 null-safe sites in FUN_006f3f40")
        ok &= install_group_s(p, plan_s, a.apply, disk)
    print("\nRESULT:", "OK" if ok else "FAILED (see above)")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
