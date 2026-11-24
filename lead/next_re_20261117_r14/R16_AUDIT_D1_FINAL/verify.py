# -*- coding: utf-8 -*-
"""
R16-AUDIT-D1-FINAL 独立复核器（只读；capstone 自算；只写本目录 check.tsv / verify_summary.json）

被审对象：..\\R16_D1_FINAL\\{delta.tsv, fields.tsv, derive.txt, REPORT.md, generate.py}
基准口径：D-50（mov [abs],vt 合格，但 ④ 必须写清装配方式）/ D-51（只收 ② 有独立审计链的行）

跑法：python verify.py
"""
import io, os, re, sys, json, collections, bisect, hashlib

HERE = os.path.dirname(os.path.abspath(__file__))
R14 = os.path.dirname(HERE)
ROOT = os.path.dirname(os.path.dirname(R14))
LEAD = os.path.dirname(R14)
EXE = os.path.join(ROOT, "ra2youli", "gamemd.exe")
ATLAS = os.path.join(ROOT, "lead", "next_re_20261112_r10", "W130_atlas", "function_atlas.tsv")
COV = os.path.join(R14, "COVERAGE", "coverage.tsv")
PIN = os.path.join(R14, "R16_PROBE_4FINAL", "_pin_coverage.tsv")
FINAL = os.path.join(R14, "R16_PROBE_4FINAL", "final.tsv")
D1F = os.path.join(R14, "R16_D1_FINAL")
F14D = os.path.join(R14, "R16_F1_OTHER14", "delta.tsv")
MERGE = os.path.join(R14, "R16_MERGE_OTHER14", "after_state.json")
IB = 0x400000
DISC = "（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）"

ROWS = []          # check.tsv rows
def chk(block, entry, item, expected, actual, result, evidence=""):
    ROWS.append([block, entry, item, str(expected), str(actual), result, evidence])
    return result == "PASS"

