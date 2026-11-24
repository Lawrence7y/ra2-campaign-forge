#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Dump first 8 KiB of every U1 row for per-file review (write target only)."""
from __future__ import annotations
import os, re

LEAD = r"D:\Project\ra2-campaign-forge\lead"
R14 = os.path.join(LEAD, "next_re_20261117_r14")
UNSURE = os.path.join(R14, "R17_R84_T1_NARRATIVE", "unsure.tsv")
OUT_TXT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "q2_heads_67.txt")
OUT_TSV = os.path.join(os.path.dirname(os.path.abspath(__file__)), "q2_features_67.tsv")

rows = []
with open(UNSURE, encoding="utf-8", newline="") as f:
    header = f.readline().rstrip("\r\n").split("\t")
    ix = {k: header.index(k) for k in ("rel", "bytes", "type", "why")}
    for line in f:
        p = line.rstrip("\r\n").split("\t")
        rows.append({k: p[ix[k]] for k in ix})
rows.sort(key=lambda r: r["rel"])

RE_CN = re.compile(r"[\u4e00-\u9fff]")
RE_VA = re.compile(r"(?m)^\s*(?:0x)?[0-9A-Fa-f]{6,8}\s*[:\t ]")
RE_HEX = re.compile(r"0x[0-9A-Fa-f]{4,8}|\b[0-9A-Fa-f]{8}\b")
RE_JSON = re.compile(r'"(?:[A-Za-z_][\w-]*|[\u4e00-\u9fff]+)"\s*:')
RE_PROC = re.compile(r"RUN_ID|timestamp|selftest|PASS|FAIL|perf|benchmark|build|wrote|assert|hit rate|命中率|自检|检查|报告|结论|未决|待办|轮次|备份|滚回|superseded|before|backup", re.I)

with open(OUT_TXT, "w", encoding="utf-8", newline="\n") as ft, open(OUT_TSV, "w", encoding="utf-8", newline="\n") as fs:
    fs.write("rel\tbytes\tread_bytes\tcn_lines\tn_lines\tva_lines\thex_hits\tjson_keys\tproc_hits\tfirst_line\n")
    for i, r in enumerate(rows, 1):
        path = os.path.join(LEAD, r["rel"].replace("/", os.sep))
        try:
            with open(path, "rb") as f:
                b = f.read(8192)
            got = "OK"
        except OSError as e:
            b = b""
            got = f"UNREADABLE:{e}"
        t = b.decode("utf-8", "replace")
        lines = t.split("\n")[:200]
        nonempty = [x for x in lines if x.strip()]
        cn = sum(1 for x in nonempty if RE_CN.search(x))
        va = sum(1 for x in nonempty if RE_VA.match(x))
        hx = len(RE_HEX.findall(t))
        js = len(RE_JSON.findall(t))
        pr = len(RE_PROC.findall(t))
        first = nonempty[0][:160].replace("\t", " ").replace("\r", " ") if nonempty else ""
        fs.write(f"{r['rel']}\t{r['bytes']}\t{len(b)}\t{cn}\t{len(nonempty)}\t{va}\t{hx}\t{js}\t{pr}\t{first}\n")
        ft.write(f"\n===== [{i:02d}] {r['rel']} | {r['bytes']} B | read={got} len={len(b)} =====\n")
        ft.write(t.rstrip() + "\n")
print(f"rows={len(rows)} bytes={sum(int(r['bytes']) for r in rows)} out={OUT_TXT}")
