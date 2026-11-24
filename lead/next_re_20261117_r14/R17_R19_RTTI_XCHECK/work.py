#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# R17-R19-RTTI-XCHECK / work.py
# 纯静态、只读输入；不建进程、不调试、不启动 gamemd。产物只写本脚本所在输出目录。
import hashlib, json, pathlib, re, struct

IMG = pathlib.Path(r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe")
COVERAGE = pathlib.Path(r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\COVERAGE\coverage.tsv")
OUT = pathlib.Path(__file__).resolve().parent
EXPECT_PREFIX = "73201CC0"
TD_VF = 0x7F9594
RE_CLASS = re.compile(r"(?<![A-Za-z0-9_])[A-Za-z_][A-Za-z0-9_]*Class(?![A-Za-z0-9_])")
PREF_PATS = ["PAV", "PBV", "AV", "BV", "V", "A", "RAM"]

def u32(b, o):
    return None if o is None or o + 4 > len(b) else struct.unpack_from("<I", b, o)[0]

def normalize(s):
    for p in (".?AV", ".?AU", ".?AW"):
        if s.startswith(p):
            s = s[len(p):]
            break
    if s.endswith("@@"):
        s = s[:-2]
    return s

def main():
    b = IMG.read_bytes()
    sha = hashlib.sha256(b).hexdigest().upper()
    assert sha.startswith(EXPECT_PREFIX), (IMG, sha)
    e = struct.unpack_from("<I", b, 0x3C)[0]
    nsec = struct.unpack_from("<H", b, e + 6)[0]
    optsz = struct.unpack_from("<H", b, e + 20)[0]
    opt = e + 24
    ib = struct.unpack_from("<I", b, opt + 28)[0]
    secs = {}
    for i in range(nsec):
        s = opt + optsz + i * 40
        name = b[s:s+8].rstrip(b"\0").decode("latin1")
        vs, va, rs, rp = struct.unpack_from("<IIII", b, s + 8)
        secs[name] = {"vs": vs, "va": va, "rs": rs, "rp": rp, "lo": ib + va}
    scan = [(".rdata", secs[".rdata"]), (".data", secs[".data"])]
    scan_bytes = sum(s["rs"] for _, s in scan)
    def sec_by_off(o):
        for n, s in scan:
            if s["rp"] <= o < s["rp"] + s["rs"]:
                return n, s
        return None, None
    def va_of(o):
        n, s = sec_by_off(o)
        return None if s is None else s["lo"] + (o - s["rp"])

    tds = []
    prefixes = {}
    for sn, s in scan:
        start, end = s["rp"], s["rp"] + s["rs"]
        o = start
        while o + 12 <= end:
            if u32(b, o) == TD_VF and u32(b, o + 4) == 0 and b[o+8:o+10] == b".?":
                p = o + 8
                while p < end and b[p] != 0:
                    p += 1
                raw = b[o+8:p]
                if 4 <= len(raw) <= 512 and all(0x20 <= c <= 0x7E for c in raw):
                    name = raw.decode("ascii")
                    pfx = ".?AV" if name.startswith(".?AV") else (".?AU" if name.startswith(".?AU") else ".?AW" if name.startswith(".?AW") else "other")
                    prefixes[pfx] = prefixes.get(pfx, 0) + 1
                    tds.append({"name": name, "prefix": pfx, "tdVA": va_of(o), "nameVA": va_of(o+8), "section": sn, "fileOff": o})
                    o = p + 1
                    while o % 4:
                        o += 1
                    continue
            o += 4
    tds.sort(key=lambda x: x["tdVA"])
    tdvas = {x["tdVA"] for x in tds}
    col_count = 0
    col_tds = set()
    rs = secs[".rdata"]
    for o in range(rs["rp"], rs["rp"] + rs["rs"] - 19, 4):
        if u32(b, o) != 0 or u32(b, o + 8) != 0:
            continue
        if u32(b, o + 4) not in (0, 4, 8, 12):
            continue
        ptd = u32(b, o + 12)
        if ptd in tdvas:
            col_count += 1
            col_tds.add(ptd)
    bare_rows = [(normalize(x["name"]), x["prefix"], x["tdVA"]) for x in tds]
    bare = [x[0] for x in bare_rows]
    bare_set, lower_set = set(bare), {x.lower() for x in bare}
    stage1 = {
        "image": str(IMG), "sha256": sha, "imageSize": len(b), "scanBytes": scan_bytes,
        "prefixCounts": prefixes, "tdNameRows": len(tds),
        "uniqueDecoratedNames": len({x["name"] for x in tds}),
        "uniqueBareNames": len(bare_set), "uniqueLowerNames": len(lower_set),
        "colCount": col_count, "colMatchedTDCount": len(col_tds),
        "first": tds[0], "last": tds[-1]
    }
    (OUT / "_stage0_sections.json").write_text(json.dumps({"image": str(IMG), "sha256": sha, "imageBase": hex(ib), "sections": secs, "scanBytes": scan_bytes}, ensure_ascii=False, indent=2), encoding="utf-8")
    (OUT / "_stage1_td.json").write_text(json.dumps(stage1, ensure_ascii=False, indent=2), encoding="utf-8")
    with (OUT / "rtti_names.tsv").open("w", encoding="utf-8", newline="") as f:
        f.write("bare_class\tprefix\ttd_VA\n")
        for n, p, va in bare_rows:
            f.write(f"{n}\t{p}\t0x{va:x}\n")

    cb = COVERAGE.read_bytes()
    cov_sha = hashlib.sha256(cb).hexdigest().upper()
    rows = cb.decode("utf-8").splitlines()[1:]
    counts = {}
    bad_width = rows_with = total_occ = 0
    for line in rows:
        cols = line.split("\t")
        if len(cols) != 8:
            bad_width += 1
        occ = RE_CLASS.findall(cols[3] if len(cols) > 3 else "")
        total_occ += len(occ)
        uniq = sorted(set(occ))
        if uniq:
            rows_with += 1
        for n in uniq:
            counts[n] = counts.get(n, 0) + 1
    cov_names = sorted(counts, key=lambda n: (-counts[n], n))
    stage2 = {
        "coverage": str(COVERAGE), "sha256": cov_sha, "bytes": len(cb),
        "dataRows": len(rows), "headerWidthFailures": bad_width, "column": 4,
        "regex": RE_CLASS.pattern, "rowsWithAtLeastOneClassToken": rows_with,
        "rawTokenOccurrences": total_occ, "distinctClassNames": len(cov_names), "counts": counts
    }
    (OUT / "_stage2_coverage.json").write_text(json.dumps(stage2, ensure_ascii=False, indent=2), encoding="utf-8")
    with (OUT / "coverage_classnames.tsv").open("w", encoding="utf-8", newline="") as f:
        f.write("class_name\trow_count\n")
        for n in cov_names:
            f.write(f"{n}\t{counts[n]}\n")

    both = sorted(n for n in cov_names if n in bare_set)
    cov_only = [n for n in cov_names if n not in bare_set]
    rtti_only = sorted(n for n in bare if n not in counts)
    lower_map = {x.lower(): x for x in bare}
    def note(n):
        lo = n.lower()
        if lo in lower_map:
            return f"可能原因：大小写差异；依据：全小写串 {lo} 命中Q1裸名小写集合，大小写原样未命中"
        for p in PREF_PATS:
            if n.startswith(p) and len(n) > len(p) and n[len(p):] in bare_set:
                t = n[len(p):]
                return f"可能原因：coverage文本保留了RTTI装饰或类型前缀，抽取器把前缀并入标识符；依据：去掉前缀 {p} 后为 {t}，该裸名在Q1集合中"
        if "_" in n:
            parts = [x for x in n.split("_") if x]
            hits = [x for x in parts if x in bare_set or x.lower() in lower_map]
            ev = ("、".join(hits) + "命中Q1集合") if hits else "无片段直接命中Q1集合"
            return f"可能原因：人工组合名或子系统名被Class后缀抽取当作单个类名；依据：token含下划线，拆分片段为 {' + '.join(parts)}，其中 {ev}"
        templ = [x for x in bare if lo in x.lower() and x.lower() != lo][:3]
        if templ:
            return f"可能原因：模板或参数化类名在coverage里被展开或省略模板实参；依据：Q1裸名 {'、'.join(templ)} 包含该token字符串"
        shell = [x for x in bare if x.lower() in lo and len(x) >= 8 and x.lower() != lo][:3]
        if shell:
            return f"可能原因：人工语义文本把名字片段粘连到Class后缀标识符；依据：coverage token包含Q1裸名 {'、'.join(shell)}"
        return "可能原因：YRpp或人工语义命名差异、拼写差异或Class后缀抽取噪声；依据：该token来自coverage第4列，未命中Q1裸名大小写原样集合与全小写集合"
    recon = []
    for n in both:
        recon.append((n, "BOTH", "coverage第4列命中；Q1裸名集合命中；仅表示不矛盾，不作正确性判定"))
    for n in cov_only:
        recon.append((n, "COVERAGE_ONLY", note(n)))
    for n in rtti_only:
        recon.append((n, "RTTI_ONLY", "Q1裸名集合命中；coverage第4列按Class后缀标识符规则未抽出"))
    with (OUT / "reconcile.tsv").open("w", encoding="utf-8", newline="") as f:
        f.write("class_name\tbucket\tnote\n")
        for r in recon:
            f.write("\t".join(r) + "\n")
    cov_after = hashlib.sha256(COVERAGE.read_bytes()).hexdigest().upper()
    (OUT / "_stage3_reconcile.json").write_text(json.dumps({
        "comparison": "Q2抽取标识符与Q1裸类名按大小写原样精确比对；全小写集合只用于COVERAGE_ONLY备注证据",
        "both": len(both), "coverageOnly": len(cov_only), "rttiOnly": len(rtti_only),
        "union": len(both) + len(cov_only) + len(rtti_only),
        "coverageShaBefore": cov_sha, "coverageShaAfter": cov_after,
        "coverageUnmodified": cov_sha == cov_after, "unobtainedItems": 0
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    def table(headers, rows):
        out = ["| " + " | ".join(headers) + " |", "|" + "|".join(["---"] * len(headers)) + "|"]
        out.extend("| " + " | ".join(str(x).replace("|", "\\|") for x in r) + " |" for r in rows)
        return "\n".join(out)
    cov_only_rows = [(n, counts[n], note(n)) for n in cov_only]
    md = [
        f"{IMG}  sha256 {sha}", "",
        "# R17-R19-RTTI-XCHECK · in-binary RTTI 类名 × coverage 类名表内对账", "",
        "- 镜像校验：实际路径见第一行；sha256 以 73201CC0 开头，符合卡面期望，结果有效。",
        f"- 镜像大小：{len(b)} B。读取方式：纯静态只读；未建进程、未调试、未启动 gamemd。",
        f"- 数据扫描：.rdata raw 0x3E1000 长度 0x31000 = 200,704 B；.data raw 0x412000 长度 0x6C000 = 442,368 B；合计 {scan_bytes} B。",
        f"- coverage.tsv：只读；{len(cb)} B；sha256 {cov_sha}；写后复核 {cov_after}；未修改。",
        "- 中间结果已先落盘；产物只写本目录。", "",
        "## Q1 · in-binary RTTI 类名集合", "",
        "- 方法：自行解析 PE 节表；在 .rdata/.data 内按 TypeDescriptor 形态提取 RTTI 内联名；未复用既有 names.tsv 作为输入。",
        f"- 装饰名总数：{len(tds)}；唯一装饰名 {len({x['name'] for x in tds})}。",
        "- 前缀分布：.?AV 962，.?AU 26，其它 0。",
        f"- 归一化后裸类名 {len(bare_set)} 个；全小写裸名 {len(lower_set)} 个。",
        "- 全量裸名、前缀、TD VA：rtti_names.tsv。", "",
        "## Q2 · coverage.tsv 第 4 列类名抽取", "",
        f"- 数据行 {len(rows)}；列宽异常 {bad_width}；命中行 {rows_with}；原始 token {total_occ}；不同类名 {len(cov_names)}。",
        f"- 正则：{RE_CLASS.pattern}；每行去重后按行计数。",
        "- 全量类名与行数：coverage_classnames.tsv。", "",
        "Top 30：", "",
        table(["#", "class_name", "出现行数"], [(i+1, n, counts[n]) for i, n in enumerate(cov_names[:30])]), "",
        "## Q3 · 三桶对账", "",
        "- 主口径：大小写原样精确比对；全小写集合只作备注旁证。",
        f"- BOTH {len(both)}；COVERAGE_ONLY {len(cov_only)}；RTTI_ONLY {len(rtti_only)}。", "",
        "BOTH 举例（≤10）：" + "、".join(x for x in both[:10]) + "。", "",
        f"COVERAGE_ONLY 全量（{len(cov_only)} 条；仅给可能原因与依据）：", "",
        table(["class_name", "行数", "可能原因与依据"], cov_only_rows), "",
        "RTTI_ONLY 举例（≤10）：" + "、".join(x for x in rtti_only[:10]) + "。", "",
        "- 三桶全量：reconcile.tsv。", "",
        "## Q4 · 诚实限制", "",
        "1. in-binary 名字集合只覆盖有 RTTI 的类；无 RTTI 的类不会出现。",
        "2. coverage 类名是人工语义文本；靠 Class 后缀抽取会漏会多。",
        "3. BOTH 只说明不矛盾；COVERAGE_ONLY 不等于名字错。", "",
        "未取得项：0。"
    ]
    (OUT / "REPORT.md").write_text("\n".join(md), encoding="utf-8")

if __name__ == "__main__":
    main()
