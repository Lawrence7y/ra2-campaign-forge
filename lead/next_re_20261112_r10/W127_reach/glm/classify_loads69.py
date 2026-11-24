# classify_loads69.py (v2) -- W127_reach "loads69" static audit for gamemd.exe
#
# Goal: find every `mov ecx, ds:[0x00887368]` (8B 0D 68 73 88 00) in .text,
# classify each site:
#   A call_del : call/jmp to FUN_00724730 (0x724730) with this=ecx before ecx modified
#   B guarded  : test/cmp on ecx (or copy) whose conditional jump provably skips
#                the first use of the value (per task definition; the compared
#                operand is reported: proven-zero vs register-unproven)
#   C other    : anything else (deref, pass to other fn, store, live-out, ...)
#
# Method (hard requirements):
#   * pefile; buffer index = VA - 0x400000 (get_memory_mapped_image()[0] == ImageBase)
#     -- verified against MZ header, crash-site decode and known-20 load bytes.
#   * capstone skipdata=True everywhere (no silent early stop).
#   * every site disassembled forward starting exactly at the load instruction
#     address; semantic window = 64 bytes (read 80 raw bytes so the window tail
#     is never a truncated instruction -- v1's 20 "exceptions" were exactly
#     buffer-truncation artifacts, verified by diagnose_skip.py).
#   * read-only on the exe; writes only into OUT_DIR.
#
# Outputs: loads69.tsv, loads69_report.txt (this script's own console log).

import os, sys, traceback, hashlib
from collections import Counter

import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

try:
    from capstone.x86 import X86_OP_IMM, X86_OP_MEM, X86_OP_REG
except Exception:
    from capstone import X86_OP_IMM, X86_OP_MEM, X86_OP_REG

EXE_PATH    = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
OUT_DIR     = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W127_reach\glm"
TSV_PATH    = os.path.join(OUT_DIR, "loads69.tsv")
REPORT_PATH = os.path.join(OUT_DIR, "loads69_report.txt")

EXPECT_SHA256 = "73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476"

IMAGE_BASE  = 0x400000
GLOBAL_VA   = 0x00887368
PATTERN     = bytes([0x8B, 0x0D, 0x68, 0x73, 0x88, 0x00])   # mov ecx, ds:[0x00887368]
DISP        = bytes([0x68, 0x73, 0x88, 0x00])
DEL_FUNC    = 0x00724730
TEXT_START  = 0x00401000
TEXT_END    = 0x007E038D        # inclusive, established premise
KNOWN20 = [
    0x654405, 0x6ABFF4, 0x6AC031, 0x6D0613, 0x6D0629, 0x6D0659, 0x6D0896,
    0x6D08A8, 0x6D0935, 0x6D09EC, 0x6D127C, 0x6D12F1, 0x6D1367, 0x6D13DC,
    0x6D153A, 0x6D1551, 0x6D15FA, 0x6D1627, 0x6D16BB, 0x6D16D2,
]
WINDOW      = 64    # semantic analysis window from load_va
WINDOW_READ = 80    # raw bytes fed to capstone (avoids tail truncation)

md  = Cs(CS_ARCH_X86, CS_MODE_32); md.skipdata = True; md.detail = True
mdf = Cs(CS_ARCH_X86, CS_MODE_32); mdf.skipdata = True

REPORT = []
def out(s=""):
    print(s)
    REPORT.append(s)

REGN = {"eax": "eax", "ax": "eax", "al": "eax", "ah": "eax",
        "ebx": "ebx", "bx": "ebx", "bl": "ebx", "bh": "ebx",
        "ecx": "ecx", "cx": "ecx", "cl": "ecx", "ch": "ecx",
        "edx": "edx", "dx": "edx", "dl": "edx", "dh": "edx",
        "esi": "esi", "si": "esi", "edi": "edi", "di": "edi",
        "ebp": "ebp", "bp": "ebp", "esp": "esp", "sp": "esp"}

def rn(rid):
    if not rid:
        return None
    return REGN.get(md.reg_name(rid).lower())

