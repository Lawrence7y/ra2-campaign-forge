#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""R16-AUDIT-D1-WIDE-B4 / 项 D（文本与事实一致，含 §12.6 指针）+ 项 E（反抄袭）"""
import os, io, re, json, hashlib, collections, itertools
HERE = os.path.dirname(os.path.abspath(__file__))
R14 = os.path.dirname(HERE)
B4 = os.path.join(R14, "R16_D1_WIDE_B4")

def load(p):
    t = io.open(p, encoding="utf-8-sig", newline="").read()
    lines = t.split("\n")
    if lines and lines[-1] == "":
        lines = lines[:-1]
    hdr = lines[0].split("\t")
    return hdr, [dict(zip(hdr, l.split("\t"))) for l in lines[1:] if l.strip()]

DH, DROWS = load(os.path.join(B4, "delta.tsv"))
FH, FROWS = load(os.path.join(B4, "fields.tsv"))
facts = {r["entry"]: r for r in json.load(io.open(os.path.join(HERE, "_facts.json"), encoding="utf-8"))["rows"]}
bc = {r["entry"]: r for r in json.load(io.open(os.path.join(HERE, "_bc.json"), encoding="utf-8"))["rows"]}

PAT = re.compile(
    r"④ 活表槽位见证：(?P<label1>[^（]+)（vt=(?P<vt>[0-9A-Fa-f]{8})，槽 (?P<slot>\d+) 值=(?P<val>[0-9A-Fa-f]{8})，"
    r"COL=(?P<col>[0-9A-Fa-f]{8}) offset=(?P<off>\d+)，RTTI=(?P<td>[0-9A-Fa-f]{8})→(?P<mangled>\.\?A[^；]*?)；"
    r"装表点 (?P<site>[0-9A-Fa-f]{8}) 位于 (?P<host>[0-9A-Fa-f]{8}) 体内，装配方式=(?P<form>\w+)"
    r"（(?P<formdesc>[^；]*?)；实测指令 (?P<ins>[^）]*?)），entry 体外）"
    r" ④升级句：(?P<label2>[^（]+)（④ 表属类与行名类一致，均为 (?P<cls>[^；]+)；该槽即其 vt=(?P<vt2>[0-9A-Fa-f]{8}) 表 slot(?P<slot2>\d+)，无归属歧义）"
    r"(?P<disc>（D-47\(A\)[^）]*）)")

