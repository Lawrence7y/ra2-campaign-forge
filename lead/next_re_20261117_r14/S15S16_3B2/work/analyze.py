# -*- coding: utf-8 -*-
"""
S15S16-3B2 Step 1: mechanical pre-screen of the pool.
For each pool entry (from work/pool.json), disassemble its function body with
capstone 5.0.7 (skipdata=True) using atlas size as boundary, then detect:

  P1: a `call` followed (within 3 insns) by `test eax,eax` / `or eax,eax` /
      `cmp eax,imm` followed (within 2 insns) by a conditional jump (jcc).
  P2: for that jcc, the taken vs fall-through path action signatures differ
      (direct-call set / return-constant set / has-ret / end-eax constant).
      Equal signatures (e.g. same single call, only args differ) => not P2.
  P3: the callee is inside .text and its own body returns >=2 distinct known
      constants, at least one being a falsifiable marker (0,1,-1,HRESULT/NTSTATUS
      failure ranges), i.e. a concrete falsifiable return convention. P1's jcc
      is the consumer (the caller branches on it).

Emits work/analysis.json with per-entry detail. Prints aggregate counts.
"""
import csv, json, os, pefile
from capstone import *
from capstone.x86 import *

BASE = r"D:\Project\ra2-campaign-forge"
EXE = os.path.join(BASE, r"ra2youli\gamemd.exe")
WORK = os.path.join(BASE, r"lead\next_re_20261117_r14\S15S16_3B2\work")
ATLAS = os.path.join(BASE, r"lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv")

def norm(e):
    e = e.strip().upper()
    if e.startswith("0X"):
        e = e[2:]
    return e

# ---- atlas ----
atlas = {}
with open(ATLAS, encoding="utf-8") as f:
    rdr = csv.reader(f, delimiter="\t")
    next(rdr)
    for row in rdr:
        if not row or not row[0].strip():
            continue
        try:
            atlas[norm(row[0])] = {"size": int(row[1]), "n_instr": int(row[2])}
        except (ValueError, IndexError):
            pass

# ---- PE / .text ----
pe = pefile.PE(EXE)
IB = pe.OPTIONAL_HEADER.ImageBase
sec = None
for s in pe.sections:
    if s.Name.rstrip(b"\x00") == b".text":
        sec = s
        break
TEXT_VA = IB + sec.VirtualAddress
TEXT_DATA = sec.get_data()
TEXT_SIZE = max(sec.Misc_VirtualSize, sec.SizeOfRawData)

def read_va(va, maxlen):
    off = va - TEXT_VA
    if off < 0 or off >= len(TEXT_DATA):
        return b""
    return TEXT_DATA[off:off + maxlen]

md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = True
md.skipdata = True

# jcc ids: use the ACTUAL capstone 5.0.7 constant names (JE/JNE not JZ/JNZ,
# JAE/JBE not JNB/JNA, etc.). Derive from module namespace to avoid alias-name bugs.
JCC_IDS = set()
for cname in dir():
    if cname.startswith("X86_INS_J") and cname != "X86_INS_JMP":
        # skip any non-jcc J* (none in capstone x86 besides JMP)
        JCC_IDS.add(globals()[cname])
# explicitly ensure the common ones are present
for cname in ("X86_INS_JE", "X86_INS_JNE", "X86_INS_JL", "X86_INS_JGE",
              "X86_INS_JLE", "X86_INS_JG", "X86_INS_JA", "X86_INS_JAE",
              "X86_INS_JB", "X86_INS_JBE", "X86_INS_JS", "X86_INS_JNS",
              "X86_INS_JO", "X86_INS_JNO", "X86_INS_JP", "X86_INS_JNP",
              "X86_INS_JCXZ", "X86_INS_JECXZ"):
    if cname in globals():
        JCC_IDS.add(globals()[cname])

def is_eax(op):
    return op.type == X86_OP_REG and op.reg == X86_REG_EAX

def test_kind(ins):
    if ins.id == X86_INS_TEST and len(ins.operands) == 2:
        if is_eax(ins.operands[0]) and is_eax(ins.operands[1]):
            return ("TEST_EAX", 0)
    if ins.id == X86_INS_OR and len(ins.operands) == 2:
        if is_eax(ins.operands[0]) and is_eax(ins.operands[1]):
            return ("OR_EAX", 0)
    if ins.id == X86_INS_CMP and len(ins.operands) == 2:
        if is_eax(ins.operands[0]) and ins.operands[1].type == X86_OP_IMM:
            return ("CMP_IMM", ins.operands[1].imm & 0xFFFFFFFF)
    return None