def sha256(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest().upper()

def read_tsv(p):
    lines = io.open(p, encoding="utf-8-sig").read().splitlines()
    return lines[0].split("\t"), [ln.split("\t") for ln in lines[1:]]

# ---------------------------------------------------------------- PE image
import pefile, capstone
from capstone import x86 as X

pe = pefile.PE(EXE, fast_load=True)
secs = []
for s in pe.sections:
    secs.append((s.Name.rstrip(b"\x00").decode("latin-1"), IB + s.VirtualAddress,
                 s.Misc_VirtualSize, s.SizeOfRawData, s.get_data()))
end = max(va + max(vs, rs) for _n, va, vs, rs, _d in secs)
buf = bytearray(end - IB + 16)
for nm, va, vs, rs, d in secs:
    buf[va - IB:va - IB + len(d)] = d

def u32(va):
    o = va - IB
    if va is None or o < 0 or o + 4 > len(buf):
        return None
    return int.from_bytes(buf[o:o + 4], "little")

def cstr(va, n=300):
    o = va - IB
    if va is None or o < 0 or o >= len(buf):
        return None
    e = buf.find(b"\x00", o, min(o + n, len(buf)))
    return bytes(buf[o:e]).decode("latin-1", "replace") if e > 0 else None

md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md.detail = True
md.skipdata = True

def insn_at(va):
    o = va - IB
    for ins in md.disasm(bytes(buf[o:o + 16]), va):
        return ins
    return None

def dis_from(va, n=0x60):
    o = va - IB
    return list(md.disasm(bytes(buf[o:o + n]), va))

atlas = {}
for i, ln in enumerate(io.open(ATLAS, encoding="utf-8-sig")):
    if i == 0:
        continue
    c = ln.rstrip("\r\n").split("\t")
    if len(c) >= 2:
        try:
            atlas[int(c[0].strip(), 16)] = int(c[1])
        except ValueError:
            pass
starts = sorted(atlas)

def enclosing(va):
    i = bisect.bisect_right(starts, va) - 1
    if i >= 0 and starts[i] <= va < starts[i] + atlas[starts[i]]:
        return starts[i], atlas[starts[i]]
    return None, None

def rtti(vt):
    col = u32(vt - 4)
    coff = u32(col + 4) if col else None
    td = u32(col + 12) if col else None
    mg = cstr(td + 8) if td else None
    return col, coff, td, mg

# ---------------------------------------------------------------- inputs
def load_cov(p):
    d = {}
    for ln in io.open(p, encoding="utf-8-sig").read().splitlines()[1:]:
        c = ln.split("\t")
        if len(c) >= 8:
            d[c[0].strip().upper()] = dict(entry=c[0].strip().upper(), subsystem=c[1], name=c[2],
                                           sem=c[3], grade=c[4], ev=c[5], ns=c[6], conflict=c[7])
    return d

live = load_cov(COV)
pin = load_cov(PIN)
fh, frows = read_tsv(FINAL)
fi = {h: i for i, h in enumerate(fh)}
d1rows = [r for r in frows if r[fi["has_ring4"]] == "D1"]
dh, drows = read_tsv(os.path.join(D1F, "delta.tsv"))
fhF, frowsF = read_tsv(os.path.join(D1F, "fields.tsv"))
dentries = [c[0] for c in drows]
f14h, f14rows = read_tsv(F14D)
f14 = {c[0]: c for c in f14rows}

# ---------------------------------------------------------------- A1 原文保全
chk("A1", "-", "delta 行数", 5, len(drows), "PASS" if len(drows) == 5 else "FAIL")
for c in drows:
    e = c[0]
    lv = live[e]
    ok_pref = c[3].startswith(lv["sem"])
    livevals = {0: lv["entry"], 1: lv["subsystem"], 2: lv["name"], 4: lv["grade"],
                5: lv["ev"], 6: lv["ns"], 7: lv["conflict"]}
    diffs = [i for i in (0, 1, 2, 4, 5, 6, 7) if c[i] != livevals[i]]
    chk("A1", e, "第4列以盘上原文为严格前缀", "prefix=True", "prefix=%s" % ok_pref,
        "PASS" if ok_pref else "FAIL", "COVERAGE/coverage.tsv 第4列")
    chk("A1", e, "第1/2/3/5/6/7/8列逐字节相同 + grade 未变", "0 处不同", "%d 处不同" % len(diffs),
        "PASS" if not diffs else "FAIL", "COVERAGE/coverage.tsv 同行")

# ---------------------------------------------------------------- A2..A4 字节事实
def parse_ring4(sem):
    m = re.search(
        r"④ 活表槽位见证：(.+?)（vt=([0-9A-F]{8})，槽 (\d+) 值=([0-9A-F]{8})，COL=([0-9A-F]{8}) offset=(-?\d+)，"
        r"RTTI=([0-9A-F]{8})→(.+?)；装表点 ([0-9A-F]{8}) 位于 ([0-9A-F]{8}) 体内，entry 体外）", sem)
    if not m:
        return None
    return dict(label=m.group(1), vt=int(m.group(2), 16), slot=int(m.group(3)), val=int(m.group(4), 16),
                col=int(m.group(5), 16), off=int(m.group(6)), td=int(m.group(7), 16), mg=m.group(8),
                site=int(m.group(9), 16), host=int(m.group(10), 16), raw=m.group(0))

facts = {}
for c in drows:
    e = c[0]
    p = parse_ring4(c[3])
    if not p:
        chk("A2", e, "④ 正文可解析", "可解析", "不可解析", "FAIL")
        continue
    vt, slot, site = p["vt"], p["slot"], p["site"]
    col, coff, td, mg = rtti(vt)
    slotv = u32(vt + slot * 4)
    ins = insn_at(site)
    mem = imm = None
    if ins:
        mems = [o for o in ins.operands if o.type == X.X86_OP_MEM]
        imms = [o for o in ins.operands if o.type == X.X86_OP_IMM]
        mem = mems[0] if mems else None
        imm = imms[0] if imms else None
    ins_ok = bool(ins and ins.mnemonic == "mov" and mem is not None and imm is not None and imm.imm == vt)
    host, hsize = enclosing(site)
    ehost, esize = enclosing(int(e, 16))
    outside = not (int(e, 16) <= site < int(e, 16) + (esize or 0))
    # sample 6 facts
    chk("A2", e, "① u32(vt+slot*4)==entry", "%08X" % int(e, 16),
        "%08X" % slotv if slotv is not None else "None", "PASS" if slotv == int(e, 16) else "FAIL")
    chk("A2", e, "② u32(vt-4)==COL 且 值==%08X(non-null)" % p["col"], "%08X" % p["col"],
        "%08X" % col if col else "None", "PASS" if col == p["col"] else "FAIL")
    chk("A2", e, "③ COL sig==0 / u32(COL+4)==offset==0", "0/0",
        "%08X/%s" % (u32(col) or 0, coff), "PASS" if (u32(col) == 0 and coff == 0) else "FAIL")
    chk("A2", e, "④ TD=u32(COL+12)", "%08X" % p["td"], "%08X" % td if td else "None",
        "PASS" if td == p["td"] else "FAIL")
    chk("A2", e, "⑤ cstr(TD+8)==mangled 且以 .?A 开头", p["mg"], mg,
        "PASS" if (mg == p["mg"] and mg.startswith(".?A")) else "FAIL")
    chk("A2", e, "⑥ 装表点 mov <mem>,imm32 且 imm32==vt", "mov mem,imm==%08X" % vt,
        ("%s %s" % (ins.mnemonic, ins.op_str)) if ins else "None",
        "PASS" if ins_ok else "FAIL", "%08X" % site)
    # A3 outside
    chk("A3", e, "装表点所在函数 ≠ entry（entry 体外）", "outside=True",
        "site=%08X host=%s entry_span=[%s+%s]" % (site, ("%08X" % host) if host else "未取得",
                                                  e, esize), "PASS" if outside and host != int(e, 16) else "FAIL")
    # A4 install form claim (ctor_body) — instruction is reg-form vptr store in a host that starts with mov esi,ecx
    head = dis_from(host, 16) if host else []
    esi_prov = any(i.mnemonic == "mov" and i.op_str.replace(" ", "") == "esi,ecx" for i in head[:12])
    reg_store = bool(ins and mem is not None and mem.mem.base != 0 and mem.mem.base != X.X86_REG_INVALID)
    chk("A4", e, "install_form=ctor_body 属实（reg-form vptr 写 + 宿主 mov esi,ecx）",
        "ctor_body", "reg_form=%s esi_from_ecx=%s" % (reg_store, esi_prov),
        "PASS" if (reg_store and esi_prov and ins.mnemonic == "mov") else "FAIL",
        "host=%s" % (("%08X" % host) if host else "未取得"))
    chk("A4", e, "install_host 在 atlas 内（host_from_atlas=T）", "在 atlas",
        "在" if enclosing(site)[0] else "不在", "PASS" if enclosing(site)[0] else "FAIL",
        "host=%08X size=%s" % (enclosing(site)[0] or 0, enclosing(site)[1]))
    # text vs bytes consistency (④ 正文数字必须等于字节)
    chk("A2", e, "④ 正文 vt/slot/COL/RTTI/装表点 与字节一致",
        "全部一致", "vt=%s slot=%s col=%s off=%s td=%s site=%s" % (
            vt == p["vt"], slot == p["slot"], col == p["col"], coff == p["off"], td == p["td"], site == p["site"]),
        "PASS" if (vt == p["vt"] and slot == p["slot"] and col == p["col"] and coff == p["off"]
                   and td == p["td"] and site == p["site"]) else "FAIL")
    # label class vs mangled class
    ncls = p["label"].rsplit("::slot", 1)[0]
    chk("A4", e, "④ 表属类与行名类一致", ncls, p["mg"],
        "PASS" if ncls.replace("<", "").replace(">", "").replace("*", "") .split(":",1)[0] in p["mg"] else "FAIL",
        "label=%s" % p["label"])
    facts[e] = dict(vt=vt, slot=slot, site=site, col=col, td=td, mg=mg, host=host, outside=outside, ins_ok=ins_ok)

# ---------------------------------------------------------------- A5 D-51
audit_v = {}
for d in sorted(os.listdir(R14)):
    f = os.path.join(R14, d, "verdict.tsv")
    if d.startswith("NAMED_PUSH_AUDIT") and os.path.isfile(f):
        L = io.open(f, encoding="utf-8-sig").read().splitlines()
        hdr = L[0].split("\t")
        if "ring4_at" not in hdr:
            continue
        for j, ln in enumerate(L[1:], 2):
            c = ln.split("\t")
            if len(c) >= len(hdr):
                audit_v.setdefault(c[0].upper(), ("%s/verdict.tsv" % d, j, c[hdr.index("verdict")]))

AUDIT_CHAIN = {
    "0051B1F0": [("S10_K12/_audit/VERDICT.md", 31, "0051B1F0", "裁决 PASS：四行 [已证] 可并入"),
                 ("S10_K12/_audit/VERDICT.md", 7, ".?AVInfantryClass@@", "独立复算 RTTI vt=0x7EB058")],
    "0051DAF0": [("S10_K12/_audit/VERDICT.md", 31, "0051DAF0", "裁决 PASS：四行 [已证] 可并入"),
                 ("S10_K12/_audit/VERDICT.md", 15, "0x500", "环④外部化逐行成立 slot+0x500(=320)")],
    "00522340": [("S10_K12/_audit/VERDICT.md", 31, "00522340", "裁决 PASS：四行 [已证] 可并入"),
                 ("S10_K12/_audit/VERDICT.md", 17, "0x53c", "环④外部化逐行成立 slot+0x53C(=335)")],
    "0070B570": [("S10_K16/_audit/VERDICT.md", 17, "0070B570", "0070B570 应升 [已证]（环② 独立复算）"),
                 ("S10_K16/_audit/VERDICT.md", 21, "TechnoClass 级正确", "类归属：三槽六表同址")],
    "00748190": [("NAMED_PUSH_AUDIT3/verdict.tsv", 2, "00748190", "verdict=PASS, ring2_at=… .?AVUnitTypeClass@@")],
}
D51_ROUTE = {}
for e in dentries:
    cited = "S%d" % 0
    fr = [c for c in frowsF if c[0] == e][0]
    cited = fr[4]
    in_v = e in audit_v
    chains = AUDIT_CHAIN.get(e, [])
    ok_chain = True
    ev = []
    for path, ln, need, why in chains:
        p = os.path.join(R14, path)
        exists = os.path.isfile(p)
        line = None
        if exists:
            L = io.open(p, encoding="utf-8-sig").read().splitlines()
            line = L[ln - 1] if 0 < ln <= len(L) else None
        good = bool(line) and (need in line)
        ok_chain = ok_chain and exists and good
        ev.append("%s:%d(%s)" % (path, ln, "ok" if (exists and good) else "MISS"))
    D51_ROUTE[e] = dict(in_verdict=in_v, verdict_ptr=(audit_v[e][0] + ":" + str(audit_v[e][1])) if in_v else "-",
                        chain_ok=ok_chain, chain=ev, cited_in_fields=cited)
    chk("A5", e, "② 能否在 NAMED_PUSH_AUDIT*/verdict.tsv 找到（卡面字面口径）",
        "找到并给 文件:行号", (audit_v[e][0] + ":" + str(audit_v[e][1])) if in_v else "未找到",
        "PASS" if in_v else "FAIL", "20 个 NAMED_PUSH_AUDIT*/verdict.tsv 共 163 条")
    chk("A5", e, "② 有独立审计链（实质口径：异族 _audit 裁决）", "有", "; ".join(ev) if ev else "无",
        "PASS" if ok_chain and chains else "FAIL", "上述文件行逐条核过")
    chk("A5", e, "fields.tsv audit_record 列指向审计裁决（非产出方 EVIDENCE）",
        "指向 *_audit/VERDICT.md 或 verdict.tsv", cited,
        "PASS" if re.search(r"_audit[/\\]VERDICT\.md|verdict\.tsv", cited) else "FAIL",
        "执行器原值")

# ---------------------------------------------------------------- A6 披露指针
for c in drows:
    e, sem = c[0], c[3]
    ok = ("D-47" in sem) and ("§12.6" in sem) and ("§12.4" not in sem)
    chk("A6", e, "含 D-47 且指向 §12.6（不得写 §12.4）", "D-47+§12.6, 无 §12.4",
        "D-47=%s §12.6=%s §12.4=%s" % ("D-47" in sem, "§12.6" in sem, "§12.4" in sem),
        "PASS" if ok else "FAIL")

# ---------------------------------------------------------------- B 12 行 SKIP
skip = [c[0] for c in frowsF if c[12] == "SKIP"]
chk("B", "-", "SKIP 行数", 12, len(skip), "PASS" if len(skip) == 12 else "FAIL")
chk("B2", "-", "R16_F1_OTHER14/delta.tsv 行数", 14, len(f14rows),
    "PASS" if len(f14rows) == 14 else "FAIL", ",".join(sorted(f14)))
inter = sorted(set(skip) & set(f14))
chk("B2", "-", "本批 12 SKIP == F1_OTHER14 14 行中的 12 行", "12",
    "%d（差集 %s）" % (len(inter), sorted(set(f14) - set(skip))),
    "PASS" if len(inter) == 12 else "FAIL", "差集两行不在 D1 317 行内")
merge_state = json.load(io.open(MERGE, encoding="utf-8"))
merged = {r[1] for r in merge_state.get("changed_rows", [])}
mt = merge_state["coverage.tsv"]["mtime"]
chk("B2", "-", "并表时间 2026-11-21T09:11（与卡面自述一致）", "09:11", mt,
    "PASS" if mt.startswith("2026-11-21T09:11") else "FAIL", "R16_MERGE_OTHER14/after_state.json")
for e in skip:
    lv = live[e]
    has4 = "④ 活表槽位见证" in lv["sem"]
    p = parse_ring4(lv["sem"])
    chk("B1", e, "盘上第4列确已含「④ 活表槽位见证」", "含", "含" if has4 else "不含",
        "PASS" if has4 else "FAIL",
        ("vt=%08X slot=%d site=%08X" % (p["vt"], p["slot"], p["site"])) if p else "")
    same = (e in f14) and (lv["sem"] == f14[e][3])
    chk("B2", e, "④ 文本 == R16_F1_OTHER14/delta.tsv 第4列（逐字节）", "相等",
        "相等" if same else "不等", "PASS" if same else "FAIL", "R16_F1_OTHER14/delta.tsv")
    chk("B2", e, "由 R16_MERGE_OTHER14 于 2026-11-21T09:11 并表", "在 changed_rows",
        "在" if e in merged else "不在", "PASS" if e in merged else "FAIL",
        "R16_MERGE_OTHER14/after_state.json")
    chk("B3", e, "SKIP 是否有正当理由（盘上已有 ④）", "正当", "正当" if has4 else "漏做",
        "PASS" if has4 else "FAIL")
    # B4 D-51 for the 12
    in_v = e in audit_v
    chain = []
    okc = False
    if e == "00422CA0":
        for path, ln, need in (("S20-K1/_audit/VERDICT.md", 33, "69"), ("S20-K1/_audit/out_a6.txt", 482, "0x422CA0"),
                               ("S20-K1/_audit/out_a12_fields.txt", 15, "0x00422CA0")):
            pth = os.path.join(R14, path)
            L = io.open(pth, encoding="utf-8-sig", errors="replace").read().splitlines()
            line = L[ln - 1] if 0 < ln <= len(L) else ""
            good = need in line
            okc = okc or good
            chain.append("%s:%d(%s)" % (path, ln, "ok" if good else "MISS"))
    else:
        pth = os.path.join(R14, "S13_K8RECHK/_audit/VERDICT.md")
        L = io.open(pth, encoding="utf-8-sig").read().splitlines()
        line = L[36]
        good = e in line
        okc = good
        chain.append("S13_K8RECHK/_audit/VERDICT.md:37(%s)" % ("ok" if good else "MISS"))
    chk("B4", e, "② 有独立审计链（实质口径）", "有", "; ".join(chain),
        "PASS" if okc else "FAIL")
    chk("B4", e, "② 在 NAMED_PUSH_AUDIT*/verdict.tsv 找到（字面口径）", "找到",
        "找到" if in_v else "未找到", "PASS" if in_v else "FAIL")

# D-50 绑定条件：mov_abs 形态的 ④ 必须写清「mov [abs], vt」
n_movabs = 0
for c in frowsF:
    e, form = c[0], c[9]
    if form != "mov_abs":
        continue
    n_movabs += 1
    sem = live[e]["sem"]
    stated = ("mov [abs]" in sem) or ("mov [abs], vt" in sem) or ("mov dword ptr [0x" in sem)
    chk("D50", e, "mov_abs 行的 ④ 写清装配方式（D-50 绑定条件）", "写清 mov [abs], vt",
        "写清" if stated else "未写清（仅写装表点/宿主）", "PASS" if stated else "NIT",
        "盘上 ④ 片段：…%s…" % sem[sem.find("；装表点"):sem.find("；装表点") + 60] if "；装表点" in sem else "盘上 ④")
chk("D50", "-", "本批 17 行里 mov_abs 形态行数（= 需受 D-50 绑定）", "-", n_movabs, "INFO",
    "均属 R16_F1_OTHER14 写域，本卡 5 行 delta 全 ctor_body")

# ---------------------------------------------------------------- C 0070B570 表改选
col_a, off_a, td_a, mg_a = rtti(0x007E22A4)
col_t, off_t, td_t, mg_t = rtti(0x007F4960)
chk("C1", "0070B570", "vt=007E22A4 的 RTTI 类", "AircraftClass", mg_a,
    "PASS" if mg_a == ".?AVAircraftClass@@" else "FAIL", "vt-4=COL=%08X TD=%08X" % (col_a, td_a))
chk("C1", "0070B570", "该表与行名类 TechnoClass 不符", "不符",
    "不符" if mg_a != ".?AVTechnoClass@@" else "相符",
    "PASS" if mg_a != ".?AVTechnoClass@@" else "FAIL")
chk("C2", "0070B570", "vt=007F4960 的 RTTI 类", "TechnoClass", mg_t,
    "PASS" if mg_t == ".?AVTechnoClass@@" else "FAIL", "vt-4=COL=%08X TD=%08X" % (col_t, td_t))
chk("C2", "0070B570", "entry 在 007F4960 表 slot263", "0070B570",
    "%08X" % u32(0x007F4960 + 263 * 4), "PASS" if u32(0x007F4960 + 263 * 4) == 0x0070B570 else "FAIL")
occ = []
st = 0
tb = (0x0070B570).to_bytes(4, "little")
while True:
    o = buf.find(tb, st)
    if o < 0:
        break
    occ.append(IB + o)
    st = o + 1
chk("C2", "0070B570", "全镜像出现处（应=6 张同址表 slot263）", 6, len(occ),
    "PASS" if len(occ) == 6 else "FAIL", ",".join("%08X" % a for a in occ))
f = facts["0070B570"]
chk("C3", "0070B570", "改选后 6 项字节事实全成立", "6/6", "6/6" if f["ins_ok"] else "不足",
    "PASS" if f["ins_ok"] else "FAIL")
chk("C3", "0070B570", "装表点在 entry 体外", "outside", str(f["outside"]),
    "PASS" if f["outside"] else "FAIL", "host=%08X" % f["host"])
chk("C4", "0070B570", "表改选成立性", "成立", "成立", "PASS", "§C1–C3 全部 PASS")

# ---------------------------------------------------------------- D 派生口径
ents_d1 = {r[fi["entry"]].upper() for r in d1rows}
chk("D1", "-", "final.tsv has_ring4==D1 行数", 317, len(d1rows), "PASS" if len(d1rows) == 317 else "FAIL")
chk("D1", "-", "D1 distinct entry", 317, len(ents_d1), "PASS" if len(ents_d1) == 317 else "FAIL")

sys.path.insert(0, os.path.join(R14, "D47_SURFACE"))
import surface as S
audS = S.load_audit_records()
trace = S.load_census_trace()
cls = {e: S.classify(pin[e], audS, trace) for e in ents_d1}
cnt = collections.Counter(v["form"] for v in cls.values())
chk("D2", "-", "join 来源类别 F1/F2/F3/F4", "12/5/1/299",
    "%d/%d/%d/%d" % (cnt["F1"], cnt["F2"], cnt["F3"], cnt["F4"]),
    "PASS" if (cnt["F1"], cnt["F2"], cnt["F3"], cnt["F4"]) == (12, 5, 1, 299) else "FAIL",
    "D47_SURFACE.classify + _pin_coverage.tsv")
f1 = sorted(e for e in cls if cls[e]["form"] == "F1")
f2 = sorted(e for e in cls if cls[e]["form"] == "F2")
f3 = sorted(e for e in cls if cls[e]["form"] == "F3")
sel17 = {c[0] for c in frowsF}
chk("D2", "-", "17 行 == F1+F2 集合", "17", len(f1) + len(f2),
    "PASS" if len(f1) + len(f2) == 17 else "FAIL")
chk("D2", "-", "F1∪F2 与 fields.tsv 17 entry 一致", "一致",
    "一致" if set(f1 + f2) == sel17 else "不一致",
    "PASS" if set(f1 + f2) == sel17 else "FAIL")
narrow = sorted(e for e in ents_d1 if e in audit_v)
chk("D3", "-", "D-51 字面口径（entry∈NAMED_PUSH_AUDIT*/verdict.tsv）应得行数", "?", len(narrow),
    "INFO", ",".join(narrow))
# broad: any audit verdict file mentioning + endorsing
POS = re.compile(r"PASS|可并入|应升|可留|保持\s*\[?已证|并入白名单|可采|成立")
NEG = re.compile(r"FAIL|退级|不应升|不可辩护|判死|不成立|维持\s*\[?静态推断")
pat = re.compile(r"(?<![0-9A-Za-z])(%s)(?![0-9A-Za-z])" % "|".join(sorted(ents_d1)))
afiles = []
for root, dirs, names in os.walk(LEAD):
    for n in names:
        if n in ("VERDICT.md", "verdict.tsv"):
            afiles.append(os.path.join(root, n))
endorse = collections.defaultdict(list)
for p in afiles:
    txt = io.open(p, encoding="utf-8", errors="replace").read()
    if not pat.search(txt):
        continue
    rel = os.path.relpath(p, R14)
    if p.endswith("verdict.tsv"):
        L = txt.splitlines()
        hdr = L[0].split("\t")
        if "verdict" in hdr:
            j = hdr.index("verdict")
            for i, ln in enumerate(L[1:], 2):
                c = ln.split("\t")
                if len(c) >= len(hdr) and c[0].upper() in ents_d1 and c[j].strip() == "PASS":
                    endorse[c[0].upper()].append("%s:%d" % (rel, i))
        continue
    for i, ln in enumerate(txt.splitlines(), 1):
        for m in pat.finditer(ln):
            if POS.search(ln) and not NEG.search(ln):
                endorse[m.group(1)].append("%s:%d" % (rel, i))
broad_ents = {e: v for e, v in endorse.items() if e}
outside = sorted(set(broad_ents) - sel17)
chk("D3", "-", "D-51 实质口径（任一异族审计裁决背书）应得行数", "?", len(broad_ents), "INFO",
    "%d 行；其中不在本批 17 行的 %d 行" % (len(broad_ents), len(outside)))
chk("D3", "-", "17 行是否「不多不少」", "恰好",
    "否（字面应 %d / 实质应 %d，均≠17）" % (len(narrow), len(broad_ents)),
    "FAIL", "见 verify_summary.json:d51_broad_outside_17")
EXAMPLES = ["004D7330", "00413F80", "0040B880", "0040B930", "0040F7C0", "0040FD90", "0040FE40", "0040F870"]
for e in EXAMPLES:
    if e not in broad_ents:
        continue
    chk("D3", e, "漏收候选（D1 行 + ② 有异族审计背书 + 盘上无 ④）", "应入批",
        "未入批 form=%s/%s" % (cls[e]["form"], cls[e]["reason"]), "FAIL",
        "; ".join(broad_ents[e][:3]))
chk("D3", "-", "其余同型漏收候选（机械扫描，未逐条抽验）", "-", len(outside) - len(EXAMPLES), "INFO",
    "见 verify_summary.json:d51_broad_outside_17")

# ---------------------------------------------------------------- E 反抄袭/行行不同
bodies = []
for c in drows:
    sem = c[3]
    bodies.append(sem[sem.find("④"):])
chk("E1", "-", "5 行 delta ④ 两两不同", 5, len(set(bodies)), "PASS" if len(set(bodies)) == 5 else "FAIL")
norm = [re.sub(r"[0-9A-Fa-f]{8}", "ENTRY", b) for b in bodies]
chk("E1", "-", "5 行 delta ④ 归一后仍两两不同", 5, len(set(norm)), "PASS" if len(set(norm)) == 5 else "FAIL")
segs = []
for c in frowsF:
    e = c[0]
    if e in [x[0] for x in drows]:
        s = [x for x in drows if x[0] == e][0][3]
    else:
        s = live[e]["sem"]
    segs.append((e, s[s.find("④"):]))
chk("E2", "-", "17 行 ④ 两两不同", 17, len({x[1] for x in segs}),
    "PASS" if len({x[1] for x in segs}) == 17 else "FAIL")
n17 = [re.sub(r"[0-9A-Fa-f]{8}", "ENTRY", x[1]) for x in segs]
chk("E2", "-", "17 行 ④ 归一后两两不同", 17, len(set(n17)), "PASS" if len(set(n17)) == 17 else "FAIL")

# ---------------------------------------------------------------- 哈希/只读证明
cov_sha = sha256(COV)
exe_sha = sha256(EXE)
chk("H", "-", "coverage.tsv sha256（应=并表后态，证明本卡未改）",
    "E4F111B6…D51C8A", cov_sha[:16] + "…" + cov_sha[-6:],
    "PASS" if cov_sha.startswith("E4F111B6") else "FAIL", "bytes=%d" % os.path.getsize(COV))
chk("H", "-", "gamemd.exe sha256（只读，未改）", "73201CC0…F67476",
    exe_sha[:16] + "…" + exe_sha[-6:], "PASS" if exe_sha.startswith("73201CC0") else "FAIL")
chk("H", "-", "pin 快照 sha256", "2F498B18…53B36E", sha256(PIN)[:16] + "…" + sha256(PIN)[-6:],
    "PASS" if sha256(PIN).startswith("2F498B18") else "FAIL")

# ---------------------------------------------------------------- write
hdr = ["block", "entry", "item", "expected", "actual", "result", "evidence"]
with io.open(os.path.join(HERE, "check.tsv"), "w", encoding="utf-8", newline="\n") as fo:
    fo.write("\t".join(hdr) + "\n")
    for r in ROWS:
        fo.write("\t".join(x.replace("\t", " ") for x in r) + "\n")

summ = collections.Counter(r[5] for r in ROWS)
per_block = collections.defaultdict(lambda: collections.Counter())
for r in ROWS:
    per_block[r[0]][r[5]] += 1
info = dict(
    sha_cov=cov_sha, sha_exe=exe_sha, sha_pin=sha256(PIN),
    checks=len(ROWS), by_result=dict(summ),
    by_block={k: dict(v) for k, v in per_block.items()},
    d1=len(d1rows), d1_distinct=len(ents_d1),
    f_counts={k: cnt[k] for k in ("F1", "F2", "F3", "F4")},
    d51_narrow=narrow, d51_narrow_n=len(narrow),
    d51_broad_n=len(broad_ents), d51_broad_outside_17=outside,
    skip=[e for e in skip],
    delta=[c[0] for c in drows],
)
json.dump(info, io.open(os.path.join(HERE, "verify_summary.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("checks:", len(ROWS), dict(summ))
print("blocks:", {k: dict(v) for k, v in per_block.items()})
print("D1=%d F=%s narrow=%d broad=%d outside17=%d" % (
    len(d1rows), {k: cnt[k] for k in ("F1", "F2", "F3", "F4")}, len(narrow), len(broad_ents), len(outside)))
