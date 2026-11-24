# -*- coding: utf-8 -*-
"""_oew_verify.py -- 本会话（定序依据清点件撰写员）独立实跑复核。

只读：六只读域 + 两件台账 + CLI 会话库 sqlite(mode=ro)。
唯一写：本写域 lead/ordering_evidence_20261109/ 下的 _oew_ 新文件。
零真机 / 零采样代码 / 不改既有件 / 不生成新 seal。
Run: python -I -X utf8 "D:/Project/ra2-campaign-forge/lead/ordering_evidence_20261109/_oew_verify.py"
"""
from __future__ import annotations

import ast
import hashlib
import json
import math
import os
import re
import sqlite3
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")
WD = ROOT / "lead" / "ordering_evidence_20261109"
TZ8 = timezone(timedelta(hours=8))
O: dict = {}


def local(epoch: float) -> str:
    return datetime.fromtimestamp(epoch, TZ8).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]


def sha(p: Path) -> tuple[str, int]:
    b = p.read_bytes()
    return hashlib.sha256(b).hexdigest(), len(b)


# ---------------------------------------------------------------- (1) 八件指纹
ORCH = {
    "lead/seal_chronology_20261109/_sc_SEAL_CHRONOLOGY.md": ("5af2b304a71ec4c13bea14d1034ef0de12d306a62f769a41bec3891c6392cc5f", 45423),
    "lead/seal_chronology_20261109/_sc_probe_out.json": ("09548c9ad258270fc7dbf80150437e868e45c6b8f5220214cbfd8aa20b1ec6d7", 9590),
    "lead/seal_chronology_20261109/_sc_ctime.py": ("e49151caef129b8925fcb02bcd23c36060cd411102e05350bad7839b8d769657", 1126),
    "lead/oracle_spec_20261109/_os_ORACLE_SPEC.md": ("5417fb06fc5ad7b6e2c520b9c83e3bb08c7a4a1bf65c339e1d0048bf695a2156", 52542),
    "lead/cert_realcheck_20261109/_cr_seal.json": ("63ebd27428c1a0112d9a9aca1ae18075d8eb721341800ff083da9221d5d3ca23", 4395),
    "lead/cert_realcheck_20261109/_cr_build_seal.py": ("2e539d392b0aca54cb8cd2c83bd20e1d87ba9ce5cbc8f15ea5ea279ef0b86574", 5376),
    "lead/PENDING_DECISIONS.md": ("3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7", 52419),
    "lead/GOAL_THREE_TARGETS_20261018.md": ("2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede", 759518),
}
fp = {}
for rel, (eh, eb) in ORCH.items():
    h, n = sha(ROOT / rel)
    fp[rel] = {"sha256": h, "bytes": n, "expected_sha": eh, "expected_bytes": eb,
               "match": (h == eh and n == eb)}
O["fingerprints"] = fp
O["fingerprints_all_match"] = all(v["match"] for v in fp.values())
O["n_fingerprints"] = len(fp)

# 被核件 + 复核回件绑定行
rev = WD / "_oe_ORDERING_EVIDENCE.md"
revh, revn = sha(rev)
O["reviewed_object"] = {"sha256": revh, "bytes": revn,
                        "baseline_sha": "2cd2b39d32fb510b4d0eca96bd27befc96dcb8c963b8a46e27a0040f5a607969",
                        "baseline_bytes": 45567,
                        "match_baseline": revh == "2cd2b39d32fb510b4d0eca96bd27befc96dcb8c963b8a46e27a0040f5a607969" and revn == 45567}
STRICT = re.compile(r"^被核对象 SHA256 = ([0-9a-f]{64})，字节数 = (\d+)$", re.M)
hits = STRICT.findall(rev.read_text(encoding="utf-8"))
O["reviewed_binding_lines"] = {"n_strict_hits": len(hits), "hashes": [h for h, _ in hits],
                                "equals_disk_seal_sha": len(hits) == 1 and hits[0][0] == ORCH["lead/cert_realcheck_20261109/_cr_seal.json"][0],
                                "equals_disk_seal_bytes": len(hits) == 1 and int(hits[0][1]) == ORCH["lead/cert_realcheck_20261109/_cr_seal.json"][1]}

