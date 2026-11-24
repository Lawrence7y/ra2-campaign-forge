"""Dump all 16 remaining S03 A-set candidate bodies with entry-relative offsets.
Extents come from SURVEY_RING24 classification.tsv (self-written CFG, NOT atlas entry+size).
Computes ③b signal metrics (jcc/jmp/call/ret/switch/backedge/cmp-imm). Read-only on exe.
"""
import os, sys, json, csv
sys.path.insert(0, os.path.dirname(__file__))
import common as C

CLS = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\SURVEY_RING24\EVIDENCE\classification.tsv"
CAND = ["00431F70","00432050","004322A0","004325C0","00473C00","00473CE0","00473FC0","0047AAB0",
        "0047AE10","00631D30","0065CCA0","0065CDD0","0065D0D0","0065D190","0065D1F0","0065D240"]

ext = {}
for r in csv.DictReader(open(CLS, encoding="utf-8"), delimiter="\t"):
    if r["entry"] in CAND:
        ext[r["entry"]] = (int(r["ext_lo"],16), int(r["ext_hi"],16), r["name"],
                           r["rtti_classes"], r["rtti_vt"], r["rtti_slot"], r["ring4_direct_sites"])

os.makedirs(os.path.join(os.path.dirname(__file__), "..", "EVIDENCE", "dis"), exist_ok=True)
meta = {}
for e in CAND:
    lo, hi, name, rcls, vt, slot, sites = ext[e]
    size = hi - lo
    off = C.va2off(lo)
    code = C._data[off:off+size]
    lines = []
    jcc = jmp = calls = rets = 0
    switch = []
    backedges = []
    cmpimm = []
    for insn in C.md().disasm(code, lo):
        o = insn.address - lo
        m = insn.mnemonic
        if m.startswith("j") and m != "jmp":
            jcc += 1
            try:
                t = int(i.op_str, 16) if False else int(insn.op_str, 16)
                if t <= insn.address:
                    backedges.append((o, m, insn.op_str))
            except Exception:
                pass
        if m == "jmp":
            jmp += 1
            if "dword ptr" in insn.op_str and "*" in insn.op_str:
                switch.append((o, m, insn.op_str))
        if m == "call":
            calls += 1
        if m.startswith("ret"):
            rets += 1
        if m == "cmp" and ("0x" in insn.op_str or "-1" in insn.op_str or insn.op_str.strip().lstrip("-").isdigit()):
            cmpimm.append((o, insn.op_str))
        lines.append("+%04X  %08X  %-9s %-40s ; %s" % (o, insn.address, m, insn.op_str, insn.bytes.hex()))
    with open(os.path.join(os.path.dirname(__file__), "..", "EVIDENCE", "dis", e + ".txt"), "w", encoding="utf-8") as f:
        f.write("; entry %s name=%s extent=%08X..%08X size=0x%X insn=%d jcc=%d jmp=%d call=%d ret=%d\n" % (
            e, name, lo, hi, size, len(lines), jcc, jmp, calls, rets))
        f.write("; rtti_classes=%s vt=%s slot=%s n_direct_out_sites=%s\n" % (rcls, vt, slot, sites))
        f.write("\n".join(lines) + "\n")
    meta[e] = {"name": name, "extent": ["0x%x"%lo,"0x%x"%hi], "size": size, "insn": len(lines),
               "jcc": jcc, "jmp": jmp, "call": calls, "ret": rets,
               "switch": switch, "backedges": backedges, "n_cmpimm": len(cmpimm),
               "rtti_classes": rcls, "vt": vt, "slot": slot}
with open(os.path.join(os.path.dirname(__file__), "..", "EVIDENCE", "dis", "_meta.json"), "w", encoding="utf-8") as f:
    json.dump(meta, f, indent=2)
print("entry   name                     size insn jcc jmp cal ret sw be cmpimm")
for e in CAND:
    m = meta[e]
    print("%s %-24s 0x%-4X %4d %3d %3d %3d %3d %2d %2d %d" % (
        e, m["name"], m["size"], m["insn"], m["jcc"], m["jmp"], m["call"], m["ret"],
        len(m["switch"]), len(m["backedges"]), m["n_cmpimm"]))
