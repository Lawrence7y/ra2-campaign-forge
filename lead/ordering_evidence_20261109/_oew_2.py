# -*- coding: utf-8 -*-
"""_oew_2.py -- 复核收窄项：AST 精确集合、闭合注册表、V1 时序、DB 最早提及、台账自警、USN 超时。

只读六只读域/两件台账/CLI 库；唯一写 = 本写域 _oew_2_out.json。
Run: python -I -X utf8 "D:/Project/ra2-campaign-forge/lead/ordering_evidence_20261109/_oew_2.py"
"""
from __future__ import annotations

import ast
import json
import os
import re
import sqlite3
import subprocess
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")
WD = ROOT / "lead" / "ordering_evidence_20261109"
TZ8 = timezone(timedelta(hours=8))
O: dict = {}


def local(e: float) -> str:
    return datetime.fromtimestamp(e, TZ8).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]


def run(cmd, timeout=70):
    r = subprocess.run(cmd, shell=True, cwd=str(ROOT), capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=timeout)
    return {"rc": r.returncode, "out": (r.stdout or "")[:2500], "err": (r.stderr or "")[:800]}


# ------------------------------------------------ (A) AST 精确集合 + 闭合注册表
def literal(src: str, name: str):
    for node in ast.walk(ast.parse(src)):
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == name for t in node.targets):
            return node.value
    return None

pred = (ROOT / "lead/gate_r9sem_20261109/_r9s_predicates.py").read_text(encoding="utf-8")
regsrc = (ROOT / "lead/gate_r9sem_20261109/_r9s_regress.py").read_text(encoding="utf-8")
bld = (ROOT / "lead/cert_realcheck_20261109/_cr_build_seal.py").read_text(encoding="utf-8")
fnr = (ROOT / "lead/falsifiable_no_relax_20261109/_fnr_check.py").read_text(encoding="utf-8")

def as_pairs(node):
    out = set()
    if isinstance(node, (ast.Dict, ast.Set, ast.List, ast.Tuple)):
        elts = node.keys if isinstance(node, ast.Dict) else node.elts
        for e in elts:
            try:
                v = ast.literal_eval(e)
            except Exception:
                continue
            if isinstance(v, tuple) and len(v) == 2 and all(isinstance(x, str) for x in v):
                out.add(v)
            elif isinstance(v, str):
                out.add(v)
    return out

specs_node = literal(pred, "SPECS")
wl_node = literal(regsrc, "WHITELIST")
items_node = literal(bld, "ITEMS")
certs_node = literal(fnr, "CERTS")
specs_keys = as_pairs(specs_node)
wl_lit = as_pairs(wl_node)
certs_pairs = as_pairs(certs_node)
items_pairs = set()
if isinstance(items_node, (ast.List, ast.Tuple)):
    for e in items_node.elts:
        if isinstance(e, ast.Dict):
            for k, v in zip(e.keys, e.values):
                if isinstance(k, ast.Constant) and k.value == "item":
                    items_pairs.add(tuple(ast.literal_eval(v)))

sealj = json.loads((ROOT / "lead/cert_realcheck_20261109/_cr_seal.json").read_text(encoding="utf-8"))
seal5 = {tuple(x["item"]) for x in sealj["items"]}
reg = json.loads((ROOT / "lead/gate_r9sem_20261109/_r9s_regress_out.json").read_text(encoding="utf-8"))
D = reg["domains32"]
flips = {(f["domain"], f["token"]) for f in D["flips"]}
wl_out = {tuple(x) for x in D["whitelist"]}
spec_inventory = reg["spec_inventory"]
inv_keys = set(spec_inventory.keys()) if isinstance(spec_inventory, dict) else set()

O["AST_sets"] = {
    "n_SPECS_keys": len(specs_keys), "SPECS_keys_is_closed_5_tokens": len(specs_keys) == 5,
    "n_WHITELIST_literal": len(wl_lit), "n_ITEMS_literal": len(items_pairs),
    "n_CERTS_keys": len(certs_pairs),
    "seal_eq_flips": seal5 == flips,
    "seal_eq_whitelist_output": seal5 == wl_out,
    "seal_eq_whitelist_literal": seal5 == wl_lit,
    "seal_eq_ITEMS_literal": seal5 == items_pairs,
    "seal_eq_CERTS_keys": seal5 == certs_pairs,
    "seal_tokens_eq_SPECS_keys": {t for _, t in seal5} == specs_keys,
    "seal_tokens_eq_spec_inventory_keys": {t for _, t in seal5} == inv_keys,
    "flips_all_whitelisted": len(D["flips_outside_whitelist"]) == 0,
    "n_tightens": D["n_tightens"],
    "n_flips": D["n_flips"],
    "n_rows_32": D["n_domains"],
    "spec_inventory_keys": sorted(inv_keys),
    "SPECS_keys": sorted(specs_keys),
    "CERTS_keys": sorted([str(x) for x in certs_pairs]),
}
# 302 项里含已登记 token 的条目数
rows32 = D["rows"]
registered_tokens = {t for _, t in seal5}
n_with_token = sum(1 for r in rows32 for t in registered_tokens if t in str(r.get("elements", "")) + str(r))
O["coverage"] = {"n_rows": len(rows32), "n_items_with_registered_token_approx": n_with_token,
                 "n_items_no_registered_token": 302 - 10, "missing": 297,
                 "note": "302 = 32 域元素全集；含已登记 token 的 (domain,token) 对仅 10 个，见 _scv_sets_out.json"}