RESULTS = []
CORE = []
for d in DROWS:
    e = d["entry"]; c4 = d["one_line_semantics"]; fx = facts[e]; b = bc[e]
    r = dict(entry=e, name=d["name"], status=fx["status"], findings=[], d_ok=True)
    m = PAT.search(c4)
    r["regex_matched"] = bool(m)
    if not m:
        r["d_ok"] = False
        r["findings"].append("④ 骨架正则不匹配（结构不符）")
        RESULTS.append(r); continue
    g = m.groupdict()
    rowcls = d["name"].split("::")[0]
    site_cls = b["site_cls"]
    # 1 vt / slot / 槽值 / COL / offset / TD / mangled
    checks = [
        ("vt", g["vt"].upper(), b["vt"].upper()),
        ("slot", g["slot"], str(b["slot"])),
        ("槽值==entry", g["val"].upper(), e.upper()),
        ("COL", g["col"].upper(), b["b"]["col"].upper()),
        ("offset", g["off"], str(b["b"]["offset"])),
        ("TD", g["td"].upper(), (b["b"]["td"] or "").upper()),
        ("mangled", g["mangled"], b["b"]["mangled"] or ""),
        ("装表点", g["site"].upper(), b["site"].upper()),
        ("宿主", g["host"].upper(), (site_cls or {}).get("host") or ""),
        ("装配方式", g["form"], b.get("form_audit") or ""),
        ("实测指令", g["ins"], (site_cls or {}).get("ins") or ""),
        ("label1", g["label1"], "%s::slot%d" % (rowcls, b["slot"])),
        ("label2", g["label2"], "%s::slot%d" % (rowcls, b["slot"])),
        ("类名", g["cls"], rowcls),
        ("vt2", g["vt2"].upper(), b["vt"].upper()),
        ("slot2", g["slot2"], str(b["slot"])),
    ]
    for nm, got, exp in checks:
        if (got or "").strip() != (exp or "").strip():
            r["d_ok"] = False
            r["findings"].append("%s 不符: 文本=%r 事实=%r" % (nm, got, exp))
    # 2 RTTI 类严格等于行名类
    if not b["rowclass_strict_eq"]:
        r["d_ok"] = False
        r["findings"].append("RTTI 类与行名类不严格相等: %s vs %s" % (b["b"]["mangled"], rowcls))
    # 3 装配方式描述与形态一致（描述性短语）
    desc_expect = {"ctor_body": "构造器体内 mov [reg], vt（写 this，宿主真构造器/工厂、无删除签名）",
                   "mov_abs": "mov [绝对地址], vt（绝对地址在 .data）",
                   "reg": "非构造器的寄存器形态（写 this 但宿主为析构器，非构造器/工厂）"}
    want = desc_expect.get(g["form"])
    if want and g["formdesc"].strip() != want:
        r["d_ok"] = False
        r["findings"].append("形态描述与枚举不符: %r" % g["formdesc"])
    # 4 entry 体外
    if not b["b"]["b5"]:
        r["d_ok"] = False
        r["findings"].append("装表点未在 entry 体外")
    # 5 [已证] 之外的 grade 未变（A 项已有，此处仅在文本层面记录）
    # 6 披露指针
    disc = g["disc"]
    r["disc"] = disc
    if "§12.6" not in disc:
        r["d_ok"] = False; r["findings"].append("披露指针未指向 §12.6")
    if "PANEL" not in disc:
        r["d_ok"] = False; r["findings"].append("披露缺 PANEL 对应披露")
    if "D-47(A)" not in disc:
        r["d_ok"] = False; r["findings"].append("披露缺 D-47(A) 条款")
    if "§12.3 对该形态让位" not in disc:
        r["d_ok"] = False; r["findings"].append("披露缺 §12.3 让步子句")
    if "已过 §12.3" in c4 or "已过§12.3" in c4:
        r["d_ok"] = False; r["findings"].append("违规措辞「已过 §12.3」")
    if "§12.4" in c4:
        r["d_ok"] = False; r["findings"].append("误引 §12.4")
    # 7 mov_abs 必须写明绝对地址在 .data
    if g["form"] == "mov_abs" and not site_cls["abs_in_data"]:
        r["d_ok"] = False; r["findings"].append("mov_abs 目标不在 .data")
    # 8 reg 行「宿主为析构器」需有依据
    if g["form"] == "reg":
        hk = site_cls["host_kind"]["kind"]
        r["reg_justified_by"] = hk
        if not hk.startswith(("scalar_deleting_dtor", "base_dtor", "dtor_like")):
            r["d_ok"] = False; r["findings"].append("reg 标注但宿主非析构器: %s" % hk)
    # 9 ctor_body 宿主需真构造器 + 写 this@disp0
    if g["form"] == "ctor_body":
        hk = site_cls["host_kind"]["kind"]
        r["ctor_justified_by"] = hk
        tr = site_cls.get("this") or {}
        if not hk.startswith("ctor"):
            r["d_ok"] = False; r["findings"].append("ctor_body 宿主非真构造器: %s" % hk)
        if tr.get("kind") != "this" or (tr.get("offset") or 0) != 0:
            r["d_ok"] = False; r["findings"].append("ctor_body 目标非 this@disp0: %s" % tr)
    # 10 fields.tsv 行与独立复算一致
    fr = [x for x in FROWS if x["entry"] == e][0]
    fl_checks = [("fields.vt", fr["vt"].upper(), b["vt"].upper()),
                 ("fields.slot", fr["slot"], str(b["slot"])),
                 ("fields.install_site", fr["install_site"].upper(), b["site"].upper()),
                 ("fields.install_host", fr["install_host"].upper(), (site_cls or {}).get("host") or ""),
                 ("fields.install_form", fr["install_form(ctor_body|mov_abs|reg|other)"], g["form"]),
                 ("fields.pre_has_ring4", fr["pre_has_ring4(是/否)"], "否")]
    for nm, got, exp in fl_checks:
        if (got or "").strip() != (exp or "").strip():
            r["d_ok"] = False; r["findings"].append("%s 与复算不符: %r vs %r" % (nm, got, exp))
    # 追加：entry 体外/函数≠entry
    r["site_outside_entry"] = b["b"]["b5"]
    r["host_ne_entry"] = b["b"]["host_ne_entry"]
    RESULTS.append(r)

