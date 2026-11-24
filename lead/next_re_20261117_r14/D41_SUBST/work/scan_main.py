# -*- coding: utf-8 -*-
"""D41-SUBST scan: self-test, .text sweep coverage, direct call sites for all S02/S19 [静态推断] candidates."""
import sys, os, json, struct
sys.path.insert(0, os.path.dirname(__file__))
from common import DATA, IB, SECS, EXE, SHA, find_dword, disasm_va, va2off, where_va, off2va, rva2off, sec_of_rva
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import X86_OP_IMM

WORK = os.path.dirname(__file__)
EVID = os.path.join(WORK, "..", "EVIDENCE")

out = {}
out["sha256"] = SHA
out["exe_size"] = len(DATA)

# ---- 1. self-test of 4-byte VA occurrence against known controls (§8.6 条2 / S21_C3) ----
controls = {0x0053AF40: 0, 0x00595740: 0, 0x00599650: 0, 0x00539760: 0, 0x0053AB50: 0,
            0x0040B880: 1, 0x005F3E30: 16}
selftest = {}
for va, expected in controls.items():
    got = len(find_dword(va))
    selftest["%08X" % va] = {"expected": expected, "got": got, "ok": got == expected}
out["selftest"] = selftest
print("=== SELFTEST (4-byte VA occurrence) ===")
for k, v in selftest.items():
    print("  %s expected=%d got=%d ok=%s" % (k, v["expected"], v["got"], v["ok"]))

# ---- 2. full .text capstone sweep (skipdata=True) ----
text = [s for s in SECS if s[0] == ".text"][0]
name, tva, tvs, trs, tra = text
text_off_start, text_off_end = tra, tra + trs
text_va_start, text_va_end = IB + tva, IB + tva + tvs
blob = DATA[text_off_start:text_off_end]
md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = True
md.skipdata = True
insn_count = 0
raw_e8 = blob.count(b"\xe8")
e8_boundary = 0
e8_id_call = 0
last_addr = text_va_start
for ins in md.disasm(blob, text_va_start):
    insn_count += 1
    if ins.mnemonic == "call" and ins.bytes and ins.bytes[0] == 0xE8:
        e8_boundary += 1
        if ins.operands and ins.operands[0].type == X86_OP_IMM:
            e8_id_call += 1
    last_addr = ins.address + ins.size
# coverage measured over VirtualSize actually disassembled
covered = last_addr - text_va_start
cover_pct = 100.0 * covered / tvs
out["text_sweep"] = {"text_va": "%08X" % text_va_start, "virtual_size": tvs, "raw_size": trs,
                     "insn_count": insn_count, "raw_e8_bytes": raw_e8,
                     "e8_at_boundary": e8_boundary, "e8_id_call": e8_id_call,
                     "covered_bytes": covered, "coverage_pct_virtualsize": round(cover_pct, 4)}
print("=== .text SWEEP ===")
print("  insn=%d rawE8=%d E8@boundary=%d E8-id-call=%d covered=%d VS=%d cover%%=%.4f" %
      (insn_count, raw_e8, e8_boundary, e8_id_call, covered, tvs, cover_pct))

# ---- 3. parse candidates ----
cand_path = os.path.join(WORK, "si_candidates.tsv")
rows = []
for line in open(cand_path, encoding="utf-8"):
    f = line.rstrip("\n").split("\t")
    if len(f) < 5:
        continue
    rows.append({"entry": f[0], "sub": f[1], "name": f[2], "sem": f[3], "grade": f[4]})
print("=== CANDIDATES ===", len(rows))

# VA occurrence + direct call sites for each candidate
# Build direct call target map from a second sweep (collect E8 rel32 at boundary)
direct_targets = {}
for ins in md.disasm(blob, text_va_start):
    if ins.mnemonic == "call" and ins.bytes and ins.bytes[0] == 0xE8 and ins.operands and ins.operands[0].type == X86_OP_IMM:
        tgt = ins.operands[0].imm & 0xffffffff
        direct_targets.setdefault(tgt, []).append(ins.address)

for r in rows:
    va = int(r["entry"], 16)
    r["vaocc"] = len(find_dword(va))
    sites = direct_targets.get(va, [])
    # exclude self-loop
    sites = [s for s in sites if not (s >= va and s < va + 0x2000)]
    r["direct_sites"] = ["%08X" % s for s in sites[:30]]
    r["direct_n"] = len(sites)

with open(os.path.join(EVID, "scan_main.json"), "w", encoding="utf-8") as fh:
    json.dump(out, fh, ensure_ascii=False, indent=2)
with open(os.path.join(WORK, "cand_scan.json"), "w", encoding="utf-8") as fh:
    json.dump(rows, fh, ensure_ascii=False, indent=2)

# summary by sub
for sub in ("S02", "S19"):
    rr = [r for r in rows if r["sub"] == sub]
    zero = [r for r in rr if r["vaocc"] == 0]
    print("=== %s: candidates=%d VAocc=0=%d ===" % (sub, len(rr), len(zero)))
    for r in zero:
        print("   %s %-30s direct=%d" % (r["entry"], r["name"], r["direct_n"]))
print("wrote EVIDENCE/scan_main.json and work/cand_scan.json")