ZEROish    = {"je", "jz", "jbe", "jle"}                # taken when value == cmp operand
NONZEROish = {"jne", "jnz", "ja", "jae", "jg", "jge"}  # taken when value != cmp operand
SIGNish    = {"js", "jns", "jp", "jnp"}
JCC_ALL    = ZEROish | NONZEROish | SIGNish
ARITH = {"add","sub","adc","sbb","and","or","xor","neg","not","inc","dec",
         "shl","shr","sar","rol","ror","rcl","rcr","shld","shrd",
         "imul","mul","idiv","div","xadd","bsf","bsr","bt","bts","btr","btc"}
FLAG_WRITERS = ARITH | {"test", "cmp"}
NOOPS = {"nop", "pause", "wait", "fnop"}

pe  = pefile.PE(EXE_PATH, fast_load=True)
img = pe.get_memory_mapped_image()

def rd(va, n):
    off = va - IMAGE_BASE          # buffer index 0 == VA ImageBase (0x400000)
    assert 0 <= off and off + n <= len(img), "VA %#x read out of mapped image" % va
    return bytes(img[off:off + n])

def mem_hits(ops, holders):
    hits = []
    for op in ops:
        if op.type == X86_OP_MEM:
            b = rn(op.mem.base)
            x = rn(op.mem.index)
            if (b and b in holders) or (x and x in holders):
                hits.append(op)
    return hits

def abs_global(ops):
    for op in ops:
        if op.type == X86_OP_MEM and op.mem.base == 0 and op.mem.index == 0 \
           and (op.mem.disp & 0xFFFFFFFF) == GLOBAL_VA:
            return True
    return False