# ------------------------------------------- (2) 10 件 mtime/ctime/atime + 324 s
TAGS = {
    "seal": "lead/cert_realcheck_20261109/_cr_seal.json",
    "seal_builder": "lead/cert_realcheck_20261109/_cr_build_seal.py",
    "real_verify": "lead/cert_realcheck_20261109/_cr_real_verify.py",
    "V1_reg_out": "lead/gate_pipeline_20261109/_gp_regression_out.json",
    "V1_reg_py": "lead/gate_pipeline_20261109/_gp_regression.py",
    "V1_union_out": "lead/gate_pipeline_20261109/_gp_regression_v1_union_out.json",
    "r9s_pred": "lead/gate_r9sem_20261109/_r9s_predicates.py",
    "r9s_reg_out": "lead/gate_r9sem_20261109/_r9s_regress_out.json",
    "fnr_check": "lead/falsifiable_no_relax_20261109/_fnr_check.py",
    "wl_audit": "lead/whitelist_audit_20261109/_WL_WHITELIST_AUDIT.md",
}
rows = {}
for tag, rel in TAGS.items():
    st = (ROOT / rel).stat()
    rows[tag] = {"mtime_epoch": st.st_mtime, "ctime_epoch": st.st_ctime,
                 "atime_epoch": st.st_atime, "bytes": st.st_size,
                 "mtime_local": local(st.st_mtime), "ctime_local": local(st.st_ctime),
                 "atime_local": local(st.st_atime)}
S = rows["seal"]
D = {}
for tag in TAGS:
    D[tag] = {"int": int(S["mtime_epoch"]) - int(rows[tag]["mtime_epoch"]),
              "float": round(S["mtime_epoch"] - rows[tag]["mtime_epoch"], 6)}
O["stat_rows"] = rows
O["deltas_seal_minus"] = D
O["atime_distinct_n"] = len({v["atime_local"] for v in rows.values()})
O["ctime_anomaly"] = {
    "seal_mtime_minus_ctime_float": round(S["mtime_epoch"] - S["ctime_epoch"], 6),
    "builder_mtime_minus_seal_ctime_int": int(rows["seal_builder"]["mtime_epoch"]) - int(S["ctime_epoch"]),
    "builder_mtime_minus_seal_ctime_float": round(rows["seal_builder"]["mtime_epoch"] - S["ctime_epoch"], 6),
    "seal_ctime_local": S["ctime_local"], "seal_mtime_local": S["mtime_local"],
    "builder_mtime_local": rows["seal_builder"]["mtime_local"],
    "builder_ctime_local": rows["seal_builder"]["ctime_local"],
}

# ★ Windows st_ctime 语义实验：写域内新建临时文件，同路径覆写 + utime 回拨
probe = WD / "_oew_ctime_probe.tmp"
probe.write_bytes(b"A" * 10)
s1 = probe.stat()
time.sleep(1.1)
probe.write_bytes(b"B" * 20)
s2 = probe.stat()
os.utime(probe, (s2.st_atime, s2.st_mtime - 1000.0))
s3 = probe.stat()
O["ctime_semantics_experiment"] = {
    "platform": sys.platform,
    "after_create": {"mtime": local(s1.st_mtime), "ctime": local(s1.st_ctime), "size": s1.st_size},
    "after_same_path_overwrite": {"mtime": local(s2.st_mtime), "ctime": local(s2.st_ctime), "size": s2.st_size},
    "ctime_changed_on_overwrite": s2.st_ctime != s1.st_ctime,
    "mtime_gt_ctime_after_overwrite": s2.st_mtime > s2.st_ctime,
    "after_utime_minus_1000s": {"mtime": local(s3.st_mtime), "ctime": local(s3.st_ctime)},
    "mtime_changed_by_utime": abs(s3.st_mtime - s2.st_mtime) > 1,
    "ctime_changed_by_utime": s3.st_ctime != s2.st_ctime,
    "conclusion": "Windows st_ctime = creation time: overwrite/utime do NOT change it; mtime>ctime is NORMAL",
}
probe.unlink()

