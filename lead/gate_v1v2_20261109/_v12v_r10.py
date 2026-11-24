# -*- coding: utf-8 -*-
r"""_v12v_r10.py -- 复核员独立实跑 r10_scan（② + ⑥）。
不采信撰写人 _v12_verify.py / _v12_probe.py 的任何分类表：
  直接从 lead/gate_fp7_20261108/_g7_predicates.py 载入 r10_scan/r10_context/r12_scan，
  对两域全文逐处实跑，另用独立 re.finditer 复算 raw 命中集并按 (pos,token) 对账。
另真 import _g9_gate.check_deliverable 复核生产门禁数字。
零真机、零采样；sys.dont_write_bytecode=True 防止在只读域生成 __pycache__。
"""
import sys
sys.dont_write_bytecode = True
import hashlib
import importlib.util
import json
import re
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")
PRED = ROOT / "lead" / "gate_fp7_20261108" / "_g7_predicates.py"
G9 = ROOT / "lead" / "gate_r9r12_20261109" / "_g9_gate.py"
PRED_SHA = "02c17e49764a6f87f2b0d26c6689f0cbeb96498509e5c75bf843104829c51120"
PRED_BYTES = 11743

DOCS = [
    ("c07_slot_20261109", ROOT / "lead" / "c07_slot_20261109" / "C07_IDENTITY_SLOT.md",
     ["已补登", "已填入", "已填", "已代填"]),
    ("c07_truth_protocol_20261109", ROOT / "lead" / "c07_truth_protocol_20261109" / "C07_TRUTH_SELF_PROOF.md",
     ["已填", "已代填", "已提交"]),
]


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def line_no(text, pos):
    return text.count("\n", 0, pos) + 1


def orig_line(text, pos):
    a = text.rfind("\n", 0, pos) + 1
    b = text.find("\n", pos)
    if b < 0:
        b = len(text)
    return text[a:b]


def main():
    b = PRED.read_bytes()
    print("[PRED-FP] %s sha256=%s bytes=%d MATCH_BASELINE=%s"
          % (PRED.name, hashlib.sha256(b).hexdigest(), len(b),
             hashlib.sha256(b).hexdigest() == PRED_SHA and len(b) == PRED_BYTES))
    g7 = load(PRED, "_v12v_g7")

    total_assertion = 0
    for name, path, bans in DOCS:
        raw_b = path.read_bytes()
        sha = hashlib.sha256(raw_b).hexdigest()
        text = raw_b.decode("utf-8")
        print("\n" + "=" * 96)
        print("[DOC] %s  bytes=%d sha256=%s" % (name, len(raw_b), sha))
        print("[BANS] %r" % (bans,))

        # ---- 独立 raw 命中集（不借 R10） ----
        raw_hits = []
        for tok in bans:
            for m in re.finditer(re.escape(tok), text):
                raw_hits.append((m.start(), tok))
        raw_hits.sort()
        uniq_pos = sorted(set(p for p, _ in raw_hits))
        print("[RAW] 逐 token 字面命中 = %d ; 去重位置 = %d ; 重叠 token 额外计数 = %d"
              % (len(raw_hits), len(uniq_pos), len(raw_hits) - len(uniq_pos)))

        # ---- 直接实跑 r10_scan ----
        problems, warnings, hits = g7.r10_scan(text, bans)
        kinds = {}
        for h in hits:
            kinds[h["kind"]] = kinds.get(h["kind"], 0) + 1
        r12p, r12h = g7.r12_scan(text, bans)
        print("[R10-MINE] problems=%d warnings=%d occurrences=%d kinds=%s"
              % (len(problems), len(warnings), len(hits), json.dumps(kinds, ensure_ascii=False)))
        print("[R12-MINE] problems=%d double_neg_hits=%d" % (len(r12p), len(r12h)))
        for p in problems:
            print("   R10-PROBLEM: " + p)
        for w in warnings:
            print("   R10-WARNING: " + w)

        r10_set = sorted((h["pos"], h["token"]) for h in hits)
        print("[RAW-VS-R10] (pos,token) 集合 IDENTICAL=%s" % (r10_set == raw_hits))

        print("[HITS-MINE] 逐处：行号 / R10 kind / 24 字符窗内否定词 / 原句")
        for h in sorted(hits, key=lambda x: x["pos"]):
            tok, pos = h["token"], h["pos"]
            ctx = g7.r10_context(text, pos, pos + len(tok))
            s = max(0, pos - g7.NEG_WINDOW)
            boundary = max(text.rfind(ch, 0, pos) for ch in g7.CLAUSE_BREAK)
            if boundary > s:
                s = boundary
            pre = text[s:pos]
            negs = g7.NEG_RE.findall(pre)
            print("   L%-4d tok=%-6s pos=%-6d R10=%-13s neg_count=%d neg_words=%r in_span=%s dbl=%s"
                  % (line_no(text, pos), tok, pos, h["kind"], ctx["neg_count"], negs,
                     ctx["in_span"], ctx["dbl"]))
            print("        WINDOW pre = %r" % pre)
            print("        ORIG = %s" % orig_line(text, pos)[:300])
            if h["kind"] == "assertion":
                total_assertion += 1

        # ---- 生产门禁 _g9_gate.check_deliverable（真 import） ----
        g9 = load(G9, "_v12v_g9")
        for label, req in (("empty-req", []), ("nonempty-req", ["填用流程"])):
            r = g9.check_deliverable(str(path), req, bans, old_gate_contrast=False)
            r10 = r["predicates"]["R10"]
            r12 = r["predicates"]["R12"]
            print("[G9-MINE/%s] verdict=%s R9=%s R10=%s R10(items=%d occ=%d kinds=%s problems=%d exempted=%d) R12(double_neg_hits=%d)"
                  % (label, r["verdict"], r["predicates"]["R9"]["verdict"], r10["verdict"],
                     r10["items"], r10["occurrences"], json.dumps(r10["kinds"], ensure_ascii=False),
                     len(r10["problems"]), r10["exempted"], r12["double_neg_hits"]))

    print("\n[TOTAL] R10 assertion problems across both domains = %d" % total_assertion)
    print("[V12V-R10-END]")


if __name__ == "__main__":
    main()
