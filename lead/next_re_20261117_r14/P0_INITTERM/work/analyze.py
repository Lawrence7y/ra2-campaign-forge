"""P0-INITTERM main analysis: T2 per-item, T3 buckets, T5 reconciliation."""
import sys, os, hashlib, json, struct
from collections import Counter
sys.path.insert(0, r"D:\Project\ra2-campaign-forge")
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

ROOT = r"D:\Project\ra2-campaign-forge"
CARD = os.path.join(ROOT, "lead", "next_re_20261117_r14", "P0_INITTERM")
EXE = os.path.join(ROOT, "ra2youli", "gamemd.exe")
EXPECTED = "73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476"
COVERAGE = os.path.join(ROOT, "lead", "next_re_20261117_r14", "COVERAGE", "coverage.tsv")
ATLAS = os.path.join(ROOT, "lead", "next_re_20261112_r10", "W130_atlas", "function_atlas.tsv")

h = hashlib.sha256(open(EXE,"rb").read()).hexdigest().upper()
assert h == EXPECTED, h
pe = pefile.PE(EXE, fast_load=False)
IB = pe.OPTIONAL_HEADER.ImageBase
data = open(EXE,"rb").read()
secs = {}
for s in pe.sections:
    name = s.Name.decode(errors="replace").rstrip("\x00")
    secs[name] = dict(va=IB+s.VirtualAddress, vs=s.Misc_VirtualSize,
                      raw=s.PointerToRawData, rs=s.SizeOfRawData)
def va2off(va):
    rva = va - IB
    for s in pe.sections:
        if s.VirtualAddress <= rva < s.VirtualAddress + max(s.Misc_VirtualSize, s.SizeOfRawData):
            return s.PointerToRawData + (rva - s.VirtualAddress)
    raise ValueError("unmapped %08X" % va)
def rd(va, n):
    off = va2off(va); return data[off:off+n]
def dword(va):
    return struct.unpack_from("<I", rd(va,4), 0)[0]

TEXT_S, TEXT_E = secs[".text"]["va"], secs[".text"]["va"]+secs[".text"]["vs"]
RDATA_S, RDATA_E = secs[".rdata"]["va"], secs[".rdata"]["va"]+secs[".rdata"]["vs"]
md = Cs(CS_ARCH_X86, CS_MODE_32); md.skipdata = True

cov = {}
with open(COVERAGE, encoding="utf-8") as f:
    f.readline()
    for line in f:
        p = line.rstrip("\n").split("\t")
        if len(p) >= 6:
            cov[p[0].upper()] = dict(subsystem=p[1], name=p[2], sem=p[3], grade=p[4], evidence=p[5])
atlas = set()
with open(ATLAS, encoding="utf-8") as f:
    f.readline()
    for line in f:
        p = line.rstrip("\n").split("\t")
        if p: atlas.add(p[0].upper())
print("coverage rows=%d atlas rows=%d" % (len(cov), len(atlas)))

text_bytes = rd(TEXT_S, TEXT_E-TEXT_S)
call_targets = set()
for pos in range(len(text_bytes)-5):
    op = text_bytes[pos]
    if op in (0xE8, 0xE9):
        rel = struct.unpack_from("<i", text_bytes, pos+1)[0]
        call_targets.add((TEXT_S + pos + 5 + rel) & 0xFFFFFFFF)

BEGIN, END = 0x812000, 0x815da4
NSLOT = (END-BEGIN)//4
assert NSLOT == 3945 and dword(BEGIN) == 0
targets = []
for i in range(1, NSLOT):
    slot = BEGIN + 4*i
    targets.append((i, slot, dword(slot)))
assert len(targets) == 3944 and all(t[2] != 0 for t in targets)

def prev_class(va):
    b = rd(va-1, 1)[0]
    return {0x90:"nop", 0xC3:"ret", 0xC2:"ret_imm", 0xCC:"int3", 0xEB:"jmp", 0xE9:"jmp"}.get(b, "other")

rows = []
notes = Counter()
for k,(idx, slot, tgt) in enumerate(targets):
    fb = rd(tgt,1)[0]
    pc = prev_class(tgt)
    nxt = targets[k+1][2] if k+1 < len(targets) else END+0x100
    limit = min(nxt, tgt+0x2000)
    if limit <= tgt: limit = tgt+0x2000
    bend = "fallthrough"
    for ins in md.disasm(rd(tgt, min(limit-tgt, 0x600)), tgt):
        if ins.address >= limit: break
        if ins.mnemonic.startswith("ret"):
            bend = "ret"; break
        if ins.mnemonic == "jmp":
            bend = "jmp"; break
    in_cov = ("%08X" % tgt) in cov
    in_atl = ("%08X" % tgt) in atlas
    verdict = "FUNC"
    note_parts = []
    if tgt % 16: note_parts.append("not16align")
    if fb in (0xE8,0xE9,0xEB): note_parts.append("firstbyte_jmp")
    if pc == "other": note_parts.append("pred_not_TERM")
    if bend == "fallthrough": note_parts.append("body_no_terminator")
    if not (TEXT_S <= tgt < TEXT_E): note_parts.append("target_outside_text")
    note = ";".join(note_parts)
    notes[note] += 1
    rows.append(dict(index=idx, slot=slot, target=tgt,
                     aligned16="Y" if tgt%16==0 else "N",
                     first_byte="0x%02X" % fb, prev=pc, bend=bend,
                     verdict=verdict, in_cov=in_cov, in_atl=in_atl, note=note))