def analyze(load_va):
    """Walk forward from the load instruction (exact start); semantic window 64B."""
    insns = list(md.disasm(rd(load_va, WINDOW_READ), load_va))
    ev = ["%#x  mov ecx, dword ptr [0x887368]   <-- LOAD (8b 0d 68 73 88 00)" % load_va]
    holders = {"ecx"}        # regs currently holding the loaded value
    zeros   = set()          # regs provably zero within the window (after the load)
    state = {"cls": None, "sub": None, "call_target": None}
    notes, del_calls = [], []
    pending_test = None       # (addr, text, desc)  desc: 'null-check' | 'cmp-reg-unproven:<reg>'
    pending_guard = None      # (test_addr, jcc_addr, target, sense, desc)
    use_since_test = False
    saw_data = [False]

    def mark_use(ad, kind, desc, is_del=False, tgt=None):
        nonlocal pending_guard, use_since_test
        use_since_test = True
        if state["cls"] is None:
            if pending_guard is not None:
                ta, ja, g, sense, gdesc = pending_guard
                pending_guard = None
                if g is None:
                    notes.append("indirect jcc @%#x -> cannot verify skip" % ja)
                elif g > ad and sense in ZEROish:
                    state["cls"], state["sub"] = "B", "guarded:%s:%s" % (gdesc, kind)
                    if gdesc.startswith("cmp-reg-unproven"):
                        notes.append("guard compares value against register %s -- not proven zero "
                                     "inside window; protective only if that register == 0" % gdesc.split(":", 1)[1])
                elif g == ad and sense in NONZEROish:
                    state["cls"], state["sub"] = "B", "guarded:%s:%s" % (gdesc, kind)
                    if gdesc.startswith("cmp-reg-unproven"):
                        notes.append("guard compares value against register %s -- not proven zero "
                                     "inside window; protective only if that register == 0" % gdesc.split(":", 1)[1])
                elif g > ad and sense in NONZEROish:
                    notes.append("INVERTED guard: %s @%#x skips use -> fallthrough (check-fail path) reaches use" % (sense, ja))
                elif g == ad and sense in ZEROish:
                    notes.append("guard jumps INTO use on check-equal path (%s @%#x)" % (sense, ja))
                elif g is not None:
                    notes.append("guard target %#x does not skip use @%#x" % (g, ad))
            if state["cls"] is None:
                if is_del:
                    state["cls"], state["sub"] = "A", "call_del"
                    state["call_target"] = DEL_FUNC
                else:
                    state["cls"], state["sub"] = "C", kind
                    if tgt is not None:
                        state["call_target"] = tgt
            elif state["cls"] == "B" and tgt is not None and state["call_target"] is None:
                state["call_target"] = tgt
            ev.append("%#x  %s   <== FIRST USE (decides class)" % (ad, desc))
        else:
            ev.append("%#x  %s" % (ad, desc))
            if kind.startswith("deref"):
                notes.append("additional deref in window after first use (value still live)")

    for ins in insns[1:]:
        m, ad = ins.mnemonic, ins.address
        if ad >= load_va + WINDOW:
            break
        if m in (".byte", "(bad)") or not m:
            saw_data[0] = True
            ev.append("%#x  DATA[%s] (skipdata)" % (ad, bytes(ins.bytes).hex()))
            notes.append("non-decodable bytes inside the 64B window")
            break
        ops = ins.operands
        ev.append("%#x  %-6s %s" % (ad, m, ins.op_str))
        if abs_global(ops):
            notes.append("window re-references global 0x887368 directly: %s %s" % (m, ins.op_str))

        if m in NOOPS:
            continue

        # ---------- control flow ----------
        if m in ("call", "jmp"):
            tgt = None
            tdesc = ins.op_str
            if ops and ops[0].type == X86_OP_IMM:
                tgt = ops[0].imm & 0xFFFFFFFF
                tdesc = "%#x" % tgt
            ecx_live = "ecx" in holders
            if m == "jmp":
                if ecx_live:
                    if tgt == DEL_FUNC:
                        mark_use(ad, "call_del", "jmp %#x   <-- tail-call FUN_00724730, this=ecx" % tgt,
                                 is_del=True, tgt=tgt)
                    else:
                        mark_use(ad, "jmp-with-ptr", "jmp %s   <-- with ecx = loaded ptr" % tdesc, tgt=tgt)
                break
            if tgt == DEL_FUNC:
                del_calls.append((ad, ecx_live))
                if ecx_live:
                    mark_use(ad, "call_del", "call %#x   <-- FUN_00724730, this=ecx" % tgt,
                             is_del=True, tgt=tgt)
                    break
                notes.append("call FUN_00724730 @%#x while ecx NO LONGER holds the loaded value "
                             "(reloaded/clobbered earlier) -- second-order path" % ad)
            elif ecx_live:
                mark_use(ad, "call:%s" % tdesc, "call %s   <-- loaded ptr passed as this" % tdesc, tgt=tgt)
            holders.discard("ecx"); holders.discard("eax"); holders.discard("edx")
            continue

        if m in ("ret", "retf", "leave", "hlt", "ud2", "int3", "int"):
            break

        if m in JCC_ALL:
            tgt = None
            if ops and ops[0].type == X86_OP_IMM:
                tgt = ops[0].imm & 0xFFFFFFFF
            if pending_test is not None and not use_since_test and holders:
                pending_guard = (pending_test[0], ad, tgt, m, pending_test[2])
            pending_test = None
            use_since_test = False
            continue

        # ---------- checks on the value ----------
        if m in ("test", "cmp"):
            if mem_hits(ops, holders):
                mark_use(ad, "deref-cmp", "%s %s   <-- deref through ptr" % (m, ins.op_str))
                pending_test = None
            else:
                r0 = rn(ops[0].reg) if (ops and ops[0].type == X86_OP_REG) else None
                if r0 in holders:
                    desc = None
                    if m == "test" and len(ops) == 2 and ops[1].type == X86_OP_REG \
                            and rn(ops[1].reg) == r0:
                        desc = "null-check"
                    elif m == "cmp" and len(ops) == 2 and ops[1].type == X86_OP_IMM \
                            and (ops[1].imm & 0xFFFFFFFF) == 0:
                        desc = "null-check"
                    elif m == "cmp" and len(ops) == 2 and ops[1].type == X86_OP_REG:
                        other = rn(ops[1].reg)
                        if other in zeros:
                            desc = "null-check"      # register provably zeroed in-window
                        else:
                            desc = "cmp-reg-unproven:%s" % other
                    elif m in ("or", "and") and len(ops) == 2 and ops[1].type == X86_OP_REG \
                            and rn(ops[1].reg) == r0:
                        desc = "null-check"
                    pending_test = (ad, "%s %s" % (m, ins.op_str), desc or "cmp-other")
                    use_since_test = False
                else:
                    pending_test = None
            continue

        # ---------- mov family ----------
        if m in ("mov", "movzx", "movsx", "movsxd"):
            d, s = ops[0], ops[1]
            if d.type == X86_OP_REG:
                dr = rn(d.reg)
                zeros.discard(dr)
                if s.type == X86_OP_REG:
                    sr = rn(s.reg)
                    if sr in zeros:
                        zeros.add(dr)
                    if sr in holders:
                        if dr != sr:
                            holders.add(dr)
                    elif dr in holders:
                        holders.discard(dr)
                        notes.append("value reg %s overwritten by '%s %s'" % (dr, m, ins.op_str))
                elif s.type == X86_OP_MEM:
                    if mem_hits(ops, holders):
                        mark_use(ad, "deref-load", "%s %s   <-- deref through ptr" % (m, ins.op_str))
                    if dr in holders:
                        holders.discard(dr)
                else:
                    if (s.imm & 0xFFFFFFFF) == 0:
                        zeros.add(dr)
                    if dr in holders:
                        holders.discard(dr)
                        notes.append("value reg %s overwritten by immediate" % dr)
            elif d.type == X86_OP_MEM:
                dhm = bool(mem_hits([d], holders))
                if dhm:
                    mark_use(ad, "deref-write", "%s %s   <-- deref-write through ptr" % (m, ins.op_str))
                if s.type == X86_OP_REG and rn(s.reg) in holders:
                    mark_use(ad, "store", "%s %s   <-- ptr stored to memory" % (m, ins.op_str))
            continue

        if m == "lea":
            d, s = ops[0], ops[1]
            dr = rn(d.reg) if d.type == X86_OP_REG else None
            if dr:
                zeros.discard(dr)
            if mem_hits([s], holders):
                if dr:
                    holders.add(dr)
                    notes.append("lea derives a pointer from the loaded value: '%s %s'" % (m, ins.op_str))
            elif dr and dr in holders:
                holders.discard(dr)
                notes.append("value reg %s overwritten by lea" % dr)
            continue

        if m == "push":
            o = ops[0]
            if o.type == X86_OP_REG and rn(o.reg) in holders:
                mark_use(ad, "push-arg", "push %s   <-- ptr passed as stack arg" % ins.op_str)
            elif mem_hits(ops, holders):
                mark_use(ad, "deref-push", "push %s   <-- deref through ptr" % ins.op_str)
            continue

        if m == "pop":
            o = ops[0]
            if o.type == X86_OP_REG:
                zeros.discard(rn(o.reg))
                if rn(o.reg) in holders:
                    holders.discard(rn(o.reg))
                    notes.append("pop replaces value reg (%s)" % ins.op_str)
            continue

        if m in ARITH:
            if mem_hits(ops, holders):
                mark_use(ad, "deref-rmw", "%s %s   <-- deref-rmw through ptr" % (m, ins.op_str))
            if ops and ops[0].type == X86_OP_REG:
                dr = rn(ops[0].reg)
                zeros.discard(dr)
                if m == "xor" and len(ops) == 2 and ops[1].type == X86_OP_REG \
                        and rn(ops[1].reg) == dr:
                    zeros.add(dr)
                if dr in holders:
                    holders.discard(dr)
                    notes.append("value reg %s mutated by '%s %s'" % (dr, m, ins.op_str))
            pending_test = None
            continue

        if m == "xchg" and len(ops) == 2 and all(o.type == X86_OP_REG for o in ops):
            r0, r1 = rn(ops[0].reg), rn(ops[1].reg)
            zeros.discard(r0); zeros.discard(r1)
            h0, h1 = r0 in holders, r1 in holders
            if h0 and not h1:
                holders.discard(r0); holders.add(r1)
            elif h1 and not h0:
                holders.discard(r1); holders.add(r0)
            continue

        if m.startswith("set"):
            if ops and ops[0].type == X86_OP_REG:
                zeros.discard(rn(ops[0].reg))
                if rn(ops[0].reg) in holders:
                    holders.discard(rn(ops[0].reg))
                    notes.append("setcc replaces value reg")
            pending_test = None
            continue

        if m.startswith("cmov"):
            d = ops[0]
            dr = rn(d.reg) if d.type == X86_OP_REG else None
            sr = rn(ops[1].reg) if (len(ops) > 1 and ops[1].type == X86_OP_REG) else None
            if dr:
                zeros.discard(dr)
            if dr and dr in holders:
                holders.discard(dr)
                notes.append("cmov may replace value reg, tracking stopped")
            elif sr and sr in holders and dr:
                holders.add(dr)
                notes.append("cmov may copy the value into %s" % dr)
            pending_test = None
            continue

        if m in ("cdq", "cwde", "cbw"):
            for r2 in (("eax", "edx") if m == "cdq" else ("eax",)):
                zeros.discard(r2)
                holders.discard(r2)
            continue

        # generic fallback
        if mem_hits(ops, holders):
            mark_use(ad, "deref-generic", "%s %s   <-- deref through ptr (generic)" % (m, ins.op_str))
        else:
            toks = set(ins.op_str.replace(",", " ").replace("[", " ").replace("]", " ").split())
            touched = sorted(t for t in toks if t in holders)
            if touched:
                notes.append("unhandled insn '%s %s' touches value reg %s (kept tracked, conservative)"
                             % (m, ins.op_str, touched))
        if m in FLAG_WRITERS:
            pending_test = None
        continue

    # ---------- finalization ----------
    if state["cls"] is None:
        if saw_data[0]:
            state["cls"], state["sub"] = "C", "uncertain-data"
        elif holders:
            if pending_guard is not None:
                ta, ja, g, sense, gdesc = pending_guard
                if g is not None and sense in ZEROish and gdesc == "null-check":
                    state["cls"], state["sub"] = "B", "guarded:null-check:use-beyond-window"
                    notes.append("test/jz-style guard @%#x; no use inside window; any later "
                                 "fallthrough use is behind the guard" % ja)
                elif g is not None and sense in ZEROish and gdesc.startswith("cmp-reg-unproven"):
                    state["cls"], state["sub"] = "B", "guarded:%s:use-beyond-window" % gdesc
                    notes.append("guard compares value against register %s -- not proven zero inside "
                                 "window; no use inside window either" % gdesc.split(":", 1)[1])
                elif g is not None and sense in NONZEROish and gdesc == "null-check":
                    state["cls"], state["sub"] = "C", "possible-inverted-guard"
                    notes.append("test+jnz-style guard @%#x: fallthrough is the check-fail path; "
                                 "a later use would be unchecked" % ja)
                else:
                    state["cls"], state["sub"] = "C", "uncertain-guard"
                    notes.append("guard @%#x (%s) inconclusive, no use inside window" % (ja, sense))
            else:
                state["cls"], state["sub"] = "C", "live-out"
                notes.append("value still live in %s at window end; use beyond 64B window not visible"
                             % sorted(holders))
        else:
            state["cls"], state["sub"] = "C", "dead-no-use"
            notes.append("value overwritten/discarded before any visible use in the window")
    if state["cls"] == "C" and state["sub"] == "store" and any(l for _a, l in del_calls):
        state["cls"], state["sub"] = "A", "call_del-after-store"
        state["call_target"] = DEL_FUNC
        notes.append("reclassified A-variant: FUN_00724730 called in-window while ecx still held the "
                     "loaded value (store in between, distance > 24B)")
    if state["cls"] != "A" and del_calls:
        notes.append("window contains call(s) to FUN_00724730: " +
                     ", ".join("@%#x(ecx_live=%s)" % (a3, l3) for a3, l3 in del_calls))
    return {"load_va": load_va, "cls": state["cls"], "sub": state["sub"],
            "notes": notes, "ev": ev, "call_target": state["call_target"],
            "del_calls": del_calls, "nxt48": rd(load_va, 48).hex()}

