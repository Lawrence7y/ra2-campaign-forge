#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""verify.py — 独立审计检测器 (R16-AUDIT-EVID675)

不 import mev675.py。自建四环检测器 + 复核脚本。

核心判据 (严格/专用): 一个文件 F 是 entry E 的「四环文档」当且仅当
  1) F 中存在以 ①②③④ 各自作为「行首首个非空白字符」的独立行 (各至少一行);
  2) F 把 E 声明为它的 (唯一) 主体, 主体来源限于强信号:
       a. 文件名中含 E 的 8/7/6 位 hex token (经 entry_set / short_map 归一到 8 位);
       b. 文件前若干行 `PROOF <hex>` 头;
       c. `① ... entry=<hex>` 行 (第①环里的 entry 字段)。
  3) F 声明的互异主体 entry 集合恰为 {E} —— 以此排除 PROOFS.md /
     GOAL_THREE_TARGETS.md 这类「多 entry 合并文档 + ①②③④ 当通用小节符号」的假阳性。

另提供 loose 判据 (文件含四环行且 E 任意出现在文件中) 仅用于对照展示假阳性规模。
"""
import csv
import json
import os
import re
import subprocess
import sys
from collections import defaultdict

# ---------- 路径 ----------
OUT = os.path.dirname(os.path.abspath(__file__))                       # R16_AUDIT_EVID675
R14 = os.path.dirname(OUT)                                              # next_re_20261117_r14
LEAD = os.path.dirname(R14)                                             # lead
MEASURE = os.path.join(R14, "R16_MEASURE_EVID675")
RESOLVE = os.path.join(R14, "R16_BASE", "evid", "resolve.tsv")
BUCKETS = os.path.join(MEASURE, "buckets675.tsv")
RECHECK = os.path.join(MEASURE, "recheck116.tsv")

RINGS = ["①", "②", "③", "④"]
PRIMARY_EXT = (".tsv", ".txt", ".json", ".md", ".csv", ".log")
CODE_EXT = (".py", ".asm", ".c", ".h", ".cpp", ".inc", ".bat", ".ps1")

KNOWN11 = ["0045a560", "0045a610", "0053c6a0", "005514b0", "00551560",
           "00557090", "00557140", "006b1850", "006b1900", "006b8660", "006b8710"]

HEXTOK = re.compile(r"(?<!-[0-9a-z])(?<![0-9a-z])(0x)?([0-9a-f]{6,8})(?![0-9a-z])", re.I)


def load_entry_set():
    with open(RESOLVE, encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh, delimiter="\t"))
    eset = {r["entry"].strip().lower() for r in rows if r.get("entry", "").strip()}
    return rows, eset

def build_short_map(eset):
    """6/7 位 hex -> 8 位 entry。仅在唯一映射时保留。"""
    cand = defaultdict(set)
    for e in eset:
        s = e.lstrip("0") or "0"
        for L in (6, 7):
            if len(s) <= L:
                cand[s.zfill(L).lower()].add(e)   # 7/6 位补前导零形式
        cand[s.lower()].add(e)                      # 去零短形式本身
    smap = {}
    for k, v in cand.items():
        if len(v) == 1 and 5 <= len(k) <= 8:
            smap[k] = next(iter(v))
    return smap


def to8(tok, eset, smap):
    t = tok.lower()
    if t.startswith("0x"):
        t = t[2:]
    if t in eset:
        return t
    if t in smap:
        return smap[t]
    # 6/7 位: 补零到 8
    z = t.zfill(8)
    if z in eset:
        return z
    return None


def load_675():
    out = {}
    with open(BUCKETS, encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh, delimiter="\t"):
            out[r["entry"].strip().lower()] = r
    return out


def load_116():
    out = {}
    with open(RECHECK, encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh, delimiter="\t"):
            out[r["entry"].strip().lower()] = r
    return out


def list_candidate_files(exts):
    """用 rg 列含 ① 与 ④ 的文本文件, 排除 .git / 两卡产物。"""
    rel_out = os.path.relpath(OUT, LEAD).replace("\\", "/")
    rel_meas = os.path.relpath(MEASURE, LEAD).replace("\\", "/")
    cmd = ["rg", "-l", "--no-messages", "--hidden", "--no-ignore", "--no-ignore-vcs",
           "-e", "①", "-e", "④", "--glob", "!.git/**",
           "--glob", "!" + rel_out + "/**", "--glob", "!" + rel_meas + "/**",
           "."]
    for ext in exts:
        cmd += ["--iglob", "*" + ext]
    p = subprocess.run(cmd, cwd=LEAD, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=3000)
    files = set()
    for line in p.stdout.splitlines():
        s = line.strip()
        if s.startswith(".\\") or s.startswith("./"):
            s = s[2:]
        if s:
            files.add(s.replace("\\", "/"))
    return sorted(files)


# 主体强信号 pattern
P_PROOF_HDR = re.compile(r"\bproof\s+(?:0x)?([0-9a-f]{6,8})\b", re.I)
P_ENTRY_FIELD = re.compile(r"①[^\n]{0,120}?\bentry\s*=\s*(?:0x)?([0-9a-f]{6,8})\b", re.I)
P_OWNER = re.compile(r"OWNER_DISK[^\n]*\n[^\n]*?\b([0-9a-f]{8})\b", re.I)


def ring_line_starts(text):
    """对每个环标记, 判断是否存在一个『行首首个非空白字符就是该标记』的行。"""
    got = {}
    for line in text.splitlines():
        s = line.lstrip()
        if not s:
            continue
        c = s[0]
        if c in RINGS:
            got[c] = got.get(c, 0) + 1
    return got


def subject_entries(text, rel, eset, smap):
    """提取文件的主体 entry 集合 (强信号)。"""
    subs = set()
    # a. 文件名 hex token
    for m in HEXTOK.finditer(os.path.basename(rel)):
        e = to8(m.group(2), eset, smap)
        if e:
            subs.add(("filename", e))
    # b/c. 内容强信号
    for line in text.splitlines()[:200]:
        for pat, tag in ((P_PROOF_HDR, "proof_hdr"), (P_ENTRY_FIELD, "entry_field")):
            for m in pat.finditer(line):
                e = to8(m.group(1), eset, smap)
                if e:
                    subs.add((tag, e))
    return subs


def analyze(eset, smap, exts, read_limit=8 * 1024 * 1024, max_lines=3000):
    files = list_candidate_files(exts)
    ring_files = []
    dedicated = defaultdict(list)     # entry -> [(rel, sources)]
    multi_subject = []                # 多主体四环文档 (假阳性类)
    line_start_four = []
    loose = defaultdict(set)          # entry -> files (loose: 四环行 + entry 任意出现)
    for rel in files:
        full = os.path.join(LEAD, rel.replace("/", os.sep))
        try:
            with open(full, "r", encoding="utf-8", errors="replace") as fh:
                text = fh.read(read_limit)
        except OSError:
            continue
        cnt = ring_line_starts(text)
        if not all(c in cnt for c in RINGS):
            continue
        line_start_four.append(rel)
        subs = subject_entries(text, rel, eset, smap)
        esubs = sorted({e for _t, e in subs})
        if len(esubs) == 1:
            dedicated[esubs[0]].append((rel, sorted(t for t, e in subs if e == esubs[0])))
        elif len(esubs) > 1:
            multi_subject.append((rel, esubs))
        else:
            # 无强信号主体, 也记录
            multi_subject.append((rel, []))
        ring_files.append(rel)
        # loose: entry 任意出现在文本里
        low = text.lower()
        for e in set(HEXTOK.findall(low)):
            e8 = to8(e[1] if isinstance(e, tuple) else e, eset, smap)
            if e8:
                loose[e8].add(rel)
    return dict(candidate_files=files, ring_files=ring_files,
                line_start_four=line_start_four,
                dedicated={k: v for k, v in dedicated.items()},
                multi_subject=multi_subject,
                loose={k: sorted(v) for k, v in loose.items()})


def main():
    rows, eset = load_entry_set()
    n_eset_orig = len(eset)
    # 11 个已知四环行已修复为 R_OK, 不在 resolve.tsv 的 791 里;
    # 正控必须把它们纳入 entry universe (与执行方 recall2.py 同口径).
    eset_full = set(eset) | set(KNOWN11)
    smap = build_short_map(eset_full)
    z675 = load_675()
    z116 = load_116()
    print(f"[in] resolve entries={n_eset_orig} (+11 known = {len(eset_full)})  "
          f"675={len(z675)}  116={len(z116)}  shortmap={len(smap)}")
    res = analyze(eset_full, smap, PRIMARY_EXT)
    print(f"[in] candidate files (①+④ external, primary ext)={len(res['candidate_files'])}")
    print(f"[ring] 行首四环齐全文件={len(res['line_start_four'])}")
    print(f"[ring] 单一主体四环文档覆盖 entry 数={len(res['dedicated'])}")
    print(f"[ring] 多主体/无主体四环文档={len(res['multi_subject'])}")

    # 正控
    hit = [e for e in KNOWN11 if e in res["dedicated"]]
    print(f"\n[POS CTRL] 11 已知四环行召回 = {len(hit)}/11")
    for e in KNOWN11:
        mark = "HIT " if e in res["dedicated"] else "MISS"
        print(f"    {e} {mark} {[x[0] for x in res['dedicated'].get(e, [])][:2]}")

    # 675 四环回指
    four675 = sorted(set(res["dedicated"]) & set(z675))
    print(f"\n[675] 严格判据下被四环文档点名为主体的 675 行数 = {len(four675)}")
    if four675:
        print("    " + ", ".join(four675))
    loose675 = sorted(set(res["loose"]) & set(z675))
    print(f"[675] loose 判据 (四环行+entry任意出现) 命中行数 = {len(loose675)} (假阳性对照)")

    # 反控: 从 MEDIUM 取 3 行确认无四环
    med = sorted(e for e, r in z675.items() if r["bucket"] == "CTX_MEDIUM")
    neg = med[:3]
    print(f"\n[NEG CTRL] CTX_MEDIUM 3 行: {neg}")
    for e in neg:
        print(f"    {e} strict={'YES' if e in res['dedicated'] else 'no'} "
              f"loose={'YES' if e in res['loose'] else 'no'}")

    out = dict(n_entries=len(eset), n_675=len(z675), n_116=len(z116),
               n_candidate_files=len(res["candidate_files"]),
               n_line_start_four=len(res["line_start_four"]),
               pos_ctrl={e: [x[0] for x in res["dedicated"].get(e, [])] for e in KNOWN11},
               pos_ctrl_recall=len(hit),
               dedicated_all={k: v for k, v in res["dedicated"].items()},
               four675=four675, loose675_count=len(loose675),
               neg_ctrl={e: dict(strict=e in res["dedicated"], loose=e in res["loose"]) for e in neg},
               line_start_four_files=res["line_start_four"],
               multi_subject=res["multi_subject"])
    with open(os.path.join(OUT, "_verify_data.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1)
    print(f"\n[out] _verify_data.json")


if __name__ == "__main__":
    main()