# ------------------------------------------- (B) 白名单早于「全部 V1 输出」?
v1_paths = [
    "lead/gate_pipeline_20261109/_gp_regression_v1_union_out.json",
    "lead/gate_pipeline_20261109/_gp_regression.py",
    "lead/gate_pipeline_20261109/_gp_regression_out.json",
    "lead/gate_r9sem_20261109/_r9s_regress_out.json",
]
v1_mtimes = {p: {"mtime_local": local((ROOT / p).stat().st_mtime),
                 "epoch": (ROOT / p).stat().st_mtime} for p in v1_paths}
wl_comment_epoch = 1794200178016 / 1000  # rowid 620123 / 12:56:18.016
O["whitelist_vs_V1"] = {
    "whitelist_comment_first_row": {"rowid": 620123, "local": local(wl_comment_epoch)},
    "V1_mtimes": {k: v["mtime_local"] for k, v in v1_mtimes.items()},
    "earliest_v1_mtime": min(v["mtime_local"] for v in v1_mtimes.values()),
    "whitelist_after_earliest_v1": wl_comment_epoch > min(v["epoch"] for v in v1_mtimes.values()),
    "claim_whitelist_before_ALL_V1_outputs_is_literally_false": wl_comment_epoch > min(v["epoch"] for v in v1_mtimes.values()),
}

# ------------------------------------- (C) DB 五个 token 最早提及 + 内容早于 V1
DB = r"C:\Users\Administrator\.zcode\cli\db\db.sqlite"
con = None
for _ in range(5):
    try:
        con = sqlite3.connect("file:" + DB + "?mode=ro", uri=True, timeout=10)
        con.execute("select count(*) from part").fetchone()
        break
    except sqlite3.DatabaseError as e:
        try:
            con.close()
        except Exception:
            pass
        con = None
        time.sleep(0.6)
if con is None:
    O["db_tokens"] = {"error": "read-only open failed"}
else:
    con.row_factory = sqlite3.Row
    toks = {}
    for t in ["可重建", "实跑输出", "改前改后", "脚本存在性", "需谁批准"]:
        r = con.execute("select rowid,time_created from part where data like ? order by rowid limit 1",
                        ("%" + t + "%",)).fetchone()
        toks[t] = {"rowid": r["rowid"], "local": local(r["time_created"] / 1000)} if r else None
    O["db_tokens"] = toks
    # 635250 / 635544 完整 stdout 尾 + 635552 old->new
    for rid in [635250, 635544, 635552]:
        r = con.execute("select time_created,data from part where rowid=?", (rid,)).fetchone()
        d = json.loads(r["data"])
        st = d.get("state", {})
        inp = st.get("input", {})
        O.setdefault("db_rows_detail", {})[str(rid)] = {
            "local": local(r["time_created"] / 1000), "tool": d.get("tool"),
            "old_string": inp.get("old_string", "")[:400],
            "new_string": inp.get("new_string", "")[:400],
            "output_tail": st.get("output", "")[-420:],
            "output_len": len(st.get("output", "")),
        }
    con.close()

# ------------------------------------------- (D) 台账自警行 + 判不了清单来源
ledger = (ROOT / "lead/GOAL_THREE_TARGETS_20261018.md").read_text(encoding="utf-8", errors="replace").splitlines()
keys = ["mtime 不自动等于", "纯 mtime", "mtime 旁证", "吻合不等于", "test_06_rewritten_same_content", "test_10_run_start_anchor"]
hits = {}
for i, line in enumerate(ledger):
    for k in keys:
        if k in line:
            hits.setdefault(k, []).append((i + 1, line[:190]))
O["ledger_selfwarnings"] = hits

# ------------------------------------------- (E) USN readjournal 超时（点名命令）
O["usn_readjournal_pipe"] = run('timeout 45 sh -c \'fsutil usn readjournal D: 2>/dev/null | grep -a -i -m 12 "_cr_seal|_cr_build_seal"\'', timeout=60)
O["git_ls_files_seal"] = run('git ls-files --error-unmatch lead/cert_realcheck_20261109/_cr_seal.json')

# ------------------------------------------- (F) atime 被自身读盘污染（再验一次）
p = ROOT / "lead/seal_chronology_20261109/_sc_ctime.py"
a1 = p.stat().st_atime
p.read_bytes()
a2 = p.stat().st_atime
O["atime_drift"] = {"file": "_sc_ctime.py", "atime_before": local(a1), "atime_after_one_read": local(a2),
                    "changed_by_our_own_read": a2 != a1, "delta_s": round(a2 - a1, 6)}

out = WD / "_oew_2_out.json"
out.write_text(json.dumps(O, ensure_ascii=False, indent=2), encoding="utf-8")
print("WROTE", out.name, out.stat().st_size)
for k in ["AST_sets", "coverage", "whitelist_vs_V1", "db_tokens", "ledger_selfwarnings",
          "usn_readjournal_pipe", "git_ls_files_seal", "atime_drift"]:
    print("===", k, "===")
    print(json.dumps(O[k], ensure_ascii=False, indent=1)[:1800])
print("=== db_rows_detail ===")
print(json.dumps(O.get("db_rows_detail", {}), ensure_ascii=False, indent=1)[:2200])