def run():
    out("=== 0. target ===")
    out("exe: %s" % EXE_PATH)
    h = hashlib.sha256()
    with open(EXE_PATH, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    digest = h.hexdigest().upper()
    out("sha256(exe) = %s" % digest)
    if digest != EXPECT_SHA256:
        out("!! PREMISE MISMATCH: sha256 differs from expected %s -- STOP" % EXPECT_SHA256)
        raise SystemExit(2)

    out("")
    out("=== 1. mapping self-check (index = VA - 0x400000) ===")
    out("rule: get_memory_mapped_image()[i] == VA(0x400000 + i)")
    out("mapped image size: %#x bytes ; img[0:2] = %r" % (len(img), bytes(img[0:2])))
    if bytes(img[0:2]) != b"MZ":
        out("!! ImageBase mapping broken -- STOP")
        raise SystemExit(2)

    out("")
    out("=== 2. FUN_00724730 / crash-site premise check ===")
    for i6 in list(md.disasm(rd(DEL_FUNC, 32), DEL_FUNC))[:8]:
        out("  %#x  %-6s %-32s [%s]" % (i6.address, i6.mnemonic, i6.op_str, bytes(i6.bytes).hex()))
    ci = list(md.disasm(rd(0x724737, 16), 0x724737))[0]
    out("  @0x724737 (recorded crash EIP): %s %s [%s]" % (ci.mnemonic, ci.op_str, bytes(ci.bytes).hex()))
    if not (ci.mnemonic == "mov" and "ebp" in ci.op_str and "0x250" in ci.op_str):
        out("!! PREMISE MISMATCH: instruction at 0x724737 is not mov eax,[ebp+0x250] -- STOP")
        raise SystemExit(2)
    out("  OK: matches premise 'first real memory access mov eax,[ebp+0x250]'")
    bad = [v for v in KNOWN20 if rd(v, 6) != PATTERN]
    if bad:
        out("!! PREMISE MISMATCH: known-20 byte mismatch at: %s -- STOP" % [hex(v) for v in bad])
        raise SystemExit(2)
    out("  OK: all 20 known load addresses contain bytes 8b 0d 68 73 88 00")

    out("")
    out("=== 3. sections ===")
    for s in pe.sections:
        nm = s.Name.rstrip(b"\x00").decode(errors="replace")
        va = IMAGE_BASE + s.VirtualAddress
        out("  %-8s VA %#010x .. %#010x (VirtualSize %#x)"
            % (nm, va, va + s.Misc_VirtualSize - 1, s.Misc_VirtualSize))

    out("")
    out("=== 4. skipdata linear sweep of .text (method check) ===")
    tb = rd(TEXT_START, TEXT_END - TEXT_START + 1)
    n = 0
    last = None
    for i7 in mdf.disasm(tb, TEXT_START):
        n += 1
        last = i7
    cov = last.address + last.size
    out("  .text bytes scanned: %#x ; decoded instructions (incl. skipdata): %d ; coverage end: %#x (expected %#x)"
        % (len(tb), n, cov, TEXT_END + 1))
    if cov != TEXT_END + 1:
        out("!! linear sweep did not cover .text fully -- STOP")
        raise SystemExit(2)

    out("")
    out("=== 5. byte-pattern scan: 8B 0D 68 73 88 00 in .text ===")
    loads = []
    p = tb.find(PATTERN)
    while p != -1:
        loads.append(TEXT_START + p)
        p = tb.find(PATTERN, p + 1)
    out("  found %d occurrences (premise: 69)" % len(loads))
    if len(loads) != 69:
        out("!! PREMISE MISMATCH: expected 69 occurrences, found %d -- STOP" % len(loads))
        raise SystemExit(2)
    missing = sorted(set(KNOWN20) - set(loads))
    if missing:
        out("!! PREMISE MISMATCH: known-20 missing from scan: %s -- STOP" % [hex(v) for v in missing])
        raise SystemExit(2)
    others = sorted(v for v in loads if v not in set(KNOWN20))
    out("  known-20 all reproduced at exact addresses; remaining loads to classify: %d" % len(others))

    out("")
    out("=== 6. classification of all 69 sites ===")
    results = []
    for v in sorted(loads):
        try:
            results.append(analyze(v))
        except Exception:
            results.append({"load_va": v, "cls": "C", "sub": "analyzer-exception",
                            "notes": ["analyzer exception: " + traceback.format_exc(limit=3).replace("\n", " | ")],
                            "ev": ["<analyzer exception>"], "call_target": None,
                            "del_calls": [], "nxt48": rd(v, 48).hex()})
    for r in results:
        r["known20"] = r["load_va"] in set(KNOWN20)
    cnt = Counter(r["cls"] for r in results)
    out("  A call_del: %d" % cnt.get("A", 0))
    out("  B guarded : %d" % cnt.get("B", 0))
    out("  C other   : %d" % cnt.get("C", 0))
    k20 = [r for r in results if r["known20"]]
    nona = [r for r in k20 if r["cls"] != "A"]
    if nona:
        out("!! PREMISE MISMATCH: known-20 sites not classified as A:")
        for r in nona:
            out("    %#x -> %s (%s)" % (r["load_va"], r["cls"], r["sub"]))
            out("      " + " ; ".join(r["ev"]))
        raise SystemExit(2)
    out("  known-20 reproduced as A: 20/20")
    dists = sorted(dc[0] - r["load_va"] for r in k20 for dc in r["del_calls"])
    if dists:
        out("  known-20 call distance (call_start - load_start): min %#x, max %#x (premise: within 0x18)"
            % (dists[0], dists[-1]))
    new_a = [r for r in results if not r["known20"] and r["cls"] == "A"]
    if new_a:
        out("  !! NEW FINDING: %d additional unconditional FUN_00724730 call sites outside the "
            "known-20 list (call distance %s):" % (len(new_a),
            ", ".join("%#x(+%#x)" % (r["load_va"], r["del_calls"][0][0] - r["load_va"]) for r in new_a)))

    out("")
    out("=== 7. the remaining %d loads (class / subkind / target) ===" % len(others))
    for r in results:
        if r["known20"]:
            continue
        ct = ("call->%#x" % r["call_target"]) if r["call_target"] else ""
        out("  %#x  %s  %-42s %s" % (r["load_va"], r["cls"], r["sub"], ct))

    out("")
    out("=== 8. B (guarded) sites ===")
    for r in results:
        if r["cls"] != "B":
            continue
        out("  --- %#x  %s" % (r["load_va"], r["sub"]))
        for ln in r["ev"]:
            out("      " + ln)
        if r["notes"]:
            out("      notes: " + " | ".join(r["notes"]))

    cs = [r for r in results if r["cls"] == "C"]
    out("")
    out("=== 9. C (other) sites: %d -- full windows ===" % len(cs))
    for r in cs:
        ct = ("   call_target=%#x" % r["call_target"]) if r["call_target"] else ""
        out("")
        out("  --- load %#x   sub=%s%s" % (r["load_va"], r["sub"], ct))
        for ln in r["ev"]:
            out("      " + ln)
        if r["notes"]:
            out("      notes: " + " | ".join(r["notes"]))

    out("")
    out("=== 10. C subkind breakdown ===")
    for sk, c in sorted(Counter(r["sub"] for r in cs).items(), key=lambda kv: (-kv[1], kv[0])):
        out("  %-46s %d" % (sk, c))

    tg = Counter(r["call_target"] for r in cs if r["call_target"] and r["call_target"] != DEL_FUNC)
    out("")
    out("=== 11. C-call targets (loaded ptr passed as this, unchecked) ===")
    for t, c in sorted(tg.items(), key=lambda kv: (-kv[1], kv[0])):
        out("  %#x  x%d" % (t, c))

    out("")
    out("=== 12. supplementary: prologue peek of each C-call target (heuristic) ===")
    for t in sorted(tg):
        out("  target %#x (used by %d site(s)):" % (t, tg[t]))
        try:
            for i8 in list(md.disasm(rd(t, 40), t))[:10]:
                out("      %#x  %-6s %s" % (i8.address, i8.mnemonic, i8.op_str))
        except Exception as e4:
            out("      <decode failed: %r>" % e4)

    out("")
    out("=== 13. supplementary census: other references to 0x887368 in .text ===")
    out("  raw occurrences of disp32 bytes 68 73 88 00: %d" % tb.count(DISP))
    CEN = [
        ("8B 0D       mov ecx,[0x887368] (the 69)", b"\x8B\x0D" + DISP),
        ("A1          mov eax,[0x887368]",   b"\xA1" + DISP),
        ("8B 1D       mov ebx,[0x887368]",   b"\x8B\x1D" + DISP),
        ("8B 15       mov edx,[0x887368]",   b"\x8B\x15" + DISP),
        ("8B 2D       mov ebp,[0x887368]",   b"\x8B\x2D" + DISP),
        ("8B 35       mov esi,[0x887368]",   b"\x8B\x35" + DISP),
        ("8B 3D       mov edi,[0x887368]",   b"\x8B\x3D" + DISP),
        ("FF 35       push [0x887368]",      b"\xFF\x35" + DISP),
        ("83 3D       cmp [0x887368],imm8",  b"\x83\x3D" + DISP),
        ("81 3D       cmp [0x887368],imm32", b"\x81\x3D" + DISP),
        ("89 0D       mov [0x887368],ecx",   b"\x89\x0D" + DISP),
        ("89 05       mov [0x887368],eax",   b"\x89\x05" + DISP),
        ("89 15       mov [0x887368],edx",   b"\x89\x15" + DISP),
        ("89 1D       mov [0x887368],ebx",   b"\x89\x1D" + DISP),
        ("89 2D       mov [0x887368],ebp",   b"\x89\x2D" + DISP),
        ("89 35       mov [0x887368],esi",   b"\x89\x35" + DISP),
        ("89 3D       mov [0x887368],edi",   b"\x89\x3D" + DISP),
        ("FF 15       call [0x887368]",      b"\xFF\x15" + DISP),
        ("FF 25       jmp [0x887368]",       b"\xFF\x25" + DISP),
        ("C7 05       mov [0x887368],imm32", b"\xC7\x05" + DISP),
        ("A3          mov [0x887368],eax",   b"\xA3" + DISP),
    ]
    for lbl, pat in CEN:
        c5 = tb.count(pat)
        if c5:
            out("  %-40s %d" % (lbl, c5))
    out("  (indicative only; disp bytes can coincide with other instruction operands)")
    out("")
    out("  -- windows for non-ecx references (read/write of the global outside the 69) --")
    for lbl, pat in CEN:
        if lbl.startswith("8B 0D"):
            continue
        idx = tb.find(pat)
        while idx != -1:
            va = TEXT_START + idx
            out("    [%s] @ %#x:" % (lbl.split()[0:3] and lbl, va))
            try:
                for i9 in list(md.disasm(rd(va, 24), va))[:6]:
                    out("        %#x  %-6s %s" % (i9.address, i9.mnemonic, i9.op_str))
            except Exception as e10:
                out("        <decode failed: %r>" % e10)
            idx = tb.find(pat, idx + 1)

    out("")
    out("=== 14. in-window FUN_00724730 calls outside the known-20 (second-order) ===")
    ext = [r for r in results if not r["known20"] and r["del_calls"]]
    if not ext:
        out("  none")
    for r in ext:
        out("  %#x  cls=%s sub=%s  del_calls=%s" % (r["load_va"], r["cls"], r["sub"],
            ["@%#x(ecx_live=%s)" % (a9, l9) for a9, l9 in r["del_calls"]]))

    out("")
    out("=== 15. supplementary extended probe (160B) for sites whose use/guard target lies "
        "beyond the 64B window ===")
    probe = [r for r in results
             if (r["cls"] == "C" and r["sub"] in ("live-out", "uncertain-data"))
             or (r["cls"] == "B" and "use-beyond-window" in r["sub"])]
    if not probe:
        out("  none")
    for r in probe:
        out("  --- site %#x (cls=%s sub=%s), 160B window from load:" % (r["load_va"], r["cls"], r["sub"]))
        try:
            for ia in list(md.disasm(rd(r["load_va"], 160), r["load_va"]))[:28]:
                out("      %#x  %-6s %s" % (ia.address, ia.mnemonic, ia.op_str))
        except Exception as eb:
            out("      <decode failed: %r>" % eb)

    # ---------- TSV ----------
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(TSV_PATH, "w", encoding="utf-8", newline="\n") as f:
        f.write("load_va\tclass\tnext_48_bytes_hex\tevidence_instructions\tcall_target_if_any\n")
        for r in sorted(results, key=lambda x: x["load_va"]):
            evs = " ; ".join(r["ev"]).replace("\t", " ").replace("\r", " ").replace("\n", " ")
            ct = ("%#x" % r["call_target"]) if r["call_target"] else ""
            f.write("%#x\t%s\t%s\t%s\t%s\n" % (r["load_va"], r["cls"], r["nxt48"], evs, ct))
    out("")
    out("TSV written : %s" % TSV_PATH)
    out("next_48_bytes_hex = 48 raw bytes starting AT the load instruction (load included)")

_rc = 0
try:
    run()
except SystemExit as e6:
    _rc = e6.code if isinstance(e6.code, int) else 1
except Exception:
    traceback.print_exc()
    REPORT.append("")
    REPORT.append("EXCEPTION:")
    REPORT.append(traceback.format_exc())
    _rc = 1
finally:
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(REPORT_PATH, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(REPORT) + "\n")
    print("report written: %s" % REPORT_PATH)
sys.exit(_rc)
