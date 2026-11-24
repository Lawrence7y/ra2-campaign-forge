#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""check_all.py — 审计复核脚本 (C/E/F + B/D 抽样清单)

复用 verify.py (本审计自建, 不 import 执行方 mev675.py) 的检测器。
"""
import csv
import json
import os
import re
from collections import defaultdict, Counter

import verify as V

OUT = V.OUT
R14 = V.R14
LEAD = V.LEAD
MEASURE = V.MEASURE
SHORT_TOK = re.compile(r"(?<![0-9a-f])[0-9a-f]{6,7}(?![0-9a-f])")
RING = ["①", "②", "③", "④"]


def walk_basenames():
    """产出 (rel, basename_lower) for all files under LEAD excluding .git / MEASURE / AUDIT."""
    norm_out = os.path.normcase(os.path.abspath(OUT))
    norm_meas = os.path.normcase(os.path.abspath(MEASURE))
    for root, dirs, fnames in os.walk(LEAD):
        dirs[:] = [d for d in dirs if d.lower() != ".git"]
        for fn in fnames:
            full = os.path.join(root, fn)
            n = os.path.normcase(os.path.abspath(full))
            if n.startswith(norm_out) or n.startswith(norm_meas):
                continue
            rel = os.path.relpath(full, LEAD).replace("\\", "/")
            yield rel, fn.lower()


def check_E():
    _, eset = V.load_entry_set()
    z675 = V.load_675()
    # 与执行方完全一致的 short map: stripped form, len 6..7
    short2e = {}
    for e in eset:
        s = e.lstrip("0")
        if 6 <= len(s) <= 7:
            short2e[s] = e
    # extended map: 额外把 zfill(6)/zfill(7) 形式也纳入
    short2e_ext = dict(short2e)
    for e in eset:
        s = e.lstrip("0")
        for L in (6, 7):
            short2e_ext[s.zfill(L)] = e

    inv = defaultdict(set)
    inv_ext = defaultdict(set)
    nfiles = 0
    for rel, base in walk_basenames():
        nfiles += 1
        for t in SHORT_TOK.findall(base):
            if t in short2e:
                inv[short2e[t]].add(rel)
            if t in short2e_ext:
                inv_ext[short2e_ext[t]].add(rel)

    # 执行方口径: s = stripped form
    hit_exec = {}
    for e in z675:
        s = e.lstrip("0")
        fs = sorted(inv.get(e, []))
        if fs:
            hit_exec[e] = fs
    # 扩展口径: 该 entry 的所有短形式映射文件
    hit_ext = {}
    for e in z675:
        fs = sorted(inv_ext.get(e, []))
        if fs:
            hit_ext[e] = fs

    # 对执行方口径的每个文件做四环检查 (全文 any + 行首 line-start)
    details = []
    for e, fs in hit_exec.items():
        for f in fs:
            full = os.path.join(LEAD, f.replace("/", os.sep))
            rings_any = ""
            rings_line = ""
            try:
                with open(full, "r", encoding="utf-8", errors="replace") as fh:
                    txt = fh.read(8 * 1024 * 1024)
                rings_any = "".join(c for c in RING if c in txt)
                cnt = V.ring_line_starts(txt)
                rings_line = "".join(c for c in RING if cnt.get(c, 0) > 0)
            except OSError:
                pass
            details.append(dict(entry=e, file=f,
                                rings_any=rings_any,
                                rings_line_start=rings_line,
                                four_line_start=all(c in rings_line for c in RING),
                                four_any=all(c in rings_any for c in RING)))

    # PROOF_* 短形式文件专项 (含 4D7330 示例)
    proof_files = []
    for rel, base in walk_basenames():
        if "proof" in base:
            toks = SHORT_TOK.findall(base)
            if toks and any(len(t) in (6, 7) for t in toks):
                proof_files.append(rel)
    proof_ring = []
    for f in proof_files:
        full = os.path.join(LEAD, f.replace("/", os.sep))
        try:
            with open(full, "r", encoding="utf-8", errors="replace") as fh:
                txt = fh.read(8 * 1024 * 1024)
        except OSError:
            continue
        cnt = V.ring_line_starts(txt)
        anyr = "".join(c for c in RING if c in txt)
        liner = "".join(c for c in RING if cnt.get(c, 0) > 0)
        proof_ring.append(dict(file=f, rings_any=anyr, rings_line_start=liner,
                               four_line_start=all(c in liner for c in RING)))

    return dict(n_files_scanned=nfiles,
                n_rows_exec=len(hit_exec), rows_exec=sorted(hit_exec),
                n_files_exec=len({f for fs in hit_exec.values() for f in fs}),
                n_rows_ext=len(hit_ext), rows_ext=sorted(hit_ext),
                detail_exec=details,
                n_proof_shortform_files=len(proof_files),
                proof_ring=proof_ring)


def check_C():
    z675 = V.load_675()
    med = {e: r for e, r in z675.items() if r["bucket"] == "CTX_MEDIUM"}
    anchor_counter = Counter()
    atlas_rows = []
    for e, r in med.items():
        note = r["note"]
        m = re.search(r"锚点=([^\s]+?):\d+\s*\[", note)
        anchor = m.group(1) if m else "(no-anchor)"
        anchor_counter[anchor] += 1
        if os.path.basename(anchor).lower() == "function_atlas.tsv":
            atlas_rows.append(e)
    return dict(n_medium=len(med), n_atlas_anchor=len(atlas_rows),
                atlas_rows=sorted(atlas_rows),
                anchor_top=anchor_counter.most_common(12))


def check_F():
    """查最终交付 TSV 是否把执行方自己的中间产物算作命中源。
    只认真正属于本卡的产物: _hits_primary.tsv / _hits_wide.tsv / R16_MEASURE_EVID675 路径。
    (外部文件里恰好叫 _hits_gframe.txt 的不是自污染。)
    """
    findings = {}
    for fn in ["buckets675.tsv", "buckets675_wide.tsv", "recheck116.tsv", "recheck116_wide.tsv", "sample18.tsv"]:
        p = os.path.join(MEASURE, fn)
        if not os.path.exists(p):
            continue
        bad = []
        with open(p, encoding="utf-8", newline="") as fh:
            for i, line in enumerate(fh, 1):
                low = line.lower()
                if ("_hits_primary.tsv" in low or "_hits_wide.tsv" in low
                        or "r16_measure_evid675/" in low or "r16_measure_evid675\\" in low):
                    bad.append(i)
        findings[fn] = dict(n_bad_lines=len(bad), bad_lines=bad[:20])
    return findings


def sample_lists():
    z675 = V.load_675()
    strong = sorted(e for e, r in z675.items() if r["bucket"] == "CTX_STRONG")
    med = sorted(e for e, r in z675.items() if r["bucket"] == "CTX_MEDIUM")
    def pick(seq, n):
        if len(seq) <= n:
            return seq
        idx = [round(i * (len(seq) - 1) / (n - 1)) for i in range(n)]
        return [seq[i] for i in sorted(set(idx))]
    b12 = pick(strong, 12)
    z116 = V.load_116()
    all116 = sorted(z116)
    d6 = pick(all116, 6)
    return dict(strong_n=len(strong), medium_n=len(med), b_sample=b12, d_sample=d6)


def main():
    print("===== E =====")
    e = check_E()
    print(json.dumps(e, ensure_ascii=False, indent=1))
    print("\n===== C =====")
    c = check_C()
    print(json.dumps(c, ensure_ascii=False, indent=1))
    print("\n===== F =====")
    f = check_F()
    print(json.dumps(f, ensure_ascii=False, indent=1))
    print("\n===== SAMPLES =====")
    s = sample_lists()
    print(json.dumps(s, ensure_ascii=False, indent=1))
    json.dump(dict(E=e, C=c, F=f, S=s), open(os.path.join(OUT, "_check_data.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("\n[out] _check_data.json")


if __name__ == "__main__":
    main()