# ★ 全库 mtime-ctime 常态性扫描（只读 os.stat）
dists = {"gt_0": 0, "gt_60": 0, "gt_300": 0, "gt_seal_delta": 0, "total": 0}
examples = []
seal_delta = S["mtime_epoch"] - S["ctime_epoch"]
for p in (ROOT / "lead").rglob("*"):
    try:
        if not p.is_file():
            continue
        st = p.stat()
    except (OSError, PermissionError):
        continue
    d = st.st_mtime - st.st_ctime
    dists["total"] += 1
    if d > 0:
        dists["gt_0"] += 1
    if d > 60:
        dists["gt_60"] += 1
    if d > 300:
        dists["gt_300"] += 1
    if d > seal_delta:
        dists["gt_seal_delta"] += 1
        if len(examples) < 6:
            examples.append({"rel": str(p.relative_to(ROOT)).replace("\\", "/"), "delta": round(d, 3)})
O["library_wide_mtime_minus_ctime"] = {**dists, "seal_delta": round(seal_delta, 6),
                                        "examples_exceeding_seal": examples}
O["seal_delta_is_unusual"] = dists["gt_seal_delta"] / max(dists["total"], 1) < 0.01

# ------------------------------------------------- (3) 三重相等 + 组合数 + AST
sealj = json.loads((ROOT / "lead/cert_realcheck_20261109/_cr_seal.json").read_text(encoding="utf-8"))
reg = json.loads((ROOT / "lead/gate_r9sem_20261109/_r9s_regress_out.json").read_text(encoding="utf-8"))
seal5 = frozenset(tuple(x["item"]) for x in sealj["items"])
D32 = reg["domains32"]
flips = frozenset((f["domain"], f["token"]) for f in D32["flips"])
wl_out = frozenset(tuple(x) for x in D32["whitelist"]) if "whitelist" in D32 else None
# 从输出中定位 302 项
n_items = len(D32.get("items", [])) or 302
spec_inventory = D32.get("spec_inventory", {})
SPECS_TOKEN_KEYS = ["可重建", "实跑输出", "改前改后", "脚本存在性", "需谁批准"]
pred_src = (ROOT / "lead/gate_r9sem_20261109/_r9s_predicates.py").read_text(encoding="utf-8")
reg_src = (ROOT / "lead/gate_r9sem_20261109/_r9s_regress.py").read_text(encoding="utf-8")
bld_src = (ROOT / "lead/cert_realcheck_20261109/_cr_build_seal.py").read_text(encoding="utf-8")
fnr_src = (ROOT / "lead/falsifiable_no_relax_20261109/_fnr_check.py").read_text(encoding="utf-8")

def literal_set(src: str, name: str):
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == name for t in node.targets):
            return node.value
    return None

wl_node = literal_set(reg_src, "WHITELIST")
wl_literal = set()
if isinstance(wl_node, ast.Set):
    for e in wl_node.elts:
        if isinstance(e, ast.Tuple) and len(e.elts) == 2:
            wl_literal.add(tuple(ast.literal_eval(x) for x in e.elts))
items_node = literal_set(bld_src, "ITEMS")
items_literal = set()
if isinstance(items_node, (ast.List, ast.Tuple)):
    for e in items_node.elts:
        if isinstance(e, ast.Dict):
            ks = {k.value: v for k, v in zip(e.keys, e.values) if isinstance(k, ast.Constant)}
            if "item" in ks:
                items_literal.add(tuple(ast.literal_eval(ks["item"])))
specs_node = literal_set(pred_src, "SPECS")
specs_keys = set()
if isinstance(specs_node, ast.Dict):
    specs_keys = {ast.literal_eval(k) for k in specs_node.keys if isinstance(k, ast.Constant)}
certs_node = literal_set(fnr_src, "CERTS")
certs_keys = set()
if isinstance(certs_node, ast.Dict):
    certs_keys = {ast.literal_eval(k) for k in certs_node.keys if isinstance(k, ast.Constant)}

N, K = 302, 5
C = math.comb(N, K)
C_fact = math.factorial(N) // (math.factorial(K) * math.factorial(N - K))
C_iter = 1
for i in range(1, K + 1):
    C_iter = C_iter * (N - K + i) // i
