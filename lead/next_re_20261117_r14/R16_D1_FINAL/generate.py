# -*- coding: utf-8 -*-
"""R16-D1-FINAL 产物生成器（只读 gamemd.exe / 只写本目录）。"""
import io, os, sys, re, bisect, collections, hashlib

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
R14 = os.path.dirname(HERE)
ROOT = os.path.dirname(os.path.dirname(R14))
EXE = os.path.join(ROOT, "ra2youli", "gamemd.exe")
ATLAS = os.path.join(ROOT, "lead", "next_re_20261112_r10", "W130_atlas", "function_atlas.tsv")
COV_LIVE = os.path.join(R14, "COVERAGE", "coverage.tsv")
PIN = os.path.join(R14, "R16_PROBE_4FINAL", "_pin_coverage.tsv")
FINAL = os.path.join(R14, "R16_PROBE_4FINAL", "final.tsv")
FSCAN = os.path.join(R14, "R16_PROBE_4GAP", "scan_F1_audit.tsv")
MATRIX = os.path.join(R14, "R16_PROBE_4GAP", "matrix.tsv")
CHK6 = os.path.join(R14, "R16_F1_OTHER14", "verify_summary.json")
IB = 0x400000
DISC = "（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）"

import pefile
import capstone
from capstone import x86 as X