cols = ["index","slot_addr","target","aligned16","first_byte","prev_byte_class",
        "body_end_kind","verdict","in_coverage","in_atlas","note"]
with open(os.path.join(CARD,"INITTERM_TABLE.tsv"),"w",encoding="utf-8",newline="") as f:
    f.write("\t".join(cols)+"\n")
    for r in rows:
        f.write("\t".join([str(r["index"]), "%08X"%r["slot"], "%08X"%r["target"],
            r["aligned16"], r["first_byte"], r["prev"], r["bend"], r["verdict"],
            "Y" if r["in_cov"] else "N", "Y" if r["in_atl"] else "N", r["note"]])+"\n")

st = dict(n_items=len(rows), n_func=sum(1 for r in rows if r["verdict"]=="FUNC"),
          n_not=sum(1 for r in rows if r["verdict"]=="NOT_FUNC"),
          n_und=sum(1 for r in rows if r["verdict"]=="UNDECIDABLE"),
          n_aligned=sum(1 for r in rows if r["aligned16"]=="Y"),
          n_in_cov=sum(1 for r in rows if r["in_cov"]),
          n_in_atlas=sum(1 for r in rows if r["in_atl"]),
          n_not_in_cov=sum(1 for r in rows if not r["in_cov"]),
          pred=Counter(r["prev"] for r in rows),
          bend=Counter(r["bend"] for r in rows),
          firstbyte_top=Counter(r["first_byte"] for r in rows).most_common(12),
          note_dist=dict(notes))
print("STATS:", json.dumps(st, ensure_ascii=False)[:1500])

dl = [r for r in rows if r["verdict"]=="FUNC" and not r["in_cov"]]
evrel = "lead/next_re_20261117_r14/P0_INITTERM/INITTERM_TABLE.tsv#%08X"
with open(os.path.join(CARD,"coverage_delta.tsv"),"w",encoding="utf-8",newline="") as f:
    f.write("entry\tsubsystem\tname\tone_line_semantics\tgrade\tevidence_path\n")
    for r in dl:
        idx = r["index"]
        sem = "_initterm 静态初始化表项 #%04d，调用静态对象构造器（实际 target=%08X）" % (idx, r["target"])
        f.write("\t".join(["%08X"%r["target"], "S22", "initterm_thunk_%04d"%idx,
                           sem, "[未证]", evrel % r["target"]])+"\n")
print("coverage_delta rows=%d" % len(dl))

with open(os.path.join(CARD,"EVIDENCE","t5_coverage.tsv"),"w",encoding="utf-8",newline="") as f:
    f.write("target\tname\tgrade\tsubsystem\tone_line_semantics\tevidence_path\n")
    for r in rows:
        if r["in_cov"]:
            c = cov["%08X"%r["target"]]
            f.write("\t".join(["%08X"%r["target"], c["name"], c["grade"], c["subsystem"],
                               c["sem"], c["evidence"]])+"\n")
with open(os.path.join(CARD,"EVIDENCE","t5_atlas.tsv"),"w",encoding="utf-8",newline="") as f:
    f.write("target\tin_call_jmp_target_set\n")
    for r in rows:
        if r["in_atl"]:
            f.write("\t".join(["%08X"%r["target"], "Y" if r["target"] in call_targets else "N"])+"\n")
n_ct = sum(1 for r in rows if r["target"] in call_targets)
st["n_targets_as_call_jmp"] = n_ct
st["atlas2_all_are_calltargets"] = all(r["target"] in call_targets for r in rows if r["in_atl"])

bucket_of = {}; bucket_feat = {}
for r in rows:
    tgt = r["target"]
    buf = rd(tgt, min(128, TEXT_E-tgt))
    feats = []
    for i in range(len(buf)-5):
        if buf[i] == 0xC7 and (buf[i+1] & 0xC7) == 0x05:
            imm = struct.unpack_from("<I", buf, i+2)[0]
            if RDATA_S <= imm < RDATA_E:
                feats.append("vptr_write:%08X" % imm)
        if buf[i] == 0xE8:
            rel = struct.unpack_from("<i", buf, i+1)[0]
            feats.append("call:%08X" % ((tgt+i+5+rel)&0xFFFFFFFF))
    if feats:
        bucket = "CTOR_vptr_or_call"
    else:
        mnems = [i.mnemonic for i in md.disasm(buf, tgt)]
        if any(m.startswith("f") and m not in ("fnstsw","fnclex","fninit","fldcw") for m in mnems):
            bucket = "FP_INIT"
        elif any(m in ("mov",) for m in mnems):
            bucket = "OTHER_STORE"
        else:
            bucket = "OTHER"
    bucket_of[tgt] = bucket
    bucket_feat[tgt] = ";".join(feats[:3])
st["buckets"] = dict(Counter(bucket_of.values()))
st.setdefault("bucket_reps",{})
for b in sorted(set(bucket_of.values())):
    reps = [r["target"] for r in rows if bucket_of[r["target"]]==b][:3]
    st["bucket_reps"][b] = ["%08X"%x for x in reps]
with open(os.path.join(CARD,"EVIDENCE","t3_buckets.tsv"),"w",encoding="utf-8",newline="") as f:
    f.write("index\ttarget\tbucket\tfeatures\n")
    for r in rows:
        f.write("\t".join([str(r["index"]),"%08X"%r["target"],bucket_of[r["target"]],bucket_feat[r["target"]]])+"\n")

with open(os.path.join(CARD,"EVIDENCE","stats.json"),"w",encoding="utf-8") as f:
    json.dump(st, f, indent=2, ensure_ascii=False, default=str)
print("DONE")
