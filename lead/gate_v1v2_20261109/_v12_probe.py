# -*- coding: utf-8 -*-
r"""_v12_probe.py -- 独立命中集复核 + R10 否定窗归因（实跑件）。

跑法：python -I -X utf8 D:\Project\ra2-campaign-forge\lead\gate_v1v2_20261109\_v12_probe.py
不采信编排方第二手分类：自己用 re.finditer 全量数词、回算行号、打印 R10 回看窗。
"""
import hashlib
import importlib.util
import re
import sys
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")
DOCS = [
    ("c07_slot_20261109", ROOT / "lead" / "c07_slot_20261109" / "C07_IDENTITY_SLOT.md",
     ["已补登", "已填入", "已填", "已代填"]),
    ("c07_truth_protocol_20261109", ROOT / "lead" / "c07_truth_protocol_20261109" / "C07_TRUTH_SELF_PROOF.md",
     ["已填", "已代填", "已提交"]),
]
PRED = ROOT / "lead" / "gate_fp7_20261108" / "_g7_predicates.py"


def load_pred():
    spec = importlib.util.spec_from_file_location("_g7_predicates_probe", PRED)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def main():
    g7 = load_pred()
    print("=== A. 独立全量命中集（不借 R10，直接 re.finditer + 行号回算） ===")
    all_hits = {}
    for name, path, bans in DOCS:
        text = path.read_bytes().decode("utf-8")
        print("\n[%s] %s bytes=%d sha256=%s" %
              (name, path.name, len(path.read_bytes()), hashlib.sha256(path.read_bytes()).hexdigest()))
        rows = []
        for tok in bans:
            for m in re.finditer(re.escape(tok), text):
                L = text.count("\n", 0, m.start()) + 1
                a = text.rfind("\n", 0, m.start()) + 1
                b = text.find("\n", m.start())
                if b == -1:
                    b = len(text)
                rows.append((m.start(), L, tok, text[a:b]))
        rows.sort()
        for pos, L, tok, line in rows:
            print("  pos=%-6d L%-4d tok=%-6s | %s" % (pos, L, tok, line[:230]))
        print("  TOTAL raw occurrences = %d" % len(rows))
        all_hits[name] = rows

    print("\n=== B. R10 分类逐处回算 + 否定回看窗归因 ===")
    for name, path, bans in DOCS:
        text = path.read_bytes().decode("utf-8")
        probs, warns, hits = g7.r10_scan(text, bans)
        print("\n[%s] R10 problems=%d warnings=%d occurrences=%d" %
              (name, len(probs), len(warns), len(hits)))
        for h in hits:
            pos, tok = h["pos"], h["token"]
            ctx = g7.r10_context(text, pos, pos + len(tok))
            s = max(0, pos - g7.NEG_WINDOW)
            boundary = max(text.rfind(ch, 0, pos) for ch in g7.CLAUSE_BREAK)
            if boundary > s:
                s = boundary
            pre = text[s:pos]
            negs = g7.NEG_RE.findall(pre)
            print("  L%-4d tok=%-6s kind=%-13s neg_count=%d in_span=%s dbl=%s" %
                  (text.count("\n", 0, pos) + 1, tok, h["kind"], ctx["neg_count"],
                   ctx["in_span"], ctx["dbl"]))
            print("     R10 回看窗 pre = %r" % pre)
            print("     R10 窗内否定词 = %r" % negs)

    print("\n=== C. 命中集一致性：R10 occurrences 是否 == 独立 raw occurrences ===")
    for name, path, bans in DOCS:
        text = path.read_bytes().decode("utf-8")
        _, _, hits = g7.r10_scan(text, bans)
        r10set = sorted((h["pos"], h["token"]) for h in hits)
        rawset = sorted((p, t) for p, L, t, _ in all_hits[name])
        print("  %-32s raw=%d r10=%d IDENTICAL=%s" %
              (name, len(rawset), len(r10set), r10set == rawset))

    print("\n=== D. 编排方指纹中标注 MISSING 的路径复核 ===")
    miss = ROOT / "lead" / "c07_truth_protocol_20260909" / "C07_TRUTH_PROTOCOL.md"
    print("  %s exists=%s" % (miss.relative_to(ROOT), miss.is_file()))
    alt = ROOT / "lead" / "c07_truth_protocol_20261109" / "_tp_C07_TRUTH_PROTOCOL.md"
    b = alt.read_bytes()
    print("  同域实际件 %s exists=%s sha256=%s bytes=%d" %
          (alt.relative_to(ROOT), alt.is_file(), hashlib.sha256(b).hexdigest(), len(b)))

    print("\n=== E. 两域是否含任何『硬性完成宣称』词族（V2 候选） ===")
    import importlib.util as iu
    spec = iu.spec_from_file_location("_v12_rule_probe", ROOT / "lead" / "gate_v1v2_20261109" / "_v12_rule.py")
    R = iu.module_from_spec(spec)
    spec.loader.exec_module(R)
    for name, path, bans in DOCS:
        text = path.read_bytes().decode("utf-8")
        found = [k for k in R.V2_OVERRIDE if k in text]
        print("  %-32s V2_OVERRIDE 命中词族 = %r" % (name, found))


if __name__ == "__main__":
    main()