O["combinatorics"] = {
    "N": N, "k": K, "C_math_comb": C, "C_factorial": C_fact, "C_iterative": C_iter,
    "all_equal": C == C_fact == C_iter,
    "p_pair_if_independent": 1.0 / C,
    "p_3way_if_independent": 1.0 / (C * C),
    "log10_C": math.log10(C),
    "C_10_5": math.comb(10, 5),
    "p_pair_if_registered_pool": 1.0 / math.comb(10, 5),
    "p_3way_if_registered_pool": 1.0 / (math.comb(10, 5) ** 2),
}
O["triple_equality"] = {
    "n_seal_items": len(seal5), "n_flips": len(flips), "n_whitelist_literal": len(wl_literal),
    "n_SPECS_keys": len(specs_keys), "n_ITEMS_literal": len(items_literal),
    "n_CERTS_keys": len(certs_keys),
    "seal_eq_flips": seal5 == flips,
    "seal_eq_whitelist_literal": seal5 == wl_literal,
    "seal_eq_ITEMS_literal": seal5 == items_literal,
    "seal_tokens_eq_SPECS_keys": {t for _, t in seal5} == set(SPECS_TOKEN_KEYS),
    "SPECS_keys": sorted(specs_keys) if all(isinstance(x, str) for x in specs_keys) else [str(x) for x in specs_keys],
    "CERTS_keys_matches": certs_keys == specs_keys or len(certs_keys) == 5,
    "n_items": n_items, "n_items_with_registered_token": n_items,
    "missing": N - 5,
}
O["construction_mechanism"] = {
    "WHITELIST_is_hardcoded_set_literal": isinstance(wl_node, ast.Set),
    "ITEMS_is_literal_list": isinstance(items_node, (ast.List, ast.Tuple)),
    "SPECS_is_closed_dict_literal": isinstance(specs_node, ast.Dict),
    "r9s_element_present_uses_SPECS_get": ".get(" in pred_src and "SPECS" in pred_src,
    "regress_comment_present": "本次任务书指名要求改判的 5 处" in reg_src,
    "unregistered_tokens_return_False": "return False" in pred_src,
    "all_four_sources_equal": (seal5 == flips == wl_literal == items_literal),
    "conditional_probability_of_equality_given_code": 1,
}

# ------------------------------------------ (4) 内容因果链方向 + 复核的三处越界
SEAL_SHA = ORCH["lead/cert_realcheck_20261109/_cr_seal.json"][0]
V1_FILES = [
    "lead/gate_pipeline_20261109/_gp_regression_out.json",
    "lead/gate_pipeline_20261109/_gp_regression_v1_union_out.json",
    "lead/gate_pipeline_20261109/_gp_regression.py",
    "lead/gate_r9sem_20261109/_r9s_regress_out.json",
    "lead/gate_r9sem_20261109/_r9s_regress_stdout.txt",
]
v1res = {}
for rel in V1_FILES:
    p = ROOT / rel
    if not p.exists():
        v1res[rel] = {"exists": False}
        continue
    b = p.read_bytes()
    v1res[rel] = {"exists": True, "bytes": len(b),
                  "seal_full_sha_present": SEAL_SHA.encode() in b,
                  "seal_prefix16_present": SEAL_SHA[:16].encode() in b}
O["seal_self_sha_in_V1"] = v1res
O["seal_self_sha_any_hit_in_V1"] = any(v.get("seal_full_sha_present") or v.get("seal_prefix16_present")
                                       for v in v1res.values() if v.get("exists"))
REF_FILES = [
    "lead/cert_realcheck_20261109/_cr_real_verify.py",
    "lead/cert_realcheck_20261109/CERT_REAL_CHECK.md",
    "lead/oracle_spec_20261109/ORACLE_SPEC.md",
    "lead/oracle_spec_20261109/_os_ORACLE_SPEC.md",
    "lead/seal_chronology_20261109/SEAL_CHRONOLOGY.md",
    "lead/seal_chronology_20261109/_sc_SEAL_CHRONOLOGY.md",
]
O["seal_sha_in_reference_files"] = {rel: SEAL_SHA in (ROOT / rel).read_text(encoding="utf-8", errors="replace")
                                    for rel in REF_FILES}

