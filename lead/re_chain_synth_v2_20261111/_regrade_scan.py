# -*- coding: utf-8 -*-
"""_regrade_scan.py — 对 CHAIN_SYNTHESIS.md 做【已证】全表普查（质疑一重定级的证据基础）。
只读：仅读取 lead/re_chain_synthesis_20261111/CHAIN_SYNTHESIS.md 与其引用的证据件。
输出（stdout）：
  1) 全文各标记（已证/未证/未验/未决/未定谳）精确计数与数法；
  2) 16 处【已证】逐条清单：行号 + 环节主题首格 + 证据引用（文件:行）；
  3) 证据引用可达性核验：文件存在、行号范围不越界、并打印引用首行内容节选。
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
LEAD = os.path.join(REPO, "lead")
TARGET = os.path.join(LEAD, "re_chain_synthesis_20261111", "CHAIN_SYNTHESIS.md")

MARKS = ["【已证】", "【未证】", "【未验】", "【未决】", "【未定谳】"]

# 引用形如 dir/file.txt:L13-L15 / file.txt:L11, L113-L115 / file.json:verdict / file.txt:37
# (要求文件名带扩展名，避免把 `HouseClass::Read_INI:0x500B40` 这类 VA 引用误判为文件引用)
REF_RE = re.compile(r"`([A-Za-z0-9_\-./\\]+?\.(?:txt|json|py|md)):([^`]+)`")


def line_count(path):
    with open(path, "rb") as f:
        return sum(1 for _ in f)


def main():
    with open(TARGET, "r", encoding="utf-8") as f:
        lines = f.readlines()

    print("target: %s" % TARGET)
    print("total lines: %d" % len(lines))

    # ---- 1) 标记计数 ----
    counts = {m: 0 for m in MARKS}
    for ln in lines:
        for m in MARKS:
            counts[m] += ln.count(m)
    print("\n== 全文标记精确计数（逐字符子串计数，含表格/清单/mermaid 全部出现） ==")
    for m in MARKS:
        print("  %s : %d" % (m, counts[m]))
    zheng = [(i + 1, ln) for i, ln in enumerate(lines) if "【已证】" in ln]
    print("  数法: 对全文 %d 行逐行 count('【已证】') 求和 = %d；命中行号: %s"
          % (len(lines), counts["【已证】"], ",".join(str(x[0]) for x in zheng)))
    outside = [n for n, _ in zheng if not (66 <= n <= 84)]
    print("  证据表(L66-L84)之外的【已证】: %s" % (outside if outside else "无（全部集中在 §2 逐环证据表）"))

    # ---- 2) 16 条逐条清单（行号 + 主题首格 + 引用） ----
    print("\n== 【已证】逐条清单 ==")
    refs_all = []
    for n, ln in zheng:
        cells = [c.strip() for c in ln.split("|")]
        topic = cells[1].replace("**", "") if len(cells) > 1 else "?"
        refs = []
        for fname, rng in REF_RE.findall(ln):
            for tok in rng.split(","):
                tok = tok.strip()
                if tok:
                    refs.append((fname, tok))
        refs_all.append((n, topic, refs))
        print("  L%-3d | %s | 证据引用: %s" % (
            n, topic[:46], " ; ".join("%s:%s" % r for r in refs) if refs else "(无显式引用)"))

    # ---- 3) 证据引用可达性核验 ----
    print("\n== 证据引用可达性核验 ==")
    cache = {}
    ok = bad = 0
    for n, topic, refs in refs_all:
        for fname, rng in refs:
            path = os.path.join(LEAD, fname.replace("/", os.sep).replace("\\", os.sep))
            if not os.path.isfile(path):
                print("  L%-3d %s:%s -> 文件不存在 [BAD]" % (n, fname, rng))
                bad += 1
                continue
            if path not in cache:
                cache[path] = line_count(path)
            total = cache[path]
            m = re.match(r"L(\d+)(?:-L(\d+))?$", rng)
            if m:
                a = int(m.group(1))
                b = int(m.group(2) or m.group(1))
                if a >= 1 and b <= total:
                    with open(path, "r", encoding="utf-8", errors="replace") as f:
                        first = f.readlines()[a - 1].rstrip()
                    print("  L%-3d %s:%s -> 文件 %d 行, 范围有效 [OK] 首行: %s"
                          % (n, fname, rng, total, first[:80]))
                    ok += 1
                else:
                    print("  L%-3d %s:%s -> 越界(文件仅 %d 行) [BAD]" % (n, fname, rng, total))
                    bad += 1
            else:
                # json 键引用等，仅验证文件存在
                print("  L%-3d %s:%s -> 文件存在(%d 行), 键引用不核行号 [OK*]" % (n, fname, rng, total))
                ok += 1
    print("  核验结果: OK=%d BAD=%d" % (ok, bad))


if __name__ == "__main__":
    main()
