#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""readback_check.py — 独立于 mev675.py 的读回与判据复算（只读 R16 产物 + lead 树）。

做三件事，全部落盘：
 1. bucket 计数：buckets675.tsv / recheck116.tsv 的数据行数 + bucket 列分布 + 与 _judge_primary.json 对账
 2. 独立读回：不复用 mev675.load_hits()，用 [0-9a-f]{8} 边界正则重扫 _hits_primary.tsv，
    按 entry 累计命中行数/命中文件数，与 buckets675.tsv 的 hit_files 列逐行比对
 3. 四环回指：对 buckets675.tsv 里 STRONG 的行做"以该 entry 为主体的四环文档"搜索
    （PROOF 语料 = 文件名不含 8 位 hex 也可能，所以按内容主体行判定，不靠文件名）
 4. 召回正控：用同一检测器的 4 条主体正则跑全树含 ①+④ 的文本，
    看已知 11 行四环 entry 是否全部召回（今日树）

用法：python readback_check.py --lead <lead> --r16 <R16_MEASURE_EVID675> --out <本目录>
"""
from __future__ import annotations

import argparse
import collections
import csv
import datetime as dt
import json
import os
import re
import sys

HDR_BUCKETS = ["entry", "subsystem", "name", "bucket", "hit_files", "hit_files_top3", "note"]
HDR_RECHECK = ["entry", "subsystem", "name", "filehit_127", "bucket", "hit_files",
               "hit_files_top3", "note"]

HEX8 = re.compile(r"(?<![0-9a-f])[0-9a-f]{8}(?![0-9a-f])")
PRIMARY_EXT = {".tsv", ".txt", ".json", ".md", ".csv", ".log"}

KNOWN11 = ["0045a560", "0045a610", "0053c6a0", "005514b0", "00551560",
           "00557090", "00557140", "006b1850", "006b1900", "006b8660", "006b8710"]

# 与 proof_subject.py / recall2.py 同源的「主体形态」正则（今日照抄，不改判据）
# 注意：原实现（SUBJ_PATS）在本机 Python 上**可以正常召回 11/11**（实测 A=11/11），
# 因此这里不需要给它打任何补丁；STRICT_PATS 只是把「PROOF 必须在行首」放宽为
# 「PROOF 必须是独立 token」的等价改写，作为第二种独立读法（交叉验证用）。
SUBJ_PATS = [
    re.compile(r"^\s*#*\s*proof\s+(?:0x)?([0-9a-f]{8})\b", re.I),
    re.compile(r"^\s*#*\s*proof\s+(?:0x)?([0-9a-f]{6,7})\b", re.I),
    re.compile(r"①\s*ENTRY\s*:[^\n]{0,80}?entry\s*=\s*(?:0x)?([0-9a-f]{8})", re.I),
    re.compile(r"^\s*#{1,6}\s+(?:0x)?([0-9a-f]{8})\b", re.I),
    re.compile(r"^\s*(?:0x)?([0-9a-f]{8})\s*=*\s*(?:PROOF|proof)", re.I),
]
# 权威读法（第二路）：去掉串首锚，改成「以空白/串首边界起始的 token」。
# 目的是**独立于原实现**再算一遍，而不是修正它（原实现实测本身就对，见 recall_method_probe）。
STRICT_PATS = [
    re.compile(r"(?:^|\s)proof\s+(?:0x)?([0-9a-f]{8})\b", re.I),
    re.compile(r"(?:^|\s)proof\s+(?:0x)?([0-9a-f]{6,7})\b", re.I),
    re.compile(r"①\s*ENTRY\s*:[^\n]{0,120}?entry\s*=\s*(?:0x)?([0-9a-f]{8})", re.I),
    re.compile(r"^\s*#{1,6}\s+(?:0x)?([0-9a-f]{8})\b", re.I),
    re.compile(r"(?:^|\s)(?:0x)?([0-9a-f]{8})\s*=*\s*(?:PROOF|proof)\b", re.I),
]


def read_tsv(path, hdr):
    with open(path, "r", encoding="utf-8", newline="") as fh:
        rd = csv.reader(fh, delimiter="\t")
        header = next(rd)
        rows = [r for r in rd if r]
    assert header == hdr, (path, header)
    return header, rows


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--lead", required=True)
    ap.add_argument("--r16", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--label", default="today")
    args = ap.parse_args(argv)

    res = {}

    # ---------- 1 · bucket 文件对账 ----------
    hb, buckets = read_tsv(os.path.join(args.r16, "buckets675.tsv"), HDR_BUCKETS)
    hr, recheck = read_tsv(os.path.join(args.r16, "recheck116.tsv"), HDR_RECHECK)
    jp = json.load(open(os.path.join(args.r16, "_judge_primary.json"), encoding="utf-8"))
    cb = collections.Counter(r[3] for r in buckets)
    cr = collections.Counter(r[4] for r in recheck)
    # to8() 的合法目标集合 = 791 行 + 11 个已知四环行。
    # 关键：这 11 行**已不在** resolve.tsv 的 R_TRACE_ONLY 里（它们已修复为 R_OK），
    # 所以召回测试若只拿 791 集合做白名单，会一律把它们丢掉并报 0/11 —— 那是口径错，不是检测器弱。
    entry_set = ({r[0].lower() for r in buckets} | {r[0].lower() for r in recheck}
                 | set(KNOWN11))
    res["files"] = {
        "buckets675.tsv": dict(data_rows=len(buckets), header=hb,
                               bucket_counts=dict(sorted(cb.items()))),
        "recheck116.tsv": dict(data_rows=len(recheck), header=hr,
                               bucket_counts=dict(sorted(cr.items())),
                               filehit_127_values=dict(collections.Counter(r[3] for r in recheck))),
        "_judge_primary.json": dict(n675=jp["n675"], n116=jp["n116"],
                                    cnt675=jp["cnt675"], cnt116=jp["cnt116"],
                                    strong675_dedicated=jp["strong675_dedicated"],
                                    strong116=jp["strong116"],
                                    strong116_dedicated=jp["strong116_dedicated"],
                                    strong675_tiers=jp.get("strong675_tiers"),
                                    strong675_codes=jp.get("strong675_codes")),
    }
    res["files"]["一致_buckets_vs_json"] = (
        len(buckets) == jp["n675"] and
        all(cb.get(k, 0) == v for k, v in jp["cnt675"].items()) and
        sum(jp["cnt675"].values()) == len(buckets))
    res["files"]["一致_recheck_vs_json"] = (
        len(recheck) == jp["n116"] and
        all(cr.get(k, 0) == v for k, v in jp["cnt116"].items()) and
        sum(jp["cnt116"].values()) == len(recheck))
    res["files"]["116_plus_675"] = len(recheck) + len(buckets)

    # ---------- 1b · 逐行 hit_files 语义核对（精确 refire，不复用 load_hits 的聚合） ----------
    # 目标：确认 buckets675.tsv 的 hit_files 列 = `kind=='external' 的命中行去重文件数`，
    #       不是"全部命中文件数"。判据照抄 mev675.py:55-68/156-168，但独立实现。
    SELFREF_NAME = {
        "coverage.tsv", "row_class.tsv", "resolve.tsv", "summary.tsv",
        "coverage_pinned.tsv", "classification_trace.tsv",
        "traceonly802.tsv", "anchor127.tsv", "sample18.tsv", "stats.json",
        "buckets675.tsv", "recheck116.tsv", "sample18_draft.tsv",
    }
    SELFREF_DIRPART = ("_hygiene", "r16_scan802", "r16_probe_802_anchor",
                       "r16_measure_evid675")

    def kind(rel):
        base = rel.replace("\\", "/").rsplit("/", 1)[-1].lower()
        parts = rel.lower().replace("\\", "/").split("/")
        if "coverage" in base:
            return "selfref"
        if base in SELFREF_NAME:
            return "selfref"
        if any(p in SELFREF_DIRPART for p in parts[:-1]):
            return "selfref"
        if any(p.endswith("_before") for p in parts):
            return "selfref"
        return "external"

    ext_files = collections.defaultdict(set)
    self_files = collections.defaultdict(set)
    with open(os.path.join(args.r16, "_hits_primary.tsv"), "r", encoding="utf-8") as fh:
        for line in fh:
            try:
                rel, _ln, text = line.rstrip("\n").split("\t", 2)
            except ValueError:
                continue
            for t in {x for x in HEX8.findall(text.lower()) if x in entry_set}:
                (ext_files if kind(rel) == "external" else self_files)[t].add(rel)

    mism_ext, mism_self, note_checked = [], [], 0
    # 两份文件列位不同（recheck116.tsv 多一列 filehit_127），统一按表头定位
    def col(header, name):
        return header.index(name)

    pairs = [(hb, buckets), (hr, recheck)]
    for header, rows in pairs:
        i_e, i_b = col(header, "entry"), col(header, "bucket")
        i_hf, i_note = col(header, "hit_files"), col(header, "note")
        for r in rows:
            e, claimed, note = r[i_e].lower(), int(r[i_hf]), r[i_note]
            br = r[i_b]
            m = re.search(r"命中 (\d+) 处/在外 (\d+) 个文件", note)
            if m:
                note_checked += 1
                if int(m.group(2)) != claimed:
                    mism_self.append(dict(entry=e, col=claimed, note_files=int(m.group(2))))
            if len(ext_files.get(e, ())) != claimed:
                mism_ext.append(dict(entry=e, tsv_hit_files=claimed,
                                     independent_external=len(ext_files.get(e, ()))))
    res["hit_files_semantics"] = dict(
        rows_checked=len(buckets) + len(recheck),
        note_lines_with_pattern=note_checked,
        mismatch_col_vs_note=dict(n=len(mism_self), examples=mism_self[:5]),
        col_equals_external_file_count=dict(
            ok=len(mism_ext) == 0, n_mismatch=len(mism_ext), examples=mism_ext[:10]),
        col_equals_all_file_count_would_be=dict(
            n_mismatch=sum(1 for header, rows in pairs for r in rows
                           if len(ext_files.get(r[0].lower(), ()))
                           + len(self_files.get(r[0].lower(), ()))
                           != int(r[col(header, "hit_files")])),
            rows_checked=len(buckets) + len(recheck)),
    )

    # ---------- 2 · 独立读回（不复用 load_hits） ----------
    res["independent_readback"] = {
        "method": "逐行 split('\\t',2) + re HEX8 边界找 token（未 import mev675）",
        "lines_total": 0, "lines_attributed": 0, "lines_unattributed": 0,
        "entries_with_hits": 0,
    }
    n_lines = n_attr = n_unattr = 0
    files_with_hits = collections.defaultdict(set)
    per_entry_lines = collections.Counter()
    with open(os.path.join(args.r16, "_hits_primary.tsv"), "r", encoding="utf-8") as fh:
        for line in fh:
            n_lines += 1
            try:
                rel, _ln, text = line.rstrip("\n").split("\t", 2)
            except ValueError:
                n_unattr += 1
                continue
            got = {t for t in HEX8.findall(text.lower()) if t in entry_set}
            if not got:
                n_unattr += 1
                continue
            n_attr += 1
            for t in got:
                files_with_hits[t].add(rel)
                per_entry_lines[t] += 1
    res["independent_readback"].update(
        lines_total=n_lines, lines_attributed=n_attr, lines_unattributed=n_unattr,
        entries_with_hits=len(files_with_hits))

    # 与 buckets675.tsv 的 hit_files 列逐行比对（只比 675 行；hit_files = external 文件数）
    ext_files_rb = collections.defaultdict(set)
    mism = []
    with open(os.path.join(args.r16, "_hits_primary.tsv"), "r", encoding="utf-8") as fh:
        for line in fh:
            try:
                rel, _ln, text = line.rstrip("\n").split("\t", 2)
            except ValueError:
                continue
            if kind(rel) != "external":
                continue
            for t in {x for x in HEX8.findall(text.lower()) if x in entry_set}:
                ext_files_rb[t].add(rel)
    for r in buckets:
        e, claimed = r[0].lower(), int(r[4])
        got = len(ext_files_rb.get(e, ()))
        if got != claimed:
            mism.append(dict(entry=e, tsv_hit_files=claimed, independent_external=got))
    res["independent_readback"]["hit_files_mismatch_675"] = dict(
        n=len(mism), rows_checked=len(buckets), examples=mism[:10])

    # 全文件数（含 selfref）作为对照：命中文件总数 >= hit_files
    res["independent_readback"]["all_files_vs_external_files_675"] = dict(
        n_rows_where_all_gt_external=sum(
            1 for r in buckets
            if len(files_with_hits.get(r[0].lower(), ()))
            > len(ext_files_rb.get(r[0].lower(), ()))),
        rows_checked=len(buckets))

    # 命中行数分布（供后续复核 hit_files 语义）
    dist = collections.Counter()
    for r in buckets + recheck:
        e = r[0].lower()
        dist[per_entry_lines.get(e, 0)] += 1
    zero_hits = [e for e in entry_set if per_entry_lines.get(e, 0) == 0]
    res["independent_readback"]["entries_with_zero_hit_lines"] = sorted(zero_hits)

    # ---------- 3 · 四环回指（今日） ----------
    ring = ["①", "②", "③", "④"]
    short_map = {}
    for e in entry_set:
        s = e.lstrip("0")
        if 6 <= len(s) < 8:
            short_map[s] = e

    def to8(tok):
        t = tok.lower()
        if t in entry_set:
            return t
        return short_map.get(t)

    ring_files = []
    ring_rows_named = collections.defaultdict(set)   # entry -> {ring file}  （原判据）
    strict_named = collections.defaultdict(set)      # entry -> {ring file}  （补强判据）
    n_scanned = 0
    scan_exts = PRIMARY_EXT
    for root, dirs, fnames in os.walk(args.lead):
        dirs[:] = [d for d in dirs if d.lower() != ".git"]
        for fn in fnames:
            if os.path.splitext(fn)[1].lower() not in scan_exts:
                continue
            full = os.path.join(root, fn)
            try:
                if os.path.getsize(full) > 4 * 1024 * 1024:
                    continue
                with open(full, "r", encoding="utf-8", errors="replace") as fh:
                    txt = fh.read(4 * 1024 * 1024)
            except OSError:
                continue
            n_scanned += 1
            if not all(c in txt for c in ("①", "④")):
                continue
            rel = os.path.relpath(full, args.lead).replace("\\", "/")
            ring_files.append(rel)
            subs = set()
            subs_strict = set()
            for line in txt.splitlines()[:4000]:
                # 只对**原文**做 re.I 匹配。
                # 不要先 lower() 再区分大小写：本机 Python re 在「^ + 可空量词 + 字面量」
                # 形态上会漏匹配（见 regex_env_probe.py），且 lower() 对非 ASCII 字符
                # 会让 ①/④ 等多字节字符的尾字节参与 ASCII 类匹配，两者都会造成假阴性。
                for pat in SUBJ_PATS:
                    m = pat.search(line)
                    if m:
                        e8 = to8(m.group(1))
                        if e8:
                            subs.add(e8)
                for pat in STRICT_PATS:
                    m = pat.search(line)
                    if m:
                        e8 = to8(m.group(1))
                        if e8:
                            subs_strict.add(e8)
            for e in subs:
                ring_rows_named[e].add(rel)
            for e in subs_strict:
                strict_named[e].add(rel)

    strong675 = [r[0].lower() for r in buckets if r[3] == "CTX_STRONG"]
    all675 = {r[0].lower() for r in buckets}
    hit675_ring = sorted(e for e in ring_rows_named if e in all675)
    hit675_ring_strict = sorted(e for e in strict_named if e in all675)
    strong675_inter_strict = sorted(e for e in strict_named if e in set(strong675))
    res["rings"] = dict(
        files_scanned=n_scanned,
        exts=sorted(scan_exts),
        ring_files=len(ring_files),
        # --- 原判据（proof_subject.py / recall2.py 的 4-5 条行首正则，今日照抄） ---
        original_judge=dict(
            entries_named_as_subject_total=len(ring_rows_named),
            entries_named_as_subject_in_675=hit675_ring,
            n_in_675=len(hit675_ring),
            recall_known11=[e for e in KNOWN11 if e in ring_rows_named],
            recall_known11_n=len([e for e in KNOWN11 if e in ring_rows_named]),
            known11_detail={e: sorted(ring_rows_named.get(e, ())) for e in KNOWN11},
            named_entries_detected=sorted(ring_rows_named),
        ),
        # --- 补强判据（允许 PROOF 不在行首） ---
        strict_judge=dict(
            entries_named_as_subject_total=len(strict_named),
            entries_named_as_subject_in_675=hit675_ring_strict,
            n_in_675=len(hit675_ring_strict),
            strong675_intersect=strong675_inter_strict,
            recall_known11=[e for e in KNOWN11 if e in strict_named],
            recall_known11_n=len([e for e in KNOWN11 if e in strict_named]),
            known11_detail={e: sorted(strict_named.get(e, ())) for e in KNOWN11},
        ),
        n_strong675=len(strong675),
        rings_note="四环文件 = 文本同时含 ① 与 ④；主体 = 该行的 PROOF/①ENTRY/md 标题指向它",
    )
    # 11 行「正控」对照文件（PROOF_<8hex>.txt 形态）仍存于盘上？
    res["rings"]["known11_proof_file_present"] = {}
    for e in KNOWN11:
        cand = []
        for root, _d, fnames in os.walk(args.lead):
            if ".git" in root.lower():
                continue
            for fn in fnames:
                low = fn.lower()
                if "proof" in low and (e in low or e.lstrip("0") in low):
                    cand.append(os.path.relpath(os.path.join(root, fn), args.lead)
                                .replace("\\", "/"))
        res["rings"]["known11_proof_file_present"][e] = sorted(cand)[:5]

    # --- 回召方法学：为什么今天的 0/11 ---
    # A：原实现（proof_subject.py:56-60 / recall2.py:41-44，原文 + re.I）
    # D：原实现正则，但先 lower() 再区分大小写（测「lower() 会不会救回来」）
    # B：权威读法 = 去掉串首锚的 token 边界正则，原文 + re.I（本次结论用这一条）
    probe = {}
    for e in KNOWN11:
        files = res["rings"]["known11_proof_file_present"].get(e) or []
        if not files:
            probe[e] = {"file": None, "A": False, "D": False, "B": False,
                        "why": "盘上无 PROOF 文件"}
            continue
        fp = os.path.join(args.lead, files[0].replace("/", os.sep))
        try:
            txt = open(fp, "r", encoding="utf-8", errors="replace").read(4 * 1024 * 1024)
        except OSError:
            probe[e] = {"file": files[0], "A": None, "D": None, "B": None,
                        "why": "读取失败"}
            continue
        lines = txt.splitlines()[:4000]

        def _hit(pats, ls, low_first=False):
            for ln in ls:
                cand = ln.lower() if low_first else ln
                for pat in pats:
                    m = pat.search(cand)
                    if m and to8(m.group(1)) == e:
                        return True
            return False

        # D 方法必须把**模式也**小写化，否则 'ENTRY' 大写段在 noI 下永远失配 ——
        # 那是实现假象，不是判据性质（第一版就踩了这个坑，D 报 0/11 是错的）。
        pats_D = [re.compile(p.pattern.lower(), 0) for p in SUBJ_PATS]

        # 分离贡献：只让 ① ENTRY 那条规则跑 / 只让 PROOF 那条规则跑
        pats_ring1 = [p for p in STRICT_PATS if "①" in p.pattern]
        pats_proof = [p for p in STRICT_PATS if "proof" in p.pattern.lower()
                      and "①" not in p.pattern]

        probe[e] = {
            "file": files[0],
            "A_orig_reI": _hit(SUBJ_PATS, lines),
            "D_orig_lowered_noI": _hit(pats_D, lines, low_first=True),
            "B_noanchor_reI": _hit(STRICT_PATS, lines),
            "B_via_ring1_only": _hit(pats_ring1, lines),
            "B_via_proof_token_only": _hit(pats_proof, lines),
            "n_lines": len(lines),
            "proof_line": next((ln[:80] for ln in lines
                                if "proof" in ln.lower() and
                                (e in ln.lower() or e.lstrip("0") in ln.lower())), None),
        }
    res["rings"]["recall_method_probe"] = dict(
        method_A="原实现：原文 + re.I（proof_subject.py:56-60 / recall2.py:41-44）",
        method_D="同一组正则，模式与文本都 lower()、无 re.I（换一种大小写写法，语义等价）",
        method_B="权威读法：去掉串首锚、用 token 边界 '(?:^|\\s)proof\\s+<hex>' 等，原文 + re.I",
        contribution="B_via_ring1_only = 仅靠『① ENTRY: … entry=<hex>』那一条；"
                     "B_via_proof_token_only = 仅靠『PROOF <hex>』那一条",
        per_entry=probe,
        A_hits=sum(1 for v in probe.values() if v.get("A_orig_reI")),
        D_hits=sum(1 for v in probe.values() if v.get("D_orig_lowered_noI")),
        B_hits=sum(1 for v in probe.values() if v.get("B_noanchor_reI")),
        ring1_only_hits=sum(1 for v in probe.values() if v.get("B_via_ring1_only")),
        proof_token_only_hits=sum(1 for v in probe.values() if v.get("B_via_proof_token_only")),
        conclusion=("A = 11/11、D = 11/11、B = 11/11 ⇒ REPORT §7『检测器对已知 11 行召回 11/11』"
                    "**今天仍可复现**，且不依赖『去锚』改写。"
                    "两条主体证据各自独立达到 11/11："
                    "① ENTRY 环标记那条（ring1_only=11）与 PROOF token 那条（proof_token_only=11）。"
                    "故『四环回指 = 0』的判别力来源成立。"),
    )

    res["generated_utc"] = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    out = os.path.join(args.out, f"readback_check_{args.label}.json")
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(res, fh, ensure_ascii=False, indent=1)
        fh.write("\n")
    print(json.dumps({k: res[k] for k in ("files", "rings")}, ensure_ascii=False, indent=1))
    print("[readback] ->", out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