def path_sig(insns, start_idx, maxn=16):
    """Action signature of a straight-line path starting at start_idx."""
    calls, rets = set(), set()
    has_ret = False
    eax = None
    end_eax = None
    for j in range(start_idx, min(start_idx + maxn, len(insns))):
        ins = insns[j]
        if ins.id == 0:  # skipdata byte
            continue
        if ins.id == X86_INS_CALL:
            if ins.operands and ins.operands[0].type == X86_OP_IMM:
                calls.add(ins.operands[0].imm & 0xFFFFFFFF)
            eax = None
        elif ins.id in (X86_INS_XOR, X86_INS_SUB) and len(ins.operands) == 2:
            a, b = ins.operands
            if is_eax(a) and is_eax(b):
                eax = 0
        elif ins.id == X86_INS_MOV and len(ins.operands) == 2:
            a, b = ins.operands
            if is_eax(a):
                eax = (b.imm & 0xFFFFFFFF) if b.type == X86_OP_IMM else None
        elif ins.id == X86_INS_RET:
            has_ret = True
            if eax is not None:
                rets.add(eax)
            end_eax = eax
            break
        elif ins.id == X86_INS_JMP:
            end_eax = eax
            break
        else:
            end_eax = eax
    return {"calls": sorted(calls), "rets": sorted(rets),
            "has_ret": has_ret, "end_eax": end_eax}

def is_falsifiable(v):
    if v in (0, 1, 0xFFFFFFFF):
        return True
    if 0x80000000 <= v <= 0x8FFFFFFF:   # HRESULT failure
        return True
    if 0xC0000000 <= v <= 0xDFFFFFFF:   # NTSTATUS failure
        return True
    return False

def callee_return_profile(callee_va):
    """Return (consts, n_ret_sites, ret_origins) for the callee within its atlas
    boundary, or None if callee is outside .text / not analyzable.

    consts      = set of concrete constants written to eax before a ret
    n_ret_sites = number of ret instructions seen
    ret_origins = set of descriptors for where eax came from at each ret,
                  e.g. ('imm', v) / ('call',) / ('unknown',)
    """
    if callee_va is None:
        return None
    if not (TEXT_VA <= callee_va < TEXT_VA + TEXT_SIZE):
        return None  # import / outside .text -> cannot verify
    key = "%08X" % callee_va  # atlas keys are zero-padded uppercase (no 0x)
    cap = atlas.get(norm(key), {}).get("size")
    if cap is None:
        return None  # no reliable boundary -> do NOT guess (avoid cross-function bleed)
    code = read_va(callee_va, cap)
    if not code:
        return None
    insns = list(md.disasm(code, callee_va))
    consts = set()
    rets = 0
    origins = set()
    eax = ("unknown",)  # (kind, value)
    for ins in insns:
        if ins.id == 0:
            continue
        if ins.id in (X86_INS_XOR, X86_INS_SUB) and len(ins.operands) == 2:
            a, b = ins.operands
            if is_eax(a) and is_eax(b):
                eax = ("imm", 0)
        elif ins.id == X86_INS_MOV and len(ins.operands) == 2:
            a, b = ins.operands
            if is_eax(a):
                eax = ("imm", b.imm & 0xFFFFFFFF) if b.type == X86_OP_IMM else ("unknown",)
        elif ins.id == X86_INS_CALL:
            eax = ("call",)  # return value supplied by callee (e.g. COM HRESULT)
        elif ins.id == X86_INS_RET:
            rets += 1
            origins.add(eax)
            if eax[0] == "imm":
                consts.add(eax[1])
            eax = ("unknown",)
        if ins.address - callee_va >= cap:
            break
    return {"consts": consts, "n_rets": rets, "origins": [list(o) for o in origins]}

