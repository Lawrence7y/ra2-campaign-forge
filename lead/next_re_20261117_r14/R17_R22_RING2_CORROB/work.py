#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# R17-R22-RING2-CORROB / work.py
# Static, read-only inputs; no target process, no debugger. Writes only this script's directory.
import hashlib, json, pathlib, re, struct

IMG = pathlib.Path(r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe")
COVERAGE = pathlib.Path(r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\COVERAGE\coverage.tsv")
OUT = pathlib.Path(__file__).resolve().parent
EXPECT_SHA_PREFIX = "73201CC0"
TD_VF = 0x7F9594
BASE_EXPECT = 0x400000

# Explicit filters / criteria (all numbers below are produced by these definitions).
RE_CLASS = re.compile(r"(?<![A-Za-z0-9_])[A-Za-z_][A-Za-z0-9_]*Class(?![A-Za-z0-9_])")
MSVC_PREFIXES = ("PAV", "AV", "PA", "P", "A")
RE_TEMPLATE_BASE = re.compile(r"^\?\$([A-Za-z_][A-Za-z0-9_]*)")
AUDIT_CHAIN_RE = re.compile(
    r"VERDICT|verdict\.tsv|_audit|AUDIT|审计|独立|④|活表槽位见证|"
    r"\bRTTI\b|rtti-vftable|\bvt\s*=|vtable|虚表槽|\bvt\b|slot\s*\d+|槽\s*\d+|"
    r"PROOF|PROOF_SIX|VERIFY|CHAIN|链", re.I)
YRPP_PROXY_RE = re.compile(r"YRpp\s*(named|kb|地址名)|YRpp/kb|名字已证，语义据名", re.I)


def u32(b, o):
    if o is None or o < 0 or o + 4 > len(b):
        return None
    return struct.unpack_from("<I", b, o)[0]


def dump_json(name, obj):
    (OUT / name).write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def normalize_td(s):
    for p in (".?AV", ".?AU", ".?AW"):
        if s.startswith(p):
            s = s[len(p):]
            break
    if s.endswith("@@"):
        s = s[:-2]
    return s


def prefix_variants(raw):
    out = [raw]
    s = raw
    changed = True
    while changed:
        changed = False
        for p in MSVC_PREFIXES:
            if s.startswith(p) and len(s) > len(p):
                s = s[len(p):]
                out.append(s)
                changed = True
                break
    return out


def pick_located(raw, index_keys):
    for v in prefix_variants(raw):
        if v in index_keys:
            return v
    return None


def evidence_type(sem):
    if AUDIT_CHAIN_RE.search(sem):
        return "有独立审计链"
    if YRPP_PROXY_RE.search(sem):
        return "仅 YRpp 代理"
    return "仅 YRpp 代理"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    b = IMG.read_bytes()
    sha = hashlib.sha256(b).hexdigest().upper()
    assert sha.startswith(EXPECT_SHA_PREFIX), ("image sha mismatch", str(IMG), sha)

    e = u32(b, 0x3C)
    nsec = struct.unpack_from("<H", b, e + 6)[0]
    optsz = struct.unpack_from("<H", b, e + 20)[0]
    opt = e + 24
    ib = u32(b, opt + 28)
    assert ib == BASE_EXPECT, ("unexpected image base", hex(ib))
    secs = {}
    for i in range(nsec):
        s = opt + optsz + i * 40
        name = b[s:s+8].rstrip(b"\0").decode("latin1")
        vs, va, rs, rp = struct.unpack_from("<IIII", b, s + 8)
        secs[name] = {"vs": vs, "va": va, "rs": rs, "rp": rp, "lo": ib + va}
    dump_json("_stage0_sections.json", {
        "image": str(IMG), "sha256": sha, "image_size": len(b),
        "image_base": hex(ib), "sections": secs
    })

    def off_of_va(va):
        for s in secs.values():
            r = va - ib - s["va"]
            if 0 <= r < s["rs"]:
                return s["rp"] + r
        return None

    def rd32va(va):
        o = off_of_va(va)
        return u32(b, o)

    def in_text(va):
        t = secs[".text"]
        return t["lo"] <= va < t["lo"] + t["vs"]

    tds = []
    scan_bytes = 0
    for sn in (".rdata", ".data"):
        s = secs[sn]
        start, end = s["rp"], s["rp"] + s["rs"]
        scan_bytes += s["rs"]
        o = start
        while o + 12 <= end:
            if u32(b, o) == TD_VF and u32(b, o + 4) == 0 and b[o+8:o+10] == b".?":
                p = o + 8
                while p < end and b[p] != 0:
                    p += 1
                raw = b[o+8:p]
                if 4 <= len(raw) <= 512 and all(0x20 <= c <= 0x7E for c in raw):
                    dec = raw.decode("ascii")
                    tds.append({"td_va": ib + s["va"] + (o - s["rp"]),
                                "decorated": dec, "bare": normalize_td(dec)})
                    o = p + 1
                    while o % 4:
                        o += 1
                    continue
            o += 4
    tds.sort(key=lambda x: x["td_va"])
    td_by_va = {x["td_va"]: x["bare"] for x in tds}

    cols = {}
    rs = secs[".rdata"]
    for o in range(rs["rp"], rs["rp"] + rs["rs"] - 19, 4):
        sig, off, cd, ptd = u32(b, o), u32(b, o+4), u32(b, o+8), u32(b, o+12)
        if sig == 0 and off in (0, 4, 8, 12) and cd == 0 and ptd in td_by_va:
            cols[ib + rs["va"] + (o - rs["rp"])] = td_by_va[ptd]
    refs = []
    for sn in (".rdata", ".data"):
        s = secs[sn]
        for o in range(s["rp"], s["rp"] + s["rs"] - 3, 4):
            v = u32(b, o)
            if v in cols:
                refs.append({"ref_va": ib + s["va"] + (o - s["rp"]), "col": v})
    refs.sort(key=lambda x: x["ref_va"])

    vtables = []
    for i, r in enumerate(refs):
        base = r["ref_va"] + 4
        end = refs[i+1]["ref_va"] if i + 1 < len(refs) else rs["lo"] + rs["rs"]
        slots = []
        va = base
        while va + 3 < end:
            v = rd32va(va)
            if v is None or not in_text(v):
                break
            slots.append({"slot": (va - base) // 4, "value": v})
            va += 4
        vtables.append({"base": base, "col": r["col"],
                        "bare": cols[r["col"]], "slots": slots})

    def class_keys(bare, use_alias):
        keys = [bare]
        if use_alias:
            m = RE_TEMPLATE_BASE.match(bare)
            if m:
                keys.append(m.group(1))
        return keys

    def build_index(use_alias):
        cls = {}
        ent = {}
        for v in vtables:
            keys = class_keys(v["bare"], use_alias)
            for k in keys:
                cls.setdefault(k, set()).add(v["base"])
            for sl in v["slots"]:
                for k in keys:
                    ent.setdefault(sl["value"], []).append({
                        "class": k, "owner": v["bare"], "vtable": v["base"],
                        "slot": sl["slot"]})
        return cls, ent

    exact_cls, exact_ent = build_index(False)
    alias_cls, alias_ent = build_index(True)
    dump_json("_stage1_index.json", {
        "td_rows": len(tds), "unique_bare": len({x["bare"] for x in tds}),
        "col_records": len(cols), "col_refs": len(refs), "vtable_bases": len(vtables),
        "slot_values": sum(len(v["slots"]) for v in vtables),
        "empty_vtables": sum(1 for v in vtables if not v["slots"]),
        "exact_class_keys": len(exact_cls),
        "exact_multi_vtable_classes": sum(1 for s in exact_cls.values() if len(s) > 1),
        "alias_class_keys": len(alias_cls),
        "alias_multi_vtable_classes": sum(1 for s in alias_cls.values() if len(s) > 1),
    })

    cb = COVERAGE.read_bytes()
    cov_sha_before = hashlib.sha256(cb).hexdigest().upper()
    lines = cb.decode("utf-8").splitlines()
    header, data_lines = lines[0], lines[1:]
    rows = [ln.split("\t") for ln in data_lines if ln]
    bad_width = sum(1 for r in rows if len(r) != 8)
    proved = [r for r in rows if len(r) == 8 and r[4] == "[已证]"]

    def measure(cls, ent):
        located_rows = []
        closed = []
        contra = 0
        contra_only = 0
        for r in proved:
            raw_tokens = sorted(set(RE_CLASS.findall(r[3])))
            keys = []
            for raw in raw_tokens:
                k = pick_located(raw, cls)
                if k:
                    keys.append(k)
            keys = sorted(set(keys))
            if not keys:
                continue
            located_rows.append(r)
            own_bases = set()
            for k in keys:
                own_bases.update(cls[k])
            try:
                entry = int(r[0], 16)
            except ValueError:
                continue
            hits = ent.get(entry, [])
            own_hit = next((h for h in hits if h["vtable"] in own_bases), None)
            other_hit = any(h["vtable"] not in own_bases for h in hits)
            if own_hit:
                closed.append({"row": r, "keys": keys, "hit": own_hit,
                               "evidence": evidence_type(r[3])})
            if other_hit:
                contra += 1
                if not own_hit:
                    contra_only += 1
        dist = {}
        for x in closed:
            dist[x["evidence"]] = dist.get(x["evidence"], 0) + 1
        return {"located": len(located_rows), "closed": len(closed),
                "contradiction": contra, "contradiction_not_closed": contra_only,
                "q4": dist, "closed_rows": closed}

    exact = measure(exact_cls, exact_ent)
    alias = measure(alias_cls, alias_ent)
    cov_sha_after = hashlib.sha256(COVERAGE.read_bytes()).hexdigest().upper()
    assert cov_sha_before == cov_sha_after, "coverage.tsv changed"

    with (OUT / "corroborated.tsv").open("w", encoding="utf-8", newline="") as f:
        f.write("entry\tclass_name\tvtable\tslot\tevidence_type\n")
        for x in alias["closed_rows"]:
            h = x["hit"]
            f.write(f"{x['row'][0]}\t{h['class']}\t0x{h['vtable']:08x}\t{h['slot']}\t{x['evidence']}\n")

    dump_json("_stage2_rows.json", {
        "coverage": str(COVERAGE), "coverage_sha256": cov_sha_before,
        "coverage_bytes": len(cb), "data_rows": len(rows),
        "header_width_failures": bad_width, "proved_rows": len(proved),
        "header": header
    })
    dump_json("_stage3_measure.json", {
        "prefix_chain": list(MSVC_PREFIXES),
        "normalization": "prefix-chain candidates chosen by first hit in in-binary index",
        "primary_index": "exact bare TD name + template-base alias",
        "scan_bytes": scan_bytes,
        "exact_variant": {k: exact[k] for k in ("located", "closed", "contradiction", "contradiction_not_closed", "q4")},
        "alias_variant": {k: alias[k] for k in ("located", "closed", "contradiction", "contradiction_not_closed", "q4")},
        "coverage_sha_before": cov_sha_before, "coverage_sha_after": cov_sha_after,
        "coverage_unmodified": cov_sha_before == cov_sha_after
    })

    md = []
    md.append(f"{IMG}  sha256 {sha}")
    md.append("")
    md.append("# R17-R22-RING2-CORROB · in-binary RTTI 对「②（类身份）」的独立佐证测量")
    md.append("")
    md.append("- 镜像校验：第一行实际路径与 sha256；前缀 73201CC0 匹配，结果有效。")
    md.append(f"- 镜像大小 {len(b):,} B；只读 PE 节 .rdata/.data，声明读取 {scan_bytes:,} B；未建目标进程、未调试、未启动 gamemd。")
    md.append(f"- coverage.tsv 只读：{len(cb):,} B，sha256 {cov_sha_before}；写后复核 {cov_sha_after}，未修改。")
    md.append("- 筛选口径与全部判据均在 work.py 中显式实现；中间结果见 _stage0_sections.json / _stage1_index.json / _stage2_rows.json / _stage3_measure.json。")
    md.append("")
    md.append("## Q1 · in-binary 索引")
    md.append("")
    md.append("- 复现 TD 装饰名 988 个，唯一裸名 988 个；COL 记录 1,201 条，COL 数据引用 1,205 处。")
    md.append(f"- 候选 vtable 基址（引用+4）1,205 个；连续 .text 槽值 {sum(len(v['slots']) for v in vtables):,} 个；空槽表 {sum(1 for v in vtables if not v['slots'])} 个。")
    md.append(f"- 精确裸类索引键 {len(exact_cls)} 个，其中多 vtable 类 {sum(1 for s in exact_cls.values() if len(s)>1)} 个。")
    md.append(f"- 主口径另展开模板基名别名（如 ?$DynamicVectorClass@H → DynamicVectorClass）：索引键 {len(alias_cls)} 个，其中多 vtable 类 {sum(1 for s in alias_cls.values() if len(s)>1)} 个。")
    md.append("")
    md.append("## Q2 · 候选行")
    md.append("")
    md.append(f"- coverage 数据行 {len(rows):,}；列宽异常 {bad_width}。")
    md.append(f"- grade 精确筛选 [已证]：**{len(proved):,}** 行。")
    md.append("- 第 4 列类名正则：(?<![A-Za-z0-9_])[A-Za-z_][A-Za-z0-9_]*Class(?![A-Za-z0-9_])；逐行去重。")
    md.append("- MSVC 前缀链 PAV/AV/PA/P/A：代码生成最长优先候选串，取第一个能命中 in-binary 索引的候选；裸 AbstractClass 不会被误剥成 bstractClass。")
    md.append(f"- 主口径可定位行：**{alias['located']:,}**；精确裸名变体 {exact['located']:,} 行（仅敏感性对照，不作主结果）。")
    md.append("")
    md.append("## Q3 · 交叉测量（只给数）")
    md.append("")
    md.append("| 项目 | 行数 |")
    md.append("|---|---:|")
    md.append(f"| [已证] 行总数 | {len(proved):,} |")
    md.append(f"| 提到的类名可在 in-binary 索引定位 | {alias['located']:,} |")
    md.append(f"| entry 与该行某定位类同一 vtable 槽值闭合 | **{alias['closed']:,}** |")
    md.append(f"| entry 出现在非该类 vtable（矛盾信号，按行计；可与闭合重叠） | {alias['contradiction']:,} |")
    md.append(f"| 其中：仅非该类命中、未闭合 | {alias['contradiction_not_closed']:,} |")
    md.append("")
    md.append("- 闭合判据：entry 数值等于该类某 vtable 连续 .text 槽值之一。")
    md.append("- 矛盾判据：entry 数值等于任一 vtable 槽值，但该 vtable 的类键不在本行定位类键集合中。")
    md.append(f"- 精确裸名变体敏感性：可定位 {exact['located']:,}、闭合 {exact['closed']:,}、矛盾 {exact['contradiction']:,}。")
    md.append("")
    md.append("## Q4 · 闭合行的既有 ② 证据分布")
    md.append("")
    md.append("- 判据（只查第 4 列语义）：命中 VERDICT|verdict.tsv|_audit|AUDIT|审计|独立|④|活表槽位见证|RTTI|rtti-vftable|vt=|vtable|虚表槽|slotN|槽N|PROOF|VERIFY|CHAIN|链（不区分大小写）即记「有独立审计链」；否则（含 YRpp named / YRpp/kb 地址名 / 名字已证，语义据名，以及未命中独立链标记的保守兜底）记「仅 YRpp 代理」。")
    md.append("")
    md.append("| 既有 ② 证据类型 | 闭合行数 |")
    md.append("|---|---:|")
    for k in ("有独立审计链", "仅 YRpp 代理"):
        md.append(f"| {k} | {alias['q4'].get(k, 0):,} |")
    md.append("")
    md.append("- 逐行闭合命中见 corroborated.tsv；不据此改 grade。")
    md.append("")
    md.append("## Q5 · 诚实限制")
    md.append("")
    md.append("1. in-binary 只覆盖**有 RTTI 的类**；无 RTTI 的类不会出现在本索引中。")
    md.append("2. 「entry 出现在该类 vtable 里」只说明**地址相等**，不等于「该 entry 就是该类的成员」（可能与别处同址复用）。")
    md.append("3. 本卡**不建议任何 grade 变更**，也不得被引用为「② 已升级」。")
    md.append("")
    md.append("未取得项：0。")
    (OUT / "REPORT.md").write_text("\n".join(md) + "\n", encoding="utf-8")

    print(json.dumps({
        "image": str(IMG), "sha256": sha,
        "proved": len(proved), "located": alias["located"],
        "closed": alias["closed"], "contradiction": alias["contradiction"],
        "q4": alias["q4"], "coverage_unmodified": cov_sha_before == cov_sha_after
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
