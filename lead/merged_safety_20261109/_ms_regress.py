# -*- coding: utf-8 -*-
"""_ms_regress.py — 门禁补丁的 30 件回归对照（旧 vs 改后），确认结构/契约不破。

只读取既有件；新写文件均在本写域。零真机、零采样代码；-I -X utf8 -B。
"""
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True
REPO = Path(r"D:\Project\ra2-campaign-forge")
W = REPO / "lead" / "merged_safety_20261109"
G9 = REPO / "lead" / "gate_r9r12_20261109" / "_g9_gate.py"
CAND = W / "_ms_g9_candidate.py"
OUT = []


def say(s=""):
    OUT.append(str(s))
    print(s)


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, str(path))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


OLD = load("_ms_reg_old", G9)
NEW = load("_ms_reg_new", CAND)
j = json.loads((REPO / "lead" / "gate_r9r12_20261109" / "_g9_regression_out.json")
               .read_text(encoding="utf-8"))
REQ = j["checklist"]["required_elements"]
FORB = j["checklist"]["forbidden_words"]
rels = [x["rel"] for x in j["results_30"]]
say("R0 corpus n=%d REQ=%s FORB=%s" % (len(rels), REQ, FORB))

keys_equal = True
r11keys_equal = True
changed = 0
rows = []
for rel in rels:
    p = REPO / rel.replace("/", "\\")
    if not p.is_file():
        say("R1 ABSENT %s (SKIP)" % rel)
        continue
    ro = OLD.check_deliverable(p, REQ, FORB)
    rn = NEW.check_deliverable(p, REQ, FORB)
    keys_equal &= (sorted(ro.keys()) == sorted(rn.keys()))
    r11keys_equal &= (sorted(ro["predicates"]["R11"].keys())
                      == sorted(rn["predicates"]["R11"].keys()))
    same_verdict = ro["verdict"] == rn["verdict"]
    if not same_verdict:
        changed += 1
    rows.append((rel, ro["predicates"]["R11"]["reverified"],
                 ro["predicates"]["R11"]["verdict"], rn["predicates"]["R11"]["verdict"],
                 ro["verdict"], rn["verdict"], same_verdict))

say("R2 top-level keys 全部相同 = %s" % keys_equal)
say("R3 R11 keys 全部相同 = %s" % r11keys_equal)
say("R4 verdict 改变件数 = %d / %d" % (changed, len(rows)))
say("R5 逐件 (rel, reverified, R11 old→new, overall old→new, same):")
for x in rows:
    say("   %-62s rev=%d R11 %s→%s overall %s→%s same=%s" % x)

# 改后模块 self_test 已由 _ms_probe D6.8 验过；此处补 old/new 同一 self_test 对照
co, ao = OLD.self_test()
cn, an = NEW.self_test()
say("R6 self_test old all_pass=%s new all_pass=%s" % (ao, an))

# 指纹：原件未变
raw = G9.read_bytes()
say("R7 _g9_gate.py sha256=%s bytes=%d (与派发值比对)"
    % (hashlib.sha256(raw).hexdigest(), len(raw)))

(W / "_ms_regress_out.txt").write_text("\n".join(OUT) + "\n", encoding="utf-8")
say()
say("WROTE %s" % (W / "_ms_regress_out.txt"))