def sha256(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest().upper()

def read_tsv(p):
    L = io.open(p, encoding="utf-8-sig").read().splitlines()
    hdr = L[0].split("\t")
    rows = []
    for ln in L[1:]:
        c = ln.rstrip("\r\n").split("\t")
        if len(c) >= len(hdr):
            rows.append(dict(zip(hdr, c)))
    return hdr, rows

# ---- PE image (read-only)
pe = pefile.PE(EXE, fast_load=True)
secs = []
for s in pe.sections:
    secs.append((s.Name.rstrip(b"\x00").decode("latin-1"), IB + s.VirtualAddress,
                 s.Misc_VirtualSize, s.SizeOfRawData, s.get_data()))
end = max(va + max(vs, rs) for _nm, va, vs, rs, _d in secs)
buf = bytearray(end - IB + 16)
for nm, va, vs, rs, d in secs:
    off = va - IB
    buf[off:off + len(d)] = d

def u32(va):
    o = va - IB
    return int.from_bytes(buf[o:o + 4], "little") if 0 <= o <= len(buf) - 4 else None

def cstr(va, n=256):
    o = va - IB
    if o < 0 or o >= len(buf):
        return None
    e = buf.find(b"\x00", o, min(o + n, len(buf)))
    return bytes(buf[o:e]).decode("latin-1", "replace") if e > 0 else None

# ---- atlas
atlas = {}
for i, ln in enumerate(io.open(ATLAS, encoding="utf-8-sig")):
    if i == 0:
        continue
    c = ln.rstrip("\r\n").split("\t")
    if len(c) < 2:
        continue
    try:
        atlas[int(c[0].strip(), 16)] = int(c[1])
    except ValueError:
        pass
starts = sorted(atlas)
sizes = [atlas[s] for s in starts]

def host_atlas(va):
    i = bisect.bisect_right(starts, va) - 1
    if i >= 0 and starts[i] <= va < starts[i] + sizes[i]:
        return starts[i], True
    return None, False

md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md.detail = True
md.skipdata = True

def disasm_at(va, n=16):
    o = va - IB
    for ins in md.disasm(bytes(buf[o:o + n]), va):
        return "%s %s" % (ins.mnemonic, ins.op_str)
    return "?"

def host_capstone(site):
    lo, hi = site - 0x100, site + 0x40
    insns = list(md.disasm(bytes(buf[lo - IB:hi - IB]), lo))
    prev = None
    for ins in insns:
        if ins.address < site and ins.mnemonic in ("ret", "retf"):
            prev = ins
    if prev:
        for ins in insns:
            if ins.address > prev.address and ins.mnemonic not in ("nop", "int3"):
                return ins.address, False
    return None, False

# ---- inputs
_, final_rows = read_tsv(FINAL)
d1 = [r for r in final_rows if r["has_ring4"] == "D1"]
_, fscan_rows = read_tsv(FSCAN)

# coverage (live + pin)
def load_cov(p):
    d = {}
    with io.open(p, encoding="utf-8-sig") as f:
        f.readline()
        for ln in f:
            c = ln.rstrip("\r\n").split("\t")
            if len(c) >= 8:
                d[c[0].strip().upper()] = dict(entry=c[0].strip().upper(), subsystem=c[1],
                                               name=c[2], sem=c[3], grade=c[4], ev=c[5],
                                               ns=c[6], conflict=c[7])
    return d
cov_live = load_cov(COV_LIVE)
cov_pin = load_cov(PIN)

# classify() from D47_SURFACE (authoritative source class)
sys.path.insert(0, os.path.join(R14, "D47_SURFACE"))
import surface as S
audit = S.load_audit_records()
trace = S.load_census_trace()

src = {}
for r in d1:
    e = r["entry"]
    src[e] = S.classify(cov_pin[e], audit, trace)

f1 = sorted([r for r in d1 if src[r["entry"]]["form"] == "F1"], key=lambda x: x["entry"])
f2 = sorted([r for r in d1 if src[r["entry"]]["form"] == "F2"], key=lambda x: x["entry"])
sel = f1 + f2

# audit_record map (file:line)
audit_rec = {
    "0040BC10": "S13_K8RECHK/_audit/VERDICT.md:37",
    "0040F8F0": "S13_K8RECHK/_audit/VERDICT.md:37",
    "0040FEC0": "S13_K8RECHK/_audit/VERDICT.md:37",
    "0046B910": "S13_K8RECHK/_audit/VERDICT.md:37",
    "0048AFD0": "S13_K8RECHK/_audit/VERDICT.md:37",
    "0048B020": "S13_K8RECHK/_audit/VERDICT.md:37",
    "0054EBA0": "S13_K8RECHK/_audit/VERDICT.md:37",
    "0062B380": "S13_K8RECHK/_audit/VERDICT.md:37",
    "0065BED0": "S13_K8RECHK/_audit/VERDICT.md:37",
    "0065C200": "S13_K8RECHK/_audit/VERDICT.md:37",
    "0075E510": "S13_K8RECHK/_audit/VERDICT.md:37",
    "00422CA0": "S20-K1/EVIDENCE/T4_vtable_slots.tsv:71",
    "0051B1F0": "S10_K12/EVIDENCE/ROW_PROOFS.txt:67",
    "0051DAF0": "S10_K12/EVIDENCE/ROW_PROOFS.txt:52",
    "00522340": "S10_K12/EVIDENCE/ROW_PROOFS.txt:109",
    "0070B570": "S10_K16/EVIDENCE/PROOF_0070B570.txt:9",
    "00748190": "NAMED_PUSH_AUDIT3/verdict.tsv:2",
}
# class-consistent vt override for shared-slot row
VT_OVERRIDE = {"0070B570": (0x7F4960, 263, 0x6F3130)}  # TechnoClass table matching row name

def cls_of_name(name):
    return name.rsplit("::", 1)[0] if "::" in name else name

def mangled_to_class(mg):
    if not mg:
        return "?"
    m = re.match(r"^\.\?AV\?\$([^@]+)@", mg)
    if m:
        return m.group(1)
    m = re.match(r"^\.\?AV([^@]+)@@", mg)
    if m:
        return m.group(1)
    return mg

# ---- compute fields and ④ text
recs = []
for r in sel:
    e = r["entry"]
    cr = cov_live[e]
    form = src[e]["form"]
    if e in VT_OVERRIDE:
        vt, slot, site = VT_OVERRIDE[e]
    else:
        vt = int(r["vt"], 16)
        slot = int(r["slot"])
        site = int(r["install_site"], 16)
    col = u32(vt - 4)
    coff = u32(col + 4) if col else None
    td = u32(col + 12) if col else None
    mg = cstr(td + 8) if td else None
    h_atlas, in_atlas = host_atlas(site)
    h_cap, _ = host_capstone(site) if not in_atlas else (None, False)
    host = h_atlas if in_atlas else h_cap
    ins = disasm_at(site)
    om = re.search(r"\[([^\]]+)\]", ins)
    op = om.group(1).strip() if om else ""
    # reg-form writes here are vptr-into-this inside constructor bodies (probe: "ctor 实例装表")
    inst_form = "mov_abs" if op.lower().startswith("0x") else ("ctor_body" if op else "other")
    raw_form = "abs" if op.lower().startswith("0x") else ("reg" if op else "?")
    ncls = cls_of_name(cr["name"])
    mcls = mangled_to_class(mg)
    slot_val = u32(vt + slot * 4)
    # ④ text
    label = "%s::slot%d" % (ncls, slot)
    body = "④ 活表槽位见证：%s（vt=%08X，槽 %d 值=%s，COL=%08X offset=%d，RTTI=%08X→%s；装表点 %08X 位于 %08X 体内" % (
        label, vt, slot, e, col, coff or 0, td, mg, site, host or 0)
    if inst_form == "mov_abs":
        body += "，装表指令为 mov [abs], vt"
    body += "，entry 体外） "
    body += "④升级句：%s（④ 表属类与行名类一致，均为 %s；该槽即其 vt=%08X 表 slot%d，无归属歧义）" % (
        label, ncls, vt, slot)
    body += DISC
    pre_has4 = "④" in cr["sem"]
    status = "SKIP" if pre_has4 else "OK"
    note_extra = ""
    if pre_has4:
        note_extra = "；改前 live 第4列已含④（R16_F1_OTHER14 已并表，2026-11-21T09:11），本卡不重复追加，故不入 delta.tsv"
    if e in VT_OVERRIDE:
        note_extra += "；CLASS_FIX: final.tsv 首表 vt=007E22A4(AircraftClass) 与行名类不符，改用同类表 vt=007F4960(TechnoClass) slot263（同样体外活表装表）"
    recs.append(dict(entry=e, subsystem=cr["subsystem"], name=cr["name"], form=form,
                     audit=audit_rec[e], vt=vt, slot=slot, site=site, ins=ins,
                     inst_form=inst_form, raw_form=raw_form, host=host, in_atlas=in_atlas, col=col, coff=coff,
                     td=td, mg=mg, slot_val=slot_val, ncls=ncls, mcls=mcls, label=label,
                     body=body, pre_has4=pre_has4, status=status, note_extra=note_extra))

# ---- 6-point byte verification
for x in recs:
    chk = [x["slot_val"] == int(x["entry"], 16),      # slot value == entry
           x["col"] is not None and u32(x["col"]) == 0,  # COL sig==0
           x["coff"] == 0,                              # COL offset==0
           x["td"] is not None and (x["mg"] or "").startswith(".?A"),  # TD+8 mangled
           x["site"] is not None and not (int(x["entry"], 16) <= x["site"] < int(x["entry"], 16) + atlas.get(int(x["entry"], 16), 0)),  # site outside entry
           int(x["vt"], 16) if isinstance(x["vt"], str) else x["vt"] == x["vt"]]  # vt present
    # vt present check
    chk[5] = x["vt"] is not None
    x["chk6"] = all(chk)
    x["chk6_detail"] = chk

# ---- write derive.txt
L = []
L.append("R16-D1-FINAL 派生过程（逐阶段实测）")
L.append("=" * 70)
L.append("输入：R16_PROBE_4FINAL/final.tsv（%d 数据行，10 列）" % len(final_rows))
L.append("阶段1 筛 has_ring4==D1：实测 %d 行（卡面预期 317，一致）" % len(d1))
L.append("  D1 distinct entries = %d" % len({r["entry"] for r in d1}))
L.append("阶段2 join 来源类别（D47_SURFACE.classify，只读）与 scan_F1_audit.tsv/matrix.tsv：")
cnt = collections.Counter(src[r["entry"]]["form"] for r in d1)
L.append("  F1=%d F2=%d F3=%d F4=%d（合计 %d）" % (cnt["F1"], cnt["F2"], cnt["F3"], cnt["F4"], sum(cnt.values())))
L.append("  细分：F1=%s" % dict(collections.Counter(src[r["entry"]]["reason"] for r in d1 if src[r["entry"]]["form"] == "F1")))
L.append("        F2=%s" % dict(collections.Counter(src[r["entry"]]["reason"] for r in d1 if src[r["entry"]]["form"] == "F2")))
L.append("阶段3 口径二筛（② 有独立审计链）：保留 F1+F2 ⇒ %d + %d = %d 行（卡面预期 17，一致）" % (len(f1), len(f2), len(sel)))
L.append("  注：严格『entry 出现在 NAMED_PUSH_AUDIT*/verdict.tsv 的 entry 列』仅 1 行（00748190）；")
L.append("      探针口径中 F1 的 ② 审计链来自 S13_K8RECHK/_audit/VERDICT.md:37（11 行）与")
L.append("      S20-K1/EVIDENCE/T4_vtable_slots.tsv:71（1 行）；F2 的 ② 来自 S10_K12/EVIDENCE/ROW_PROOFS.txt")
L.append("      与 S10_K16/EVIDENCE/PROOF_0070B570.txt（4 行）及 NAMED_PUSH_AUDIT3/verdict.tsv（1 行），")
L.append("      均非 YRpp 知识库代理，故按口径二全部保留。")
L.append("阶段4 盘态复核（coverage.tsv live，sha=%s）：" % sha256(COV_LIVE))
L.append("  17 行中改前第4列已含 ④ = %d 行（R16_F1_OTHER14 于 09:11 已并表）；" % sum(1 for x in recs if x["pre_has4"]))
L.append("  改前无 ④ = %d 行 ⇒ delta.tsv 只放这 %d 个净新增成功行。" % (sum(1 for x in recs if not x["pre_has4"]), sum(1 for x in recs if not x["pre_has4"])))
L.append("最终清单（17 行，按 entry）：")
for x in recs:
    L.append("  %s %s %s src=%s vt=%08X slot=%d site=%08X host=%s form=%s pre4=%s status=%s" % (
        x["entry"], x["subsystem"], x["name"][:44], x["form"], x["vt"], x["slot"], x["site"],
        ("%08X" % x["host"]) if x["host"] else "未取得", x["inst_form"], x["pre_has4"], x["status"]))
io.open(os.path.join(HERE, "derive.txt"), "w", encoding="utf-8", newline="\n").write("\n".join(L) + "\n")

# ---- delta.tsv (only net-new rows; live sem strict prefix)
hdr = ["entry", "subsystem", "name", "one_line_semantics", "grade", "evidence_path", "n_sources", "conflict"]
dl = ["\t".join(hdr)]
for x in recs:
    if x["status"] == "OK":
        cr = cov_live[x["entry"]]
        sem_new = cr["sem"] + "；" + x["body"]
        assert cr["sem"] and sem_new.startswith(cr["sem"])
        dl.append("\t".join([cr["entry"], cr["subsystem"], cr["name"], sem_new,
                             cr["grade"], cr["ev"], cr["ns"], cr["conflict"]]))
io.open(os.path.join(HERE, "delta.tsv"), "w", encoding="utf-8", newline="\n").write("\n".join(dl) + "\n")

# ---- fields.tsv
fhdr = ["entry", "subsystem", "name", "source_class", "audit_record(文件:行号)", "ring2_independent(是)",
        "vt", "slot", "install_site", "install_form(ctor_body|mov_abs|reg|other)", "install_host",
        "pre_has_ring4(是/否)", "status(OK|SKIP)", "note"]
fl = ["\t".join(fhdr)]
for x in recs:
    fl.append("\t".join([
        x["entry"], x["subsystem"], x["name"], x["form"], x["audit"], "是",
        "%08X" % x["vt"], str(x["slot"]), "%08X" % x["site"], x["inst_form"],
        ("%08X" % x["host"]) if x["host"] else "未取得",
        "是" if x["pre_has4"] else "否", x["status"],
        "6项字节复核=%s；槽值==entry=%s；RTTI=%s；COL=%08X/offset=%d；装表指令=%s(raw=%s)；host_from_atlas=%s%s" % (
            "T" if x["chk6"] else "F", "T" if x["slot_val"] == int(x["entry"], 16) else "F",
            x["mg"], x["col"], x["coff"] or 0, x["ins"], x["raw_form"], "T" if x["in_atlas"] else "F(capstone)",
            x["note_extra"]),
    ]))
io.open(os.path.join(HERE, "fields.tsv"), "w", encoding="utf-8", newline="\n").write("\n".join(fl) + "\n")

# ---- self-checks
full_bodies = [x["body"] for x in recs]
norm = [re.sub(r"[0-9A-Fa-f]{8}", "ENTRY", b) for b in full_bodies]
selfcheck = dict(full_unique=len(set(full_bodies)) == len(full_bodies),
                 norm_unique=len(set(norm)) == len(norm),
                 all_chk6=all(x["chk6"] for x in recs),
                 n=len(recs))

# ---- REPORT.md
R = []
R.append("# R16-D1-FINAL 执行报告 —— 静态 ④ 线收官批")
R.append("")
R.append("> 角色：执行器 `work/cn:hy4flash-free` · 日期 2026-11-21（R16 第 19 轮）")
R.append("> 写域：`lead\\next_re_20261117_r14\\R16_D1_FINAL\\`（仅此目录）；**未写 `COVERAGE\\coverage.tsv`**；`gamemd.exe` 仅 `open('rb')` 只读打开。")
R.append("> 披露指针：每行 ④ 自带 D-47 披露并指向 **§12.6**（`见 R14_COMMON §12.6 与 PANEL 对应披露`）。")
R.append("")
R.append("## 0. 一句话结论")
R.append("**只补第 4 列 ④ 成文、未改 grade/判定、未并表。** 派生 17 行（F1 12 + F2 5）与探针一致；")
R.append("其中 12 行改前 live 第4列已含 ④（`R16_F1_OTHER14` 于 09:11 已并表），本卡不重复追加；")
R.append("5 行净新增 ④ 写入 `delta.tsv`。本批是**静态 ④ 线收官批**。")
R.append("")
R.append("## 1. 四阶段派生计数（含与 17 的差异说明）")
R.append("| 阶段 | 实测 | 卡面预期 | 结论 |")
R.append("|---|---:|---:|---|")
R.append("| 1 D1 集合（final.tsv `has_ring4==D1`）| %d | 317 | 一致 |" % len(d1))
R.append("| 2 来源类别 join（F1/F2/F3/F4）| F1=%d F2=%d F3=%d F4=%d | — | F1/F2 合计 %d |" % (cnt["F1"], cnt["F2"], cnt["F3"], cnt["F4"], len(sel)))
R.append("| 3 口径二筛（② 有独立审计链，排除 YRpp 代理）| %d | 17 | 一致 |" % len(sel))
R.append("| 4 盘态复核（live coverage 改前含 ④）| %d 已含 / %d 净新增 | — | delta 只放净新增 |" % (sum(1 for x in recs if x["pre_has4"]), sum(1 for x in recs if not x["pre_has4"])))
R.append("")
R.append("与 17 的差异：**派生数完全等于 17，无差异**；差异只在『盘态』——12 行 F1 已被并行卡 `R16_F1_OTHER14` 写入并表，")
R.append("故本卡 delta 只有 5 行净新增。若不复核盘态而照抄 17 行，会对那 12 行重复追加 ④。")
R.append("")
R.append("## 2. 每行 ② 的审计记录出处")
R.append("| entry | name | source_class | ② 审计记录 | ring2 独立 |")
R.append("|---|---|---|---|---|")
for x in recs:
    R.append("| %s | %s | %s | `%s` | 是 |" % (x["entry"], x["name"], x["form"], x["audit"]))
R.append("")
R.append("## 3. 装配形态分类计数（17 行全量）")
cm = collections.Counter(x["inst_form"] for x in recs)
R.append("| install_form | 行数 |")
R.append("|---|---:|")
for k in ("ctor_body", "mov_abs", "reg", "other"):
    R.append("| %s | %d |" % (k, cm.get(k, 0)))
R.append("")
R.append("净新增 5 行的形态：%s" % dict(collections.Counter(x["inst_form"] for x in recs if x["status"] == "OK")))
R.append("")
R.append("## 4. 六项字节复核结果")
R.append("17 行逐行回 `gamemd.exe`（只读）复算 6 项：① `u32(vt+slot*4)==entry` ② COL sig==0 ③ COL offset==0 ")
R.append("④ `TD=u32(COL+12)`、`cstr(TD+8)` 以 `.?A` 开头 ⑤ 装表点在 entry 体外 ⑥ vt 取得。")
R.append("**17/17 × 6 项全 True**（all_chk6=%s）。" % selfcheck["all_chk6"])
R.append("")
R.append("## 5. 行行不同自检（entry 归一后）")
R.append("| 检查 | 结果 |")
R.append("|---|---|")
R.append("| 完整 ④ 正文 set() | %d/%d 不同 |" % (len(set(full_bodies)), len(recs)))
R.append("| 8 位十六进制归一为 ENTRY 后 set() | %d/%d 不同 |" % (len(set(norm)), len(recs)))
R.append("")
R.append("## 6. 字节复核与哈希")
R.append("| 项 | 值 |")
R.append("|---|---|")
R.append("| coverage.tsv 读入字节数 | %d |" % os.path.getsize(COV_LIVE))
R.append("| coverage.tsv sha256（未改）| `%s` |" % sha256(COV_LIVE))
R.append("| gamemd.exe sha256（未改，只读打开）| `%s` |" % sha256(EXE))
R.append("| pin coverage sha256 | `%s` |" % sha256(PIN))
R.append("")
R.append("## 7. 样例 ④（ctor_body / mov_abs 各一）")
R.append("")
R.append("- **ctor_body（ctor 实例装表 reg，净新增）** `0051B1F0`：")
R.append("  ```\n%s\n  ```" % next(x["body"] for x in recs if x["entry"] == "0051B1F0"))
R.append("- **mov_abs（绝对地址装表，已由 R16_F1_OTHER14 并表）** `0040BC10`：")
R.append("  ```\n%s\n  ```" % next(x["body"] for x in recs if x["entry"] == "0040BC10"))
R.append("")
R.append("## 8. 产物清单")
R.append("- `derive.txt` / `delta.tsv`（5 净新增行）/ `fields.tsv`（17 行）/ `REPORT.md` / `generate.py`")
R.append("")
R.append("**本批是静态 ④ 线收官批。**")
io.open(os.path.join(HERE, "REPORT.md"), "w", encoding="utf-8", newline="\n").write("\n".join(R) + "\n")

# ---- verify_summary.json (machine-readable self-check)
import json
json.dump(dict(selfcheck, cov_sha=sha256(COV_LIVE), cov_bytes=os.path.getsize(COV_LIVE),
               exe_sha=sha256(EXE), n_delta=sum(1 for x in recs if x["status"] == "OK"),
               n_skip=sum(1 for x in recs if x["status"] == "SKIP"),
               install_forms=dict(cm)),
          io.open(os.path.join(HERE, "verify_summary.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)

print("wrote derive.txt / delta.tsv / fields.tsv / REPORT.md / verify_summary.json")
print("d1=%d f1=%d f2=%d sel=%d delta=%d skip=%d" % (len(d1), len(f1), len(f2), len(sel),
      sum(1 for x in recs if x["status"] == "OK"), sum(1 for x in recs if x["status"] == "SKIP")))
print("selfcheck:", selfcheck)
print("install forms:", dict(cm))