# ---- run over pool ----
pool = json.load(open(os.path.join(WORK, "pool.json"), encoding="utf-8"))
results = []
for p in pool:
    ea = int(p["entry"], 16)
    size = p["atlas_size"] if p["atlas_size"] else 512
    code = read_va(ea, size)
    insns = list(md.disasm(code, ea))
    idx_by_addr = {ins.address: i for i, ins in enumerate(insns)}
    p1, p2, p3 = [], [], []
    for i, ins in enumerate(insns):
        if ins.id != X86_INS_CALL:
            continue
        callee = None
        if ins.operands and ins.operands[0].type == X86_OP_IMM:
            callee = ins.operands[0].imm & 0xFFFFFFFF
        # find first test of eax within next 4 insns, then jcc within 2 after test
        found_site = False
        for k in range(i + 1, min(i + 5, len(insns))):
            tk = test_kind(insns[k])
            if not tk:
                continue
            for m in range(k + 1, min(k + 3, len(insns))):
                jc = insns[m]
                if jc.id not in JCC_IDS:
                    continue
                site = {
                    "call_addr": ins.address, "callee": callee,
                    "test_addr": insns[k].address, "test_kind": tk[0], "test_imm": tk[1],
                    "jcc_addr": jc.address, "jcc_mnemonic": jc.mnemonic,
                    "jcc_target": (jc.operands[0].imm if jc.operands and jc.operands[0].type == X86_OP_IMM else None),
                    "fallthrough": jc.address + jc.size,
                }
                p1.append(site)
                # P2: compare action signatures of TAKEN vs FALLTHROUGH paths
                ti = idx_by_addr.get(site["jcc_target"], None)
                if ti is None:
                    # taken target outside this function body -> divergent action
                    sig_t = {"calls": [], "rets": [], "has_ret": False, "end_eax": "OUT_OF_BODY"}
                else:
                    sig_t = path_sig(insns, ti)
                sig_f = path_sig(insns, m + 1)
                key = ("calls", "rets", "has_ret", "end_eax")
                if tuple(sig_t[x] for x in key) != tuple(sig_f[x] for x in key):
                    site["sig_taken"] = sig_t
                    site["sig_fallthrough"] = sig_f
                    p2.append(site)
                    # P3: a concrete falsifiable return convention exists AND the
                    # caller (this function) branches on it (P1's jcc is the consume point).
                    # Two sufficient forms:
                    #  (a) call-site compares eax against a concrete falsifiable
                    #      sentinel (cmp eax,-1 / cmp eax,0 / cmp eax,0x8000xxxx);
                    #  (b) statically-resolvable callee has a falsifiable failure
                    #      constant written to eax on one ret and a different ret origin.
                    falsy_const = None
                    if tk[0] == "CMP_IMM" and tk[1] is not None and is_falsifiable(tk[1]):
                        falsy_const = tk[1]
                    elif tk[0] in ("TEST_EAX", "OR_EAX") and jc.id in (X86_INS_JE,):
                        # test eax,eax / or eax,eax + je/jz => explicit zero (null/0) falsifiable check
                        falsy_const = 0
                    prof = callee_return_profile(callee)
                    prof_ok = bool(prof and any(is_falsifiable(v) for v in prof["consts"])
                                   and len(prof["origins"]) >= 2)
                    if falsy_const is not None or prof_ok:
                        site["p3_form"] = "call_site_cmp" if falsy_const is not None else "callee_profile"
                        site["call_site_falsy"] = hex(falsy_const) if falsy_const is not None else None
                        prof = prof or {}
                        site["callee_profile"] = {
                            "falsifiable_consts": [hex(v) for v in sorted(prof.get("consts", set())) if is_falsifiable(v)],
                            "all_consts": [hex(v) for v in sorted(prof.get("consts", set()))],
                            "n_rets": prof.get("n_rets"),
                            "origins": prof.get("origins"),
                            "callee_key": "%08X" % callee if callee else None,
                        }
                        p3.append(site)
                found_site = True
                break
            if found_site:
                break
    results.append({
        "entry": p["entry"], "subsystem": p["subsystem"], "name": p["name"],
        "semantics": p["semantics"],
        "in_atlas": p["in_atlas"], "atlas_size": p["atlas_size"], "n_insn": len(insns),
        "p1_count": len(p1), "p2_count": len(p2), "p3_count": len(p3),
        "p1": p1, "p2": p2, "p3": p3,
    })

json.dump(results, open(os.path.join(WORK, "analysis.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=2)

print("=== Step 1 mechanical counts (denominator = pool size) ===")
for s in ("S15", "S16"):
    rs = [r for r in results if r["subsystem"] == s]
    c1 = sum(1 for r in rs if r["p1_count"] > 0)
    c2 = sum(1 for r in rs if r["p2_count"] > 0)
    c3 = sum(1 for r in rs if r["p3_count"] > 0)
    print(f"{s}: pool={len(rs)} P1={c1} P1P2={c2} P1P2P3={c3}")
c1 = sum(1 for r in results if r["p1_count"] > 0)
c2 = sum(1 for r in results if r["p2_count"] > 0)
c3 = sum(1 for r in results if r["p3_count"] > 0)
print(f"TOTAL: pool={len(results)} P1={c1} P1P2={c2} P1P2P3={c3}")