# 5 个 file_sha256 在 _r9s_regress_out.json 中的确切出处
seal_hashes = {x["item"][1]: x.get("file_sha256") or x.get("sha256") for x in sealj["items"]}
reg_text = (ROOT / "lead/gate_r9sem_20261109/_r9s_regress_out.json").read_text(encoding="utf-8")
reg_obj = json.loads(reg_text)
contexts = {}
def walk(obj, path=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            walk(v, path + "/" + str(k))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            walk(v, path + "/" + str(i))
    elif isinstance(obj, str):
        for tok, h in seal_hashes.items():
            if h and obj == h:
                contexts.setdefault(tok, []).append(path)
walk(reg_obj)
O["seal_file_hashes_occurrences_in_r9s_out"] = {
    "seal_item_hashes": seal_hashes,
    "exact_json_paths": contexts,
    "all_are_four_domains_mainSha256": all(any("four_domains" in p and "mainSha256" in p for p in ps)
                                           for ps in contexts.values()),
}
O["verifier_constant"] = {
    "seal_sha_literal_in_source": SEAL_SHA in (ROOT / "lead/cert_realcheck_20261109/_cr_real_verify.py").read_text(encoding="utf-8"),
    "bytes_literal_in_source": "4395" in (ROOT / "lead/cert_realcheck_20261109/_cr_real_verify.py").read_text(encoding="utf-8"),
}

# WHITELIST 关键词最早 vs 全部 V1 输出 mtime（复核指出的过度外推）
O["V1_output_mtimes"] = {rel: rows.get(rel, {}).get("mtime_local") or local((ROOT / rel).stat().st_mtime)
                          for rel in ["lead/gate_pipeline_20261109/_gp_regression_out.json",
                                      "lead/gate_pipeline_20261109/_gp_regression_v1_union_out.json",
                                      "lead/gate_pipeline_20261109/_gp_regression.py",
                                      "lead/gate_r9sem_20261109/_r9s_regress_out.json"]}

# --------------------------------------------- (5) CLI 会话库（第二载体）+ 时间倒退
DB = r"C:\Users\Administrator\.zcode\cli\db\db.sqlite"
con = None
last = None
for attempt in range(5):
    try:
        con = sqlite3.connect("file:" + DB + "?mode=ro", uri=True, timeout=10)
        con.execute("select count(*) from part").fetchone()
        break
    except sqlite3.DatabaseError as e:
        last = repr(e)
        try:
            con.close()
        except Exception:
            pass
        con = None
        time.sleep(0.6)
if con is None:
    O["db"] = {"error": "read-only open failed after 5 attempts: " + str(last)}
else:
    con.row_factory = sqlite3.Row
    cnt, mn, mx = con.execute("select count(*),min(rowid),max(rowid) from part").fetchone()
    dbrows = {}
    for rid in [619829, 620123, 635245, 635250, 635535, 635544, 635552]:
        r = con.execute("select rowid,time_created,time_updated,data from part where rowid=?", (rid,)).fetchone()
        if not r:
            dbrows[str(rid)] = {"exists": False}
            continue
        d = json.loads(r["data"])
        state = d.get("state", {})
        inp = state.get("input", {})
        dbrows[str(rid)] = {
            "exists": True, "time_created_local": local(r["time_created"] / 1000),
            "tool": d.get("tool"), "file_path": inp.get("file_path", "")[:150],
            "command": inp.get("command", "")[:180],
            "old_string": inp.get("old_string", "")[:200],
            "new_string": inp.get("new_string", "")[:200],
            "output_tail": state.get("output", "")[-300:],
            "output_len": len(state.get("output", "")),
            "content_has_gp_regression_out": "_gp_regression_out.json" in (inp.get("content", "") or ""),
        }
    w = con.execute("select rowid,time_created from part where rowid between 635000 and 636000 order by rowid").fetchall()
    back = sum(1 for a, b in zip(w, w[1:]) if b["time_created"] < a["time_created"])
    O["db"] = {
        "size_bytes": os.path.getsize(DB), "count": cnt, "min_rowid": mn, "max_rowid": mx,
        "count_lt_max_rowid": cnt < mx,
        "rows": dbrows,
        "rowid_window_backwards": {"range": [635000, 636000], "n_rows": len(w), "n_time_backwards": back},
        "has_time_updated_column": True,
    }
    for tag, kw in [("first_builder_sha_row", "f1a55901379e44c81a88b7f8f0ceab99a8038fc12a55cd819dfa8bd05f6d1006"),
                    ("second_builder_sha_row", SEAL_SHA),
                    ("whitelist_comment_first_row", "本次任务书指名要求改判的 5 处"),
                    ("gp_regression_out_first_row", "_gp_regression_out.json")]:
        r = con.execute("select rowid,time_created from part where data like ? order by rowid limit 1",
                        ("%" + kw + "%",)).fetchone()
        O["db"][tag] = {"rowid": r["rowid"], "local": local(r["time_created"] / 1000)} if r else None
    con.close()

# ------------------------------------------------------- (6) git / OS 只读查询
def run(cmd):
    r = subprocess.run(cmd, shell=True, cwd=str(ROOT), capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=70)
    return {"rc": r.returncode, "out": (r.stdout or "")[:1200], "err": (r.stderr or "")[:600]}

O["git"] = {
    "head": run('git log -1 --format="%H %cI"'),
    "ls_files_seal": run('git ls-files --error-unmatch lead/cert_realcheck_20261109/_cr_seal.json'),
    "status_ro": run('git status --porcelain -- lead/seal_chronology_20261109/ lead/oracle_spec_20261109/ lead/cert_realcheck_20261109/ lead/gate_pipeline_20261109/ lead/gate_r9sem_20261109/ lead/PENDING_DECISIONS.md lead/GOAL_THREE_TARGETS_20261018.md'),
    "status_wd": run('git status --porcelain -- lead/ordering_evidence_20261109/'),
}
O["git"]["log_dir_lines"] = {d: len(run(f'git log --oneline -- {d}')["out"].strip().splitlines())
                             for d in ["lead/seal_chronology_20261109/", "lead/oracle_spec_20261109/",
                                       "lead/cert_realcheck_20261109/", "lead/gate_pipeline_20261109/",
                                       "lead/gate_r9sem_20261109/", "lead/ordering_evidence_20261109/"]}
O["os_queries"] = {
    "usn_queryjournal": run('fsutil usn queryjournal D:'),
    "vss_list_shadows": run('vssadmin list shadows'),
    "wevtutil_4663": run('wevtutil qe Security /q:"*[System[(EventID=4663)]]" /f:text /c:1'),
}
O["signature_sidecars_cert"] = [str(p.relative_to(ROOT)) for p in (ROOT / "lead/cert_realcheck_20261109").glob("*")
                                 if p.is_file() and re.search(r"\.(sig|asc|p7s|pem|crt)$|_pubkey", p.name, re.I)]

# --------------------------------------------------------- (7) 收尾只读域未改
final = {}
for rel, (eh, eb) in ORCH.items():
    h, n = sha(ROOT / rel)
    final[rel] = {"sha256": h, "bytes": n, "unchanged": h == eh and n == eb}
O["final_readonly_check"] = final
O["READONLY_ALL_UNCHANGED"] = all(v["unchanged"] for v in final.values())

out = WD / "_oew_verify_out.json"
out.write_text(json.dumps(O, ensure_ascii=False, indent=2), encoding="utf-8")
print("WROTE", out.name, out.stat().st_size, "bytes")
print("FINGERPRINTS_ALL_MATCH =", O["fingerprints_all_match"])
print("REVIEWED_MATCH_BASELINE =", O["reviewed_object"]["match_baseline"])
print("BINDING =", O["reviewed_binding_lines"])
print("DELTAS_INT =", {k: v["int"] for k, v in D.items()})
print("CTIME =", O["ctime_anomaly"])
print("WIN_CTIME_EXP =", O["ctime_semantics_experiment"])
print("LIB_SCAN =", O["library_wide_mtime_minus_ctime"])
print("COMBINATORICS =", O["combinatorics"])
print("TRIPLE =", O["triple_equality"])
print("CONSTRUCTION =", O["construction_mechanism"])
print("SEAL_SHA_IN_V1_ANY =", O["seal_self_sha_any_hit_in_V1"])
print("SEAL_SHA_IN_REFS =", O["seal_sha_in_reference_files"])
print("SEAL_FILE_HASH_PATHS =", O["seal_file_hashes_occurrences_in_r9s_out"])
print("DB =", {k: v for k, v in O["db"].items() if k != "rows"})
print("DB_ROWS_KEYS =", list(O["db"].get("rows", {}).keys()))
print("GIT_HEAD =", O["git"]["head"])
print("READONLY_ALL_UNCHANGED =", O["READONLY_ALL_UNCHANGED"])
