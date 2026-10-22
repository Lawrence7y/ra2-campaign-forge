#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VERIFY_FRAME.py -- independent frame proof for the 0x724737 crash.

Question: which of the 30 direct E8 call sites of 0x724730 is on the stack?

Method (no trust in the briefing, everything re-derived from the two inputs):
  1. parse the "Stack dump" block of ra2youli\\except.txt into {addr: value}
  2. the prologue sub esp,0xc / push ebp / mov ebp,ecx / push esi moves ESP
     down by 0xc+4+4 = 0x14, so the return-address slot is Esp+0x14
  3. read that slot -> return address -> call site = retaddr-5 -> check E8 rel32
  4. brute-force scan every E8 in .text for rel32 resolving to 0x724730
  5. prove the *other* plausible site (0x4A8B75) is NOT the one taken

PE notes honoured: ImageBase is read at e_lfanew+0x18+0x1C (not a fixed 0x34),
section VirtualAddress is an RVA and VA = RVA + ImageBase.

Exit code 0 only when every check passes.
"""

import os
import re
import struct
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
EXE = os.path.join(ROOT, "ra2youli", "gamemd.exe")
EXC = os.path.join(ROOT, "ra2youli", "except.txt")

TARGET_FUNC = 0x00724730      # function under investigation
PROLOGUE_LEN = 0x0C + 4 + 4   # sub esp,0xc ; push ebp ; push esi  == 0x14
SITE_EXPECTED = 0x00654413    # candidate call site from the briefing
RET_EXPECTED = 0x00654418     # = SITE_EXPECTED + 5
SITE_RIVAL = 0x004A8B75       # the other plausible call site
RET_RIVAL = SITE_RIVAL + 5    # 0x004A8B7A
EXPECTED_CALLERS = 30

CHECKS = []


def check(cid, ok, desc, expected, actual, required=True):
    CHECKS.append(
        dict(id=cid, ok=bool(ok), desc=desc, expected=expected,
             actual=actual, required=required)
    )
    tag = "PASS" if ok else ("FAIL" if required else "INFO-FAIL")
    print("[%s] %-4s %-62s exp=%s got=%s" % (tag, cid, desc, expected, actual))
    return bool(ok)


def banner(title):
    print("")
    print("=" * 78)
    print(title)
    print("=" * 78)


# --------------------------------------------------------------------------
# PE parsing
# --------------------------------------------------------------------------
class PE(object):
    def __init__(self, path):
        with open(path, "rb") as fh:
            self.data = fh.read()
        d = self.data
        if d[:2] != b"MZ":
            raise SystemExit("not an MZ image: %s" % path)
        self.e_lfanew = struct.unpack_from("<I", d, 0x3C)[0]
        if d[self.e_lfanew:self.e_lfanew + 4] != b"PE\0\0":
            raise SystemExit("bad PE signature at e_lfanew=0x%x" % self.e_lfanew)
        coff = self.e_lfanew + 4                       # COFF file header
        self.num_sec = struct.unpack_from("<H", d, coff + 2)[0]
        self.opt_size = struct.unpack_from("<H", d, coff + 16)[0]
        opt = coff + 20                                # optional header
        self.magic = struct.unpack_from("<H", d, opt)[0]
        if self.magic != 0x10B:
            raise SystemExit("expected PE32 (0x10b), got 0x%x" % self.magic)
        # ImageBase lives at opt+0x1c -- NOT a fixed file offset of 0x34.
        self.image_base = struct.unpack_from("<I", d, opt + 0x1C)[0]
        self.entry = self.image_base + struct.unpack_from("<I", d, opt + 0x10)[0]
        self.sections = []
        sec = opt + self.opt_size                      # section table
        for i in range(self.num_sec):
            o = sec + i * 40
            name = d[o:o + 8].rstrip(b"\0").decode("ascii", "replace")
            vsize, vaddr, rsize, rptr = struct.unpack_from("<IIII", d, o + 8)
            self.sections.append(dict(name=name, vsize=vsize, vaddr=vaddr,
                                      rsize=rsize, rptr=rptr))

    def sec(self, name):
        for s in self.sections:
            if s["name"] == name:
                return s
        return None

    def span(self, s):
        """Number of bytes that are actually backed by file data."""
        n = s["rsize"]
        if s["vsize"] and s["vsize"] < n:
            n = s["vsize"]
        return n

    def va_to_off(self, va):
        rva = va - self.image_base
        for s in self.sections:
            if s["vaddr"] <= rva < s["vaddr"] + max(s["vsize"], s["rsize"]):
                delta = rva - s["vaddr"]
                if delta >= self.span(s):
                    return None
                return s["rptr"] + delta
        return None

    def read(self, va, n):
        o = self.va_to_off(va)
        if o is None:
            return None
        return self.data[o:o + n]

    def u8(self, va):
        b = self.read(va, 1)
        return None if not b else b[0]

    def u32(self, va):
        b = self.read(va, 4)
        return None if b is None or len(b) < 4 else struct.unpack("<I", b)[0]

    def which_section(self, va):
        rva = va - self.image_base
        for s in self.sections:
            if s["vaddr"] <= rva < s["vaddr"] + max(s["vsize"], s["rsize"]):
                return s["name"]
        return None

    def callers_of(self, target, section_name=".text"):
        """Every E8 rel32 inside `section_name` whose target is `target`."""
        s = self.sec(section_name)
        if s is None:
            raise SystemExit("section %s not found" % section_name)
        base_va = self.image_base + s["vaddr"]
        start = s["rptr"]
        end = start + self.span(s) - 5
        hits = []
        d = self.data
        for o in range(start, end + 1):
            if d[o] != 0xE8:
                continue
            site = base_va + (o - start)
            rel = struct.unpack_from("<i", d, o + 1)[0]
            if site + 5 + rel == target:
                hits.append(site)
        return hits


# --------------------------------------------------------------------------
# except.txt parsing
# --------------------------------------------------------------------------
def parse_except(path):
    with open(path, "rb") as fh:
        raw = fh.read()
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        text = raw.decode("latin-1")

    info = {}
    m = re.search(r"Exception occurred at ([0-9A-Fa-f]{8})", text)
    if m:
        info["exc_at"] = int(m.group(1), 16)
    m = re.search(r"Access address:\s*([0-9A-Fa-f]+)\s+was\s+(\w+)", text)
    if m:
        info["access_addr"] = int(m.group(1), 16)
        info["access_kind"] = m.group(2)
    m = re.search(r"Bytes at CS:EIP\s*\(\s*([0-9A-Fa-f]{8})\s*\)\s*:\s*([0-9A-Fa-f ]+)",
                  text)
    if m:
        info["bytes_at_eip_va"] = int(m.group(1), 16)
        info["bytes_at_eip"] = bytes(int(x, 16) for x in m.group(2).split())

    for reg in ("Eip", "Esp", "Ebp", "Eax", "Ebx", "Ecx", "Edx", "Esi", "Edi"):
        m = re.search(r"\b%s:\s*([0-9A-Fa-f]{8})" % reg, text)
        if m:
            info[reg.lower()] = int(m.group(1), 16)

    # Stack dump lines:  "00F9A358: 00654418"  or  "00F9A344: 00000278 DATA_PTR"
    # (a trailing non-hex marker such as DATA_PTR may follow the value).
    stack = {}
    in_dump = False
    for line in text.splitlines():
        if "Stack dump" in line:
            in_dump = True
            continue
        if not in_dump:
            continue
        m = re.match(r"^\s*([0-9A-Fa-f]{8}):\s+([0-9A-Fa-f]{8})(\s+\S+)?\s*$", line)
        if m:
            stack[int(m.group(1), 16)] = int(m.group(2), 16)
    info["stack"] = stack
    info["raw_text"] = text
    return info


# --------------------------------------------------------------------------
def main():
    banner("INPUTS")
    print("gamemd.exe : %s" % EXE)
    print("except.txt : %s" % EXC)
    for p in (EXE, EXC):
        if not os.path.isfile(p):
            raise SystemExit("missing input: %s" % p)

    pe = PE(EXE)
    exc = parse_except(EXC)
    st = exc["stack"]

    banner("STEP 0  PE headers (ImageBase @ e_lfanew+0x18+0x1C)")
    print("e_lfanew      = 0x%08X" % pe.e_lfanew)
    print("opt magic     = 0x%04X (PE32)" % pe.magic)
    print("ImageBase     = 0x%08X" % pe.image_base)
    print("EntryPoint VA = 0x%08X" % pe.entry)
    print("sections      = %d" % pe.num_sec)
    for s in pe.sections:
        print("  %-8s RVA 0x%08X  VSize 0x%08X  RawPtr 0x%08X  RawSize 0x%08X"
              % (s["name"], s["vaddr"], s["vsize"], s["rptr"], s["rsize"]))

    banner("STEP 1  except.txt -> stack dict")
    print("Eip=0x%08X Esp=0x%08X Ebp=0x%08X Esi=0x%08X Edi=0x%08X"
          % (exc.get("eip", 0), exc.get("esp", 0), exc.get("ebp", 0),
             exc.get("esi", 0), exc.get("edi", 0)))
    print("access address = 0x%X (%s)"
          % (exc.get("access_addr", 0), exc.get("access_kind", "?")))
    print("stack entries  = %d, range 0x%08X..0x%08X"
          % (len(st), min(st), max(st)))
    check("S1", len(st) > 0 and exc.get("esp") == min(st),
          "stack dict parsed; first slot == Esp",
          "Esp == min(stack)", "n=%d min=0x%08X esp=0x%08X"
          % (len(st), min(st), exc.get("esp", 0)))

    # ---- frame geometry -------------------------------------------------
    esp = exc["esp"]
    ret_slot = esp + PROLOGUE_LEN
    arg_slot = ret_slot + 4
    local_lo = esp + 0x08          # after push ebp(0x348) push esi(0x344)...
    banner("STEP 2  frame geometry")
    print("prologue: sub esp,0xc ; push ebp ; mov ebp,ecx ; push esi")
    print("stack delta at fault = 0xc + 4 + 4 = 0x14")
    print("Esp                = 0x%08X" % esp)
    print("  [Esp+0x00] saved esi      -> 0x%08X" % esp)
    print("  [Esp+0x04] saved ebp      -> 0x%08X" % (esp + 4))
    print("  [Esp+0x08..0x10] locals   -> 0x%08X..0x%08X" % (esp + 8, esp + 0x10))
    print("  [Esp+0x14] return address -> 0x%08X" % ret_slot)
    print("  [Esp+0x18] argument 1     -> 0x%08X" % arg_slot)

    # ---- required check 2 ----------------------------------------------
    banner("STEP 3  required check 2: return-address slot")
    got_ret = st.get(ret_slot)
    check("C2", got_ret == RET_EXPECTED,
          "stack[0x%08X] == 0x%08X (return addr)" % (ret_slot, RET_EXPECTED),
          "0x%08X" % RET_EXPECTED,
          "None" if got_ret is None else "0x%08X" % got_ret)

    # ---- required check 3 ----------------------------------------------
    banner("STEP 4  required check 3: 0x654413 is an E8 rel32 -> 0x724730")
    site = RET_EXPECTED - 5
    raw5 = pe.read(site, 5)
    op = pe.u8(site)
    rel = None if raw5 is None or len(raw5) < 5 else struct.unpack_from("<i", raw5, 1)[0]
    tgt = None if rel is None else (site + 5 + rel) & 0xFFFFFFFF
    print("call site      = 0x%08X  (return 0x%08X - 5)" % (site, RET_EXPECTED))
    print("bytes          = %s" % ("None" if raw5 is None else raw5.hex(" ").upper()))
    print("opcode         = %s" % ("None" if op is None else "0x%02X" % op))
    print("rel32          = %s" % ("None" if rel is None else "0x%X (%d)" % (rel & 0xFFFFFFFF, rel)))
    print("target         = %s" % ("None" if tgt is None else "0x%08X" % tgt))
    print("section        = %s" % pe.which_section(site))
    check("C3a", op == 0xE8,
          "byte at 0x%08X == 0xE8 (call rel32)" % site,
          "0xE8", "None" if op is None else "0x%02X" % op)
    check("C3b", tgt == TARGET_FUNC,
          "E8 target == 0x%08X" % TARGET_FUNC,
          "0x%08X" % TARGET_FUNC,
          "None" if tgt is None else "0x%08X" % tgt)

    # ---- required check 4 ----------------------------------------------
    banner("STEP 5  required check 4: full .text E8 rel32 sweep for 0x724730")
    callers = pe.callers_of(TARGET_FUNC, ".text")
    print("callers found = %d" % len(callers))
    for i, c in enumerate(callers):
        print("  [%2d] 0x%08X  %s" % (i + 1, c, pe.read(c, 5).hex(" ").upper()))
    check("C4", site in callers,
          "0x%08X is among the direct E8 callers of 0x%08X" % (site, TARGET_FUNC),
          "present", "present" if site in callers else "ABSENT")

    # ---- required check 5 ----------------------------------------------
    banner("STEP 6  required check 5: the rival return address is NOT on the stack")
    print("rival site  = 0x%08X" % SITE_RIVAL)
    print("rival ret   = 0x%08X" % RET_RIVAL)
    rraw = pe.read(SITE_RIVAL, 5)
    rrel = struct.unpack_from("<i", rraw, 1)[0] if rraw and len(rraw) == 5 else None
    rtgt = None if rrel is None else (SITE_RIVAL + 5 + rrel) & 0xFFFFFFFF
    print("rival bytes = %s  -> target 0x%08X (a genuine caller)"
          % (rraw.hex(" ").upper(), rtgt or 0))
    vals = set(st.values())
    in_vals = RET_RIVAL in vals
    literal = ("%08X" % RET_RIVAL) in exc["raw_text"].upper()
    print("0x%08X in stack values : %s" % (RET_RIVAL, in_vals))
    print("0x%08X in except.txt   : %s" % (RET_RIVAL, literal))
    print("stack slots holding it : %s"
          % ([hex(k) for k, v in st.items() if v == RET_RIVAL] or "none"))
    # no slot V with V-5 == rival site either
    via_minus5 = [hex(k) for k, v in st.items() if ((v - 5) & 0xFFFFFFFF) == SITE_RIVAL]
    print("slots with value-5 == 0x%08X : %s" % (SITE_RIVAL, via_minus5 or "none"))
    check("C5", (not in_vals) and (not literal) and (not via_minus5),
          "0x%08X absent from the stack dump" % RET_RIVAL,
          "absent", "PRESENT" if (in_vals or literal or via_minus5) else "absent")

    # ---- required check 6 ----------------------------------------------
    banner("STEP 7  required check 6: saved Esi == 0x278")
    got_esi = st.get(esp)
    check("C6", got_esi == exc.get("esi") == 0x278,
          "stack[0x%08X] == Esi == 0x278 (push esi)" % esp,
          "0x278", "None" if got_esi is None else "0x%08X" % got_esi)

    # ---- required check 7 ----------------------------------------------
    banner("STEP 8  required check 7: single argument == 0xF2")
    got_arg = st.get(arg_slot)
    check("C7", got_arg == 0xF2,
          "stack[0x%08X] == 0xF2 (pushed argument)" % arg_slot,
          "0x000000F2", "None" if got_arg is None else "0x%08X" % got_arg)

    # ---- corroborating extras ------------------------------------------
    banner("STEP 9  corroboration (extra, not from the briefing)")

    check("E1", len(callers) == EXPECTED_CALLERS,
          "direct E8 caller count of 0x%08X in .text" % TARGET_FUNC,
          str(EXPECTED_CALLERS), str(len(callers)))

    # the rival is a real call site, which is why the exclusion matters
    check("E2", rrel is not None and rtgt == TARGET_FUNC,
          "0x%08X is itself a genuine E8 -> 0x%08X" % (SITE_RIVAL, TARGET_FUNC),
          "0x%08X" % TARGET_FUNC,
          "None" if rtgt is None else "0x%08X" % rtgt)

    # argument discriminator: site 0x654413 pushes 0xf2, site 0x4A8B75 pushes 0x1f4
    push_site = None
    for back in range(1, 40):
        if pe.u8(site - back) == 0x68:      # push imm32
            imm = pe.u32(site - back + 1)
            if imm is not None and imm < 0x10000:
                push_site = (site - back, imm)
                break
    rpush = None
    for back in range(1, 60):
        if pe.u8(SITE_RIVAL - back) == 0x68:
            imm = pe.u32(SITE_RIVAL - back + 1)
            if imm is not None and imm < 0x10000:
                rpush = (SITE_RIVAL - back, imm)
                break
    print("nearest push imm32 before 0x%08X : %s"
          % (site, "none" if not push_site else "0x%08X push 0x%X" % push_site))
    print("nearest push imm32 before 0x%08X : %s"
          % (SITE_RIVAL, "none" if not rpush else "0x%08X push 0x%X" % rpush))
    print("stack argument slot holds 0x%X" % (got_arg if got_arg is not None else -1))
    check("E3", push_site is not None and push_site[1] == got_arg
          and (rpush is None or rpush[1] != got_arg),
          "arg slot matches 0x%08X's push 0x%X, not 0x%08X's"
          % (site, got_arg or 0, SITE_RIVAL),
          "0x%X" % (got_arg or 0),
          "site=0x%X rival=%s"
          % (push_site[1] if push_site else -1,
             ("0x%X" % rpush[1]) if rpush else "none"))

    # crash site self-consistency: mov eax,[ebp+0x250] with ebp=0 -> fault 0x250
    eip = exc.get("eip")
    ebp = exc.get("ebp")
    bytes_ok = False
    if eip is not None and exc.get("bytes_at_eip"):
        live = pe.read(eip, len(exc["bytes_at_eip"]))
        bytes_ok = live == exc["bytes_at_eip"]
        print("Eip 0x%08X bytes live=%s  dump=%s  match=%s"
              % (eip, live.hex(" ").upper() if live else "None",
                 exc["bytes_at_eip"].hex(" ").upper(), bytes_ok))
    check("E4", bytes_ok,
          "bytes at Eip match except.txt (faulting instruction is in the image)",
          "identical", "identical" if bytes_ok else "differ")
    disp = pe.u32(eip + 2) if eip is not None else None
    expected_fault = ((ebp or 0) + (disp if disp is not None and disp < 0x1000 else 0)) & 0xFFFFFFFF
    print("instruction at Eip = mov eax,[ebp+0x%X]; ebp=0x%X -> read 0x%X"
          % (disp or 0, ebp or 0, expected_fault))
    check("E5", disp is not None and expected_fault == exc.get("access_addr"),
          "faulting access [ebp+disp] reproduces Access address 0x%X"
          % exc.get("access_addr", 0),
          "0x%X" % exc.get("access_addr", 0), "0x%X" % expected_fault)

    # the slot just below the return address holds 0x6543B1 -- a local, not a frame
    below = st.get(ret_slot - 4)
    print("[Esp+0x10] = 0x%08X (0x6543B1 is the return of call 0x6543AC -> 0x4E1A20,"
          " stored as a local inside the 0xc-byte local area)" % (below or 0))
    check("E6", below is not None and pe.which_section(below) is not None
          and (esp + 8) <= (ret_slot - 4) <= (esp + 0x10),
          "slot below the return address is inside the local area, not a call frame",
          "local slot", "0x%08X @ local area" % (below or 0), required=False)

    # ---- summary --------------------------------------------------------
    req = [c for c in CHECKS if c["required"]]
    passed = [c for c in req if c["ok"]]
    failed = [c for c in req if not c["ok"]]
    total = len(req)

    banner("SUMMARY")
    for c in CHECKS:
        if not c["ok"]:
            print("FAILED: %-4s %s  expected=%s actual=%s"
                  % (c["id"], c["desc"], c["expected"], c["actual"]))
    print("")
    print("conclusion: crash entered 0x%08X from call site 0x%08X"
          % (TARGET_FUNC, site))
    print("            (return address 0x%08X at stack slot 0x%08X)"
          % (RET_EXPECTED, ret_slot))
    print("")
    print("checks passed: %d/%d" % (len(passed), total))
    print("RESULT: %s" % ("ALL PASS" if not failed else "HAS FAILURES"))
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
