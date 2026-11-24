#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# R17_R20_RECON / work.py
# Pure static + in-table reconciliation. Read-only inputs; no process creation/debugging/launch.
# Writes only files in this script directory.
import hashlib, json, pathlib, re, struct

IMG = pathlib.Path(r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe")
COVERAGE = pathlib.Path(r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\COVERAGE\coverage.tsv")
OUT = pathlib.Path(__file__).resolve().parent
EXPECT_PREFIX = "73201CC0"
TD_VF = 0x7F9594
RE_CLASS = re.compile(r"(?<![A-Za-z0-9_])[A-Za-z_][A-Za-z0-9_]*Class(?![A-Za-z0-9_])")
CAT = {
    "a": "(a) 无独立 vtable 的类",
    "b": "(b) 多重继承或嵌套导致的复合名片段",
    "c": "(c) 模板类",
    "d": "(d) 疑似命名差异/拼写差异",
    "e": "(e) 其它/无法判定",
}
STATIC_LIKE = {"RulesClass", "ScenarioClass", "InputManagerClass", "CDDriveManagerClass", "GameOptionsClass", "ZBufferClass"}
SAMPLES = [
    "AircraftClass", "FileClass", "AVAircraftClass", "AVFootClass", "AVTechnoClass", "PAVBombClass", "PAVInfantryClass", "AVWWMouseClass", "VAircraftTypeClass", "VNeuronClass",
    "PAVAbstractClass", "RTacticalClass_RadarClass", "INIEntry_INIClass", "SelectClass_StripClass_SidebarClass", "TacticalClass_DisplayClass", "SBGadgetClass_SidebarClass", "INISection_INIClass", "DynamicVectorClass", "VectorClass", "AVCDFileClass",
]

def u16(b, o): return struct.unpack_from("<H", b, o)[0]
def u32(b, o): return struct.unpack_from("<I", b, o)[0]
def clean(s): return re.sub(r"\s+", " ", str(s).replace("\t", " ").replace("\r", " ").replace("\n", " ")).strip()
def pct(a, b): return f"{100.0 * a / b:.2f}%"

def candidate_keys(token):
    seeds = [token]
    if token.startswith("?"):
        seeds.append(token[1:])
    prefix = []
    for s in list(seeds):
        for n in range(1, min(4, len(s)) + 1):
            p = s[:n]
            if p and all(c in "PAV" for c in p):
                prefix.append(s[n:])
    segments = []
    for s in seeds + prefix:
        segments.extend(p for p in s.split("_") if p)
    ordered, seen = [], set()
    for x in seeds + prefix + segments:
        k = x.lower()
        if k not in seen:
            seen.add(k)
            ordered.append(x)
    return ordered

def write_tsv(name, header, rows):
    with (OUT / name).open("w", encoding="utf-8", newline="") as f:
        f.write("\t".join(header) + "\n")
        for row in rows:
            f.write("\t".join(clean(x) for x in row) + "\n")

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    b = IMG.read_bytes()
    sha = hashlib.sha256(b).hexdigest().upper()
    if not sha.startswith(EXPECT_PREFIX):
        raise SystemExit(f"image sha mismatch: {sha}")
    pe = u32(b, 0x3C)
    nsec, optsz = u16(b, pe + 6), u16(b, pe + 20)
    opt = pe + 24
    image_base = u32(b, opt + 28)
    secs = {}
    for i in range(nsec):
        s = opt + optsz + i * 40
        name = b[s:s+8].rstrip(b"\0").decode("latin1")
        vs, va, rs, rp = struct.unpack_from("<IIII", b, s + 8)
        secs[name] = {"name": name, "vs": vs, "va": va, "rs": rs, "rp": rp, "lo": image_base + va}
    scan = [secs[".rdata"], secs[".data"]]
    scan_bytes = sum(s["rs"] for s in scan)

    rtti, prefix_counts = [], {}
    for sec in scan:
        start, end = sec["rp"], sec["rp"] + sec["rs"]
        o = start
        while o + 12 <= end:
            if u32(b, o) == TD_VF and u32(b, o + 4) == 0 and b[o+8:o+10] == b".?":
                p = o + 8
                while p < end and b[p] != 0:
                    p += 1
                raw = b[o+8:p]
                if 4 <= len(raw) <= 512 and all(0x20 <= c <= 0x7E for c in raw):
                    dec = raw.decode("ascii")
                    pfx = ".?AV" if dec.startswith(".?AV") else ".?AU" if dec.startswith(".?AU") else ".?AW" if dec.startswith(".?AW") else "other"
                    if pfx != "other":
                        bare = dec[4:]
                        if bare.endswith("@@"):
                            bare = bare[:-2]
                        extra = bare[2:].split("@", 1)[0] if bare.startswith("?$") and "@" in bare else ""
                        prefix_counts[pfx] = prefix_counts.get(pfx, 0) + 1
                        rtti.append({"decorated": dec, "bare": bare, "prefix": pfx, "tdVA": sec["lo"] + (o - sec["rp"]), "extra": extra, "section": sec["name"], "fileOff": o})
                        o = p + 1
                        while o % 4:
                            o += 1
                        continue
            o += 4
    rtti.sort(key=lambda e: e["tdVA"])
    exact, tmpl = {}, {}
    for e in rtti:
        exact.setdefault(e["bare"].lower(), []).append(e)
        if e["extra"]:
            tmpl.setdefault(e["extra"].lower(), []).append(e)

    cb = COVERAGE.read_bytes()
    cov_sha_before = hashlib.sha256(cb).hexdigest().upper()
    lines = cb.decode("utf-8").splitlines()
    counts, ctxs = {}, {}
    rows_with = raw_occ = bad_width = 0
    for i, line in enumerate(lines[1:], 2):
        cols = line.split("\t")
        if len(cols) != 8:
            bad_width += 1
        sem = cols[3] if len(cols) > 3 else ""
        all_toks = RE_CLASS.findall(sem)
        raw_occ += len(all_toks)
        toks = list(dict.fromkeys(all_toks))
        if toks:
            rows_with += 1
        for t in toks:
            counts[t] = counts.get(t, 0) + 1
            ctxs.setdefault(t, [])
            if len(ctxs[t]) < 3:
                ctxs[t].append({"line": i, "entry": cols[0], "sub": cols[1], "name": cols[2], "sem": sem})
    cov_names = sorted(counts, key=lambda n: (-counts[n], n))

    def resolve(token):
        cands = candidate_keys(token)
        base = [token] + ([token[1:]] if token.startswith("?") else [])
        prefixes = []
        for s in base:
            for n in range(1, min(4, len(s)) + 1):
                if s[:n] and all(c in "PAV" for c in s[:n]):
                    prefixes.append(s[n:])
        segments = [p for s in base + prefixes for p in s.split("_") if p]
        ordered = []
        for arr, kind in ((base, "exact"), (prefixes, "msvc_prefix"), (segments, "underscore")):
            for x in arr:
                if not any(o["k"] == x.lower() for o in ordered):
                    ordered.append({"x": x, "k": x.lower(), "kind": kind})
        for o in ordered:
            if o["k"] in exact:
                mech = ("exact" if o["x"] == token else "leading_q") if o["kind"] == "exact" else o["kind"]
                return {"token": token, "normalized": o["x"], "hit": exact[o["k"]][0]["bare"], "mechanism": mech, "candidates": cands}
        for o in ordered:
            if o["k"] in tmpl:
                return {"token": token, "normalized": o["x"], "hit": tmpl[o["k"]][0]["bare"], "mechanism": "template_base", "templateMatches": tmpl[o["k"]], "candidates": cands}
        return None

    resolutions = {n: resolve(n) for n in cov_names}
    resolutions = {k: v for k, v in resolutions.items() if v}
    unresolved = [n for n in cov_names if n not in resolutions]
    old_cov_only = [n for n in cov_names if n.lower() not in exact]
    mech_counts = {}
    for r in resolutions.values():
        mech_counts[r["mechanism"]] = mech_counts.get(r["mechanism"], 0) + 1

    cov_keys = {c.lower() for n in cov_names for c in candidate_keys(n)}
    covered = [e for e in rtti if e["bare"].lower() in cov_keys or (e["extra"] and e["extra"].lower() in cov_keys)]
    direct = [e for e in rtti if e["bare"].lower() in cov_keys]
    base_cov = [e for e in rtti if e["extra"] and e["extra"].lower() in cov_keys]
    rtti_only = [e for e in rtti if e["bare"].lower() not in cov_keys and not (e["extra"] and e["extra"].lower() in cov_keys)]

    def uniq(es):
        seen, out = set(), []
        for e in es:
            key = (e["tdVA"], e["bare"])
            if key not in seen:
                seen.add(key)
                out.append(e)
        return out

    def find_nested(cands):
        out = []
        for c in cands:
            for e in rtti:
                if e["bare"].lower().startswith(c.lower() + "@"):
                    out.append(e)
        return uniq(out)

    def find_template_arg(cands):
        out = []
        for c in cands:
            for e in rtti:
                if e["bare"].startswith("?$") and c.lower() in e["bare"].lower():
                    out.append(e)
        return uniq(out)

    def find_alt(context_list):
        rx = re.compile(r"RTTI=([0-9A-Fa-f]{6,8})→\.\?A[UV]([A-Za-z0-9_?@$]+?)@@")
        for x in context_list:
            m = rx.search(x["sem"])
            if m and m.group(2).lower() in exact:
                return exact[m.group(2).lower()][0]
        return None

    def classify(name):
        cs = ctxs.get(name, [])
        cands = candidate_keys(name)
        first = cs[0] if cs else {"line": 0, "entry": "", "name": ""}
        loc = f"coverage L{first['line']} entry={first['entry']} name={first['name']}"
        nohit = f"候选键 {'|'.join(cands)} 与 in-binary RTTI 裸名/模板首段基名均无大小写不敏感等号命中"
        nested = find_nested(cands)
        if nested:
            ev = "、".join(f"{e['bare']}@TD 0x{e['tdVA']:x}" for e in nested[:2])
            return CAT["b"], f"{loc}；{nohit}；RTTI 存在嵌套复合形态 {ev}，token 是其首段/前缀后片段"
        tms = find_template_arg(cands)
        if tms:
            ev = "、".join(f"{e['bare']} @0x{e['tdVA']:x}" for e in tms[:2])
            return CAT["c"], f"{loc}；{nohit}；仅见模板名实参内出现，TD {ev}"
        alt = find_alt(cs)
        if alt:
            return CAT["d"], f"{loc}；{nohit}；coverage 上下文活表见证写有 .?A[UV]{alt['bare']}@@，对应 TD 0x{alt['tdVA']:x}；仅标疑似"
        if name in STATIC_LIKE:
            return CAT["a"], f"{loc}；{nohit}；扫描节内无同名 TD，coverage 上下文为管理/静态/命名空间式入口且无 vt 槽见证；据此归为无独立 vtable 类"
        return CAT["e"], f"{loc}；{nohit}；无模板实参/嵌套/替代 RTTI 名的表内证据，无法判定"

    unresolved_rows = [(n, counts[n], *classify(n)) for n in unresolved]
    cat_dist = {}
    for _, _, cat, _ in unresolved_rows:
        cat_dist[cat] = cat_dist.get(cat, 0) + 1
    sample_rows = []
    for n in SAMPLES:
        r = resolutions[n]
        if r["mechanism"] == "exact":
            why = "原 token 已是 in-binary 裸名，未做扩展"
        elif r["mechanism"] == "template_base":
            why = f"首段基名命中模板实例 {r['templateMatches'][0]['bare']}"
        elif r["mechanism"] == "underscore":
            why = "下划线复合名取段，段本身是完整裸名"
        else:
            why = "仅去 P/A/V 前缀链后即与完整裸名相等"
        sample_rows.append((n, r["normalized"], r["hit"], f"是（{r['mechanism']}）：{why}"))

    (OUT / "_stage0_sections.json").write_text(json.dumps({"image": str(IMG), "sha256": sha, "size": len(b), "imageBase": hex(image_base), "sections": secs, "scan": [{"name": s["name"], "raw": hex(s["rp"]), "len": s["rs"], "va": hex(s["lo"])} for s in scan], "scanBytes": scan_bytes}, ensure_ascii=False, indent=2), encoding="utf-8")
    (OUT / "_stage1_rtti.json").write_text(json.dumps({"decoratedNames": len(rtti), "uniqueDecorated": len({e["decorated"] for e in rtti}), "prefixCounts": prefix_counts, "uniqueBare": len(exact), "templateInstances": sum(1 for e in rtti if e["extra"]), "distinctTemplateBaseKeys": len(tmpl), "first": rtti[0], "last": rtti[-1]}, ensure_ascii=False, indent=2), encoding="utf-8")
    (OUT / "_stage2_coverage.json").write_text(json.dumps({"coverage": str(COVERAGE), "sha256": cov_sha_before, "bytes": len(cb), "dataRows": len(lines) - 1, "badWidth": bad_width, "rowsWithClassToken": rows_with, "rawTokenOccurrences": raw_occ, "distinctTokens": len(cov_names), "counts": counts}, ensure_ascii=False, indent=2), encoding="utf-8")
    (OUT / "_stage3_normalization.json").write_text(json.dumps({"rules": ["case-insensitive exact bare-name equality", "remove one leading ?", "strip leading P/A/V run length<=4 only on exact equality", "split underscore compounds only on exact segment equality", "template first-segment base as additional key"], "oldCoverageOnly": len(old_cov_only), "resolvedOldCoverageOnly": sum(1 for n in old_cov_only if n in resolutions), "unresolvedOldCoverageOnly": sum(1 for n in old_cov_only if n not in resolutions), "mechanismCounts": mech_counts, "sampleRows": sample_rows}, ensure_ascii=False, indent=2), encoding="utf-8")
    cov_sha_after = hashlib.sha256(COVERAGE.read_bytes()).hexdigest().upper()
    (OUT / "_stage4_reconcile.json").write_text(json.dumps({"bothCoverageTokens": len(resolutions), "coverageOnly": len(unresolved), "rttiOnly": len(rtti_only), "rttiEntriesCovered": len(covered), "directCovered": len(direct), "templateBaseCovered": len(base_cov), "categoryDistribution": cat_dist, "coverageShaAfter": cov_sha_after}, ensure_ascii=False, indent=2), encoding="utf-8")

    write_tsv("rtti_names.tsv", ["bare_class", "prefix", "td_VA", "extra_template_base"], [(e["bare"], e["prefix"], hex(e["tdVA"]), e["extra"]) for e in rtti])
    ctx_rows = []
    for n in cov_names:
        for x in ctxs.get(n, []):
            ctx_rows.append((n, x["line"], x["entry"], x["sub"], x["name"], x["sem"][:400]))
    write_tsv("_coverage_contexts.tsv", ["original_token", "line", "entry", "subsystem", "row_name", "column4_context"], ctx_rows)
    write_tsv("normalization.tsv", ["original_token", "normalized_key", "hit_name", "reasonable"], sample_rows)
    write_tsv("unresolved.tsv", ["name", "coverage_rows", "category", "evidence"], unresolved_rows)

    md = []
    md.append(f"{IMG}  sha256 {sha}")
    md.append("")
    md.append("# R17-R20-RECON · RTTI × coverage 对账纠正版")
    md.append("")
    md.append("> 🔴 本项不是类名正确性判定。未解析只表示：按本卡口径，in-binary RTTI 里没有同名类；不得据此说 coverage 的类名是错的。")
    md.append("")
    md.append(f"- 校验：镜像 sha256 前缀 {EXPECT_PREFIX}，结果有效。镜像大小 {len(b)} B。")
    md.append(f"- 静态读取：只读 .rdata raw {hex(secs['.rdata']['rp'])} 长度 {secs['.rdata']['rs']} B、.data raw {hex(secs['.data']['rp'])} 长度 {secs['.data']['rs']} B，合计 {scan_bytes} B；未建进程、未调试、未启动 gamemd。")
    md.append(f"- coverage.tsv：只读；{len(cb)} B；sha256 {cov_sha_before}；写后复核 {cov_sha_after}；{'未修改' if cov_sha_before == cov_sha_after else '发生变化（异常）'}。")
    md.append("")
    md.append("## Q1 · 两边集合与口径")
    md.append("")
    md.append(f"- in-binary：装饰名 {len(rtti)}；前缀 " + "、".join(f"{k} {v}" for k, v in prefix_counts.items()) + f"；裸名 {len(exact)}；模板实例 {sum(1 for e in rtti if e['extra'])}；首段基名附加键 {len(tmpl)}。")
    md.append(f"- coverage：数据行 {len(lines)-1}；列宽异常 {bad_width}；命中行 {rows_with}；原始 token {raw_occ}；不同 token {len(cov_names)}。")
    md.append("")
    md.append("## Q2 · 归一化规则、消解率与 20 条抽检")
    md.append("")
    md.append("规则：原 token 精确命中优先；再去一个前导 ?；再剥长度 1-4 的 P/A/V 前缀链；再按下划线取完整段；模板名 ?$Xxx@... 另给首段基名 Xxx 作附加键。所有相等判定大小写不敏感；只接受完整相等，不做子串或模糊匹配。")
    md.append(f"- 旧 COVERAGE_ONLY {len(old_cov_only)} 中消解 {sum(1 for n in old_cov_only if n in resolutions)}，消解率 {pct(sum(1 for n in old_cov_only if n in resolutions), len(old_cov_only))}；剩余 {sum(1 for n in old_cov_only if n not in resolutions)}。")
    md.append(f"- 全 coverage token {len(cov_names)} 中消解 {len(resolutions)}，消解率 {pct(len(resolutions), len(cov_names))}。")
    md.append("- 机制：" + "，".join(f"{k}={v}" for k, v in mech_counts.items()) + "。")
    md.append("")
    md.append("| 原 token | 归一化后 | 命中 in-binary 名 | 是否合理 |")
    md.append("|---|---|---|---|")
    for row in sample_rows:
        md.append("| " + " | ".join(clean(x).replace("|", "\\|") for x in row) + " |")
    md.append("")
    md.append("## Q3 · 三桶重算")
    md.append("")
    md.append("BOTH/COVERAGE_ONLY 以 coverage token 为分母；RTTI_ONLY 以 in-binary 裸名条目为分母。")
    md.append("")
    md.append("| 桶 | 旧数 | 纠正后 | 变化 |")
    md.append("|---|---:|---:|---:|")
    md.append(f"| BOTH | 209 | {len(resolutions)} | +{len(resolutions)-209} |")
    md.append(f"| COVERAGE_ONLY | 220 | {len(unresolved)} | -{220-len(unresolved)} |")
    md.append(f"| RTTI_ONLY | 779 | {len(rtti_only)} | -{779-len(rtti_only)} |")
    md.append("")
    md.append(f"RTTI 条目侧：覆盖 {len(covered)}（直接 {len(direct)} + 模板基名 {len(base_cov)}）+ RTTI_ONLY {len(rtti_only)} = {len(rtti)}。")
    md.append("")
    md.append("## Q4 · 剩余未解析逐条归因")
    md.append("")
    md.append(f"共 {len(unresolved)} 条；分布：" + "，".join(f"{k} {v}" for k, v in cat_dist.items()) + "。")
    md.append("")
    md.append("| 名字 | coverage 行数 | 归因分类 | 依据 |")
    md.append("|---|---:|---|---|")
    for name, n, cat, ev in unresolved_rows:
        md.append(f"| {name} | {n} | {cat} | {clean(ev).replace('|', chr(92)+'|')} |")
    md.append("")
    md.append("限制：未解析只能说 in-binary RTTI 里没有同名类；不是类名正确性判定。")
    md.append("")
    md.append("未取得项：0。")
    (OUT / "REPORT.md").write_text("\n".join(md), encoding="utf-8")

if __name__ == "__main__":
    main()
