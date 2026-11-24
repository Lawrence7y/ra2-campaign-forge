#!/usr/bin/env python3
"""W128c: verify the 6 null-guard hooks -- before and after installation.

  pre                                   check the on-disk image still has the
                                        original bytes at all 6 entries
  post --pid <pid>                      check a live gamemd: each entry is
                                        `E9 rel32` into a stub whose body is
                                        test ecx,ecx / jz / <relocated> / jmp rel32
                                        and whose jmp lands exactly on `resume`;
                                        also check the null path bytes.

READ-ONLY (post mode never writes process memory).
Exit code 0 = all checks passed.
"""
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


class Mem:
    def __init__(self, pid):
        self.h = k32.OpenProcess(0x0010 | 0x0400, False, pid)  # VM_READ|QUERY
        if not self.h:
            raise OSError("OpenProcess failed: %d" % ctypes.get_last_error())

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


def load_plan():
    d = json.load(open(os.path.join(HERE, "entries.json")))
    stubs = {s["fn"]: s for s in json.load(open(os.path.join(HERE, "stubs.json")))}
    plan = []
    for e in d["entries"]:
        s = stubs[e["fn"]]
        plan.append({
            "fn": int(e["fn"], 16),
            "fn_s": e["fn"],
            "reloc_len": e["relocate_len"],
            "reloc": bytes.fromhex(e["relocate_bytes"]),
            "resume": int(e["resume_at"], 16),
            "stub": bytes.fromhex(s["bytes"]),
            "jmp_off": s["jmp_rel32_off"],
            "pop": s["pop"],
            "ret_al": s["returns_al"],
        })
    return plan


def cmd_pre(plan):
    img = open(EXE, "rb").read()
    import pefile
    pe = pefile.PE(EXE, fast_load=True)
    ib = pe.OPTIONAL_HEADER.ImageBase
    ok = True
    print("%-12s %-8s %-24s %s" % ("entry", "len", "on-disk bytes", "verdict"))
    print("-" * 70)
    for p in plan:
        off = pe.get_offset_from_rva(p["fn"] - ib)
        got = img[off:off + p["reloc_len"]]
        good = got == p["reloc"]
        ok &= good
        print("%-12s %-8d %-24s %s" % (p["fn_s"], p["reloc_len"], got.hex(),
                                       "OK" if good else "MISMATCH exp " + p["reloc"].hex()))
    print("\nPRE-FLIGHT:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


def cmd_post(plan, pid):
    m = Mem(pid)
    ok = True
    print("%-12s %-10s %-10s %-6s %s" % ("entry", "jmp->stub", "stub body", "jmp ok", "verdict"))
    print("-" * 78)
    for p in plan:
        entry = m.rd(p["fn"], 8)
        if entry is None:
            print("%-12s <unreadable>" % p["fn_s"]); ok = False; continue
        if entry[0] != 0xE9:
            print("%-12s %-10s %-10s %-6s NOT-HOOKED (byte0=0x%02X)"
                  % (p["fn_s"], "-", "-", "-", entry[0]))
            ok = False
            continue
        rel = struct.unpack("<i", entry[1:5])[0]
        stub = (p["fn"] + 5 + rel) & 0xFFFFFFFF
        body = m.rd(stub, len(p["stub"]))
        if body is None:
            print("%-12s 0x%08X <unreadable stub>" % (p["fn_s"], stub)); ok = False; continue

        # expected body = template with jmp disp patched
        exp = bytearray(p["stub"])
        disp = (p["resume"] - (stub + p["jmp_off"] + 4)) & 0xFFFFFFFF
        exp[p["jmp_off"]:p["jmp_off"] + 4] = struct.pack("<I", disp)
        body_ok = bytes(body) == bytes(exp)

        # independently decode the jmp inside the stub
        jmp_at = p["jmp_off"] - 1
        assert body[jmp_at] == 0xE9, "stub does not carry jmp at expected offset"
        d2 = struct.unpack("<i", body[jmp_at + 1:jmp_at + 5])[0]
        target = (stub + jmp_at + 5 + d2) & 0xFFFFFFFF
        jmp_ok = (target == p["resume"])

        # entry padding must be 0x90 beyond the E9
        pad_ok = all(b == 0x90 for b in entry[5:p["reloc_len"]]) if p["reloc_len"] > 5 else True

        good = body_ok and jmp_ok and pad_ok
        ok &= good
        print("%-12s 0x%08X %-10s %-6s %s"
              % (p["fn_s"], stub, "match" if body_ok else "DIFF",
                 "yes" if jmp_ok else "NO->0x%08X" % target,
                 "OK" if good else "FAIL"))
        if not body_ok:
            print("        expected: %s" % bytes(exp).hex())
            print("        actual  : %s" % bytes(body).hex())
        if not jmp_ok:
            print("        resume should be 0x%08X" % p["resume"])
    print("\nPOST-CHECK:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


def main(argv):
    plan = load_plan()
    if len(argv) < 2:
        print(__doc__)
        return 2
    mode = argv[1]
    if mode == "pre":
        return cmd_pre(plan)
    if mode == "post":
        pid = None
        for i, a in enumerate(argv):
            if a == "--pid" and i + 1 < len(argv):
                pid = int(argv[i + 1])
        if pid is None:
            print("post needs --pid <pid>")
            return 2
        return cmd_post(plan, pid)
    print("unknown mode", mode)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