# ---------------- 项 E：反抄袭（只看追加的 ④ 段，不看原 one_line_semantics） ----------------
segs = []
for d in DROWS:
    mm = PAT.search(d["one_line_semantics"])
    segs.append(mm.group(0) if mm else "")
def norm_hex(s): return re.sub(r"[0-9A-Fa-f]{8}", "HEX", s)
def norm_slot(s):
    s = norm_hex(s)
    s = re.sub(r"slot\s*\d+", "SLOT", s)
    return re.sub(r"槽\s*\d+", "SLOT", s)

full_distinct = len(set(segs)) == len(segs)
norm_distinct = len(set(norm_hex(x) for x in segs)) == len(segs)
slot_norm = [norm_slot(x) for x in segs]
groups = collections.defaultdict(list)
for d, s in zip(DROWS, slot_norm):
    groups[s].append(d["entry"])

# 与盘上既有 ④ 段的逐字重复：读 coverage.tsv 里已含 ④ 的行（排 B4 自己）
COV = os.path.join(R14, "COVERAGE", "coverage.tsv")
cov_lines = io.open(COV, encoding="utf-8", newline="").read().split("\n")
b4set = set(d["entry"] for d in DROWS)
existing = []
for ln in cov_lines[1:]:
    p = ln.split("\t")
    if len(p) >= 8 and "④ 活表槽位见证" in p[3] and p[0] not in b4set:
        existing.append((p[0], p[3]))
dup = []
for d, mine in zip(DROWS, segs):
    if not mine:
        continue
    for (en, c4) in existing:
        if mine in c4:
            dup.append((d["entry"], en, "整段 ④ 逐字重复"))
            break
        # 见证核心句（到「entry 体外）」为止）逐字比对
        core_sent = mine.split(" ④升级句：")[0]
        if core_sent and core_sent in c4:
            dup.append((d["entry"], en, "见证核心句逐字重复"))
            break
# witness-core 碰撞：同 class/vt/slot/site
core = collections.defaultdict(list)
for d in DROWS:
    b = bc[d["entry"]]
    key = (d["name"].split("::")[0], b["vt"], b["slot"], b["site"])
    core[key].append(d["entry"])
# 同 class/vt/site（不看 slot）——事实同源而非抄袭
core_noslot = collections.defaultdict(list)
for d in DROWS:
    b = bc[d["entry"]]
    key = (d["name"].split("::")[0], b["vt"], b["site"])
    core_noslot[key].append(d["entry"])

E = dict(full_distinct=full_distinct, n_full=len(segs),
         norm_hex_distinct=norm_distinct,
         slot_normalized_groups={("%s" % k[:70]): v for k, v in groups.items() if len(v) > 1},
         n_slot_normalized_distinct=len(groups),
         verbatim_dup_with_existing=dup,
         n_existing_ring4_rows=len(existing),
         witness_core_collisions={str(k): v for k, v in core.items() if len(v) > 1},
         witness_core_noslot_groups={str(k): v for k, v in core_noslot.items() if len(v) > 1})

D_n_bad = sum(0 if r["d_ok"] else 1 for r in RESULTS)
out = dict(d_rows=RESULTS, d_bad_rows=[r["entry"] for r in RESULTS if not r["d_ok"]],
           n_d_bad=D_n_bad, E=E)
json.dump(out, io.open(os.path.join(HERE, "_d_e.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

print("=== D: 逐行 ===")
for r in RESULTS:
    print("%s  D=%s  form=%s  regex=%s  %s" % (
        r["entry"], "OK" if r["d_ok"] else "FAIL", (PAT.search([d for d in DROWS if d['entry']==r['entry']][0]['one_line_semantics']).group('form') if PAT.search([d for d in DROWS if d['entry']==r['entry']][0]['one_line_semantics']) else "?"),
        r["regex_matched"], ("; ".join(r["findings"]) if r["findings"] else "")))
print("\nD 不合格行数 =", D_n_bad)
print("\n=== E ===")
print(json.dumps(E, ensure_ascii=False, indent=1))
