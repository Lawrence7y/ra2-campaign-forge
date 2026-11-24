# -*- coding: utf-8 -*-
# _eqv_diffrows.py — 45 行清点中两检测器判定不一致的行，逐行取双方判定+旗标（只读）
import importlib.util, json, pathlib, sys
sys.path.insert(0, r"D:/Project/ra2-campaign-forge/lead/eqdecl_gate_20261109")

HERE = pathlib.Path(r"D:/Project/ra2-campaign-forge/lead/eqdecl_gate_20261109")
ROOT = pathlib.Path(r"D:/Project/ra2-campaign-forge")

spec = importlib.util.spec_from_file_location("_eq_detector_theirs", HERE / "_eq_detector.py")
eq = importlib.util.module_from_spec(spec)
spec.loader.exec_module(eq)

import _eqv_detector as mine

fl = json.loads((HERE / "_eq_full_out.json").read_text(encoding="utf-8"))
theirs = {}
for d in fl["per_file_full"]:
    for x in d["findings"]:
        theirs[(d["file"], x["line"])] = f"{x['verdict']}/{x['failure_type']}"

ROWS = [
    ("lead/layer_identity_20261109/LAYER_IDENTITY.md", [13, 52, 223, 228, 242, 337, 338, 400]),
    ("lead/score_decomp_20261109/SCORE_DECOMP.md", [135, 239]),
    ("lead/comparability_20261109/COMPARABILITY_AUDIT.md", [158]),
]
for rel, lns in ROWS:
    rec = mine.scan(ROOT / rel)
    m = {r["line"]: r for r in rec["recs"]}
    # 他们的全量记录也要 passes/skips 桶 —— full_out per_file_full 只有 findings+skips[:20]
    # ⇒ 内存重算他们的 scan_file 拿全桶
    trec = eq.scan_file(ROOT / rel)
    tmap = {}
    for b in ("findings", "passes", "tautology_ok", "skips", "undecidables"):
        for x in trec[b]:
            tmap[x["line"]] = f"{x['verdict']}/{x['failure_type'] or '-'}[{b}]"
    for n in lns:
        mine_r = m.get(n)
        mv = f"{mine_r['verdict']}/{mine_r['failure_type'] or '-'}" if mine_r else "NOT_ANCHOR"
        mf = {k: v for k, v in (mine_r["flags"].items() if mine_r else [])
              if k in ("intens_line", "univ_line", "obs_line", "scope_line", "taut_line",
                       "struct_line", "seteq_line", "iff_line", "quest_line", "negassert_line")}
        print(f"{rel}:{n}")
        print(f"  theirs: {tmap.get(n, 'NOT_ANCHOR')}")
        print(f"  mine  : {mv}  flags={json.dumps(mf, ensure_ascii=False)}")
        print(f"  text  : {mine_r['text'][:110] if mine_r else ''}")
