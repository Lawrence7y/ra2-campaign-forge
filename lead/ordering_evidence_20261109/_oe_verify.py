# -*- coding: utf-8 -*-
"""_oe_verify.py -- 定序依据清点：独立复核时序/元数据/指纹/集合。
零真机、零采样、纯离线只读盘；唯一写 = lead/ordering_evidence_20261109/ 下本件输出。
Run: python -I -X utf8 "D:/Project/ra2-campaign-forge/lead/ordering_evidence_20261109/_oe_verify.py"
"""
import os, sys, json, hashlib, datetime, pathlib

ROOT = pathlib.Path(r"D:\Project\ra2-campaign-forge")
W = ROOT / "lead" / "ordering_evidence_20261109"

# 编排方【编排方实跑指纹】8 件
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

# 10 件时序（编排方【定序依据清点】与 SEAL_CHRONOLOGY.md:68-79）
TIMING = [
 ("seal",          "lead/cert_realcheck_20261109/_cr_seal.json",                    "2026-11-09 18:33:04", 1794220384, 4395),
 ("seal_builder",  "lead/cert_realcheck_20261109/_cr_build_seal.py",               "2026-11-09 18:33:00", 1794220380, 5376),
 ("real_verify",   "lead/cert_realcheck_20261109/_cr_real_verify.py",              "2026-11-09 18:34:15", 1794220455, 21178),
 ("V1_reg_out",    "lead/gate_pipeline_20261109/_gp_regression_out.json",          "2026-11-09 13:53:57", 1794203637, 38575),
 ("V1_reg_py",     "lead/gate_pipeline_20261109/_gp_regression.py",                "2026-11-09 12:52:54", 1794199974, 13017),
 ("V1_union_out",  "lead/gate_pipeline_20261109/_gp_regression_v1_union_out.json", "2026-11-09 12:51:07", 1794199867, 37461),
 ("r9s_pred",      "lead/gate_r9sem_20261109/_r9s_predicates.py",                 "2026-11-09 13:00:28", 1794200428, 23111),
 ("r9s_reg_out",   "lead/gate_r9sem_20261109/_r9s_regress_out.json",              "2026-11-09 14:32:26", 1794205946, 75673),
 ("fnr_check",     "lead/falsifiable_no_relax_20261109/_fnr_check.py",            "2026-11-09 16:11:22", 1794211882, 28811),
 ("wl_audit",      "lead/whitelist_audit_20261109/_WL_WHITELIST_AUDIT.md",        "2026-11-09 15:06:20", 1794207980, 52705),
]

def st(rel):
    p = ROOT / rel
    s = p.stat()
    b = p.read_bytes()
    f = lambda x: datetime.datetime.fromtimestamp(x).strftime("%Y-%m-%d %H:%M:%S")
    return {"mtime": s.st_mtime, "ctime": s.st_ctime, "atime": s.st_atime,
            "mtime_int": int(s.st_mtime), "mtime_local": f(s.st_mtime),
            "ctime_local": f(s.st_ctime), "atime_local": f(s.st_atime),
            "bytes": s.st_size, "sha256": hashlib.sha256(b).hexdigest()}

def hms(sec):
    a = abs(sec); h, r = divmod(int(a), 3600); m, s = divmod(r, 60)
    return ("-" if sec < 0 else "+") + "%dh%dm%ds" % (h, m, s)

out = {"python": sys.version, "root": str(ROOT), "ran_at": datetime.datetime.now().isoformat()}

# (1) 编排方 8 件指纹
out["orch_fingerprints"] = {}
for rel, (sha, nb) in ORCH.items():
    s = st(rel)
    out["orch_fingerprints"][rel] = {"sha256": s["sha256"], "bytes": s["bytes"],
        "sha_match": s["sha256"] == sha, "bytes_match": s["bytes"] == nb}
out["orch_all_match"] = all(v["sha_match"] and v["bytes_match"] for v in out["orch_fingerprints"].values())

# (2) 10 件 mtime/ctime/atime 三元组 + 复现编排方秒差
T = {}
for tag, rel, mstr, ep, nb in TIMING:
    s = st(rel)
    T[tag] = dict(s, rel=rel,
                  mtime_str_match=(s["mtime_local"] == mstr),
                  epoch_match=(s["mtime_int"] == ep),
                  bytes_match=(s["bytes"] == nb))
out["timing"] = T
out["timing_all_match"] = all(v["mtime_str_match"] and v["epoch_match"] and v["bytes_match"] for v in T.values())
seal = T["seal"]
out["deltas_seal_minus"] = {}
for tag in T:
    if tag == "seal": continue
    out["deltas_seal_minus"][tag] = {"int": seal["mtime_int"] - T[tag]["mtime_int"],
        "float": round(seal["mtime"] - T[tag]["mtime"], 6),
        "hms": hms(seal["mtime_int"] - T[tag]["mtime_int"])}
# ctime 异常
out["ctime_anomaly"] = {
    "seal_mtime_local": seal["mtime_local"], "seal_ctime_local": seal["ctime_local"],
    "seal_mtime_minus_ctime_float": round(seal["mtime"] - seal["ctime"], 6),
    "builder_mtime_local": T["seal_builder"]["mtime_local"],
    "builder_ctime_local": T["seal_builder"]["ctime_local"],
    "builder_mtime_minus_seal_ctime_int": T["seal_builder"]["mtime_int"] - int(seal["ctime"]),
    "builder_mtime_minus_seal_ctime_float": round(T["seal_builder"]["mtime"] - seal["ctime"], 6),
    "impossible_under_normal_fs": seal["ctime"] < T["seal_builder"]["mtime"],
}
# atime 漂移
out["atime_values"] = {tag: {"atime_local": v["atime_local"]} for tag, v in T.items()}
out["atime_distinct"] = sorted(set(v["atime_local"] for v in T.values()))

# (3) 三重相等 + 302 覆盖（独立重算，不调用任何既有脚本）
reg = json.loads((ROOT / "lead/gate_r9sem_20261109/_r9s_regress_out.json").read_text(encoding="utf-8"))
sealj = json.loads((ROOT / "lead/cert_realcheck_20261109/_cr_seal.json").read_text(encoding="utf-8"))
D = reg["domains32"]
flips = frozenset((f["domain"], f["token"]) for f in D["flips"])
wl = frozenset(tuple(x) for x in D["whitelist"])
seal5 = frozenset(tuple(i["item"]) for i in sealj["items"])
spec_keys = frozenset(reg["spec_inventory"].keys())
items = []
for r in D["rows"]:
    if r.get("main_missing"): continue
    for e in r["per_element"]: items.append((r["domain"], e["token"]))
I = frozenset(items)
reg_pairs = frozenset(x for x in items if x[1] in spec_keys)
out["sets"] = {
  "n_items": len(items), "distinct": len(I), "n_flips": len(flips), "n_whitelist": len(wl),
  "n_seal": len(seal5), "spec_keys": sorted(spec_keys),
  "seal_eq_flips": seal5 == flips, "seal_eq_whitelist": seal5 == wl,
  "flips_eq_whitelist": flips == wl,
  "seal_tokens_eq_spec_keys": frozenset(t for _, t in seal5) == spec_keys,
  "seal_subset_I": seal5 <= I, "coverage": len(seal5)/len(I), "missing": len(I)-len(seal5),
  "n_items_with_registered_token": len(reg_pairs),
  "n_items_no_registered_token": len(items)-len(reg_pairs),
  "n_distinct_registered_pairs": len(frozenset(reg_pairs)),
  "truth_all_true": all(i["oracle"]["truth"] is True for i in sealj["items"]),
  "n_negatives": sum(1 for i in sealj["items"] if i["oracle"]["truth"] is not True),
  "seal_top_keys": sorted(sealj.keys()),
  "seal_items_sorted": [list(x) for x in sorted(seal5)],
  "flips_sorted": [list(x) for x in sorted(flips)],
  "whitelist_sorted": [list(x) for x in sorted(wl)],
}

# (4) 组合数概率：I 中 302 个不同 (domain,token)，随机取 5 个
from math import comb
C = comb(len(I), 5)
out["combinatorics"] = {
  "N": len(I), "k": len(seal5), "C_N_k": C,
  "p_3way_exact_if_independent": 1.0/(C*C),   # 两个独立 5-子集都等于同一 5-子集
  "p_pair_match": 1.0/C,
  "log10_C": __import__("math").log10(C),
  "C_registered_pairs": len(frozenset(reg_pairs)),
  "comb_registered_5": comb(len(frozenset(reg_pairs)), 5),
  "p_if_pool_is_registered": 1.0/(comb(len(frozenset(reg_pairs)),5)**2),
  "p_single_if_pool_registered": 1.0/comb(len(frozenset(reg_pairs)),5),
}

# (5) 内容因果链：seal 的 sha256 / 各件 sha256 是否出现在其它件里（反向哈希锚定）
allsha = {tag: v["sha256"] for tag, v in T.items()}
allsha.update({k.split("/")[-1]: v["sha256"] for k, v in out["orch_fingerprints"].items()})
targets = [
 "lead/gate_pipeline_20261109/_gp_regression_out.json",
 "lead/gate_pipeline_20261109/_gp_regression_v1_union_out.json",
 "lead/gate_pipeline_20261109/_gp_regression_out.txt",
 "lead/gate_r9sem_20261109/_r9s_regress_out.json",
 "lead/cert_realcheck_20261109/_cr_real_verify.py",
 "lead/cert_realcheck_20261109/_cr_build_seal.py",
 "lead/cert_realcheck_20261109/CERT_REAL_CHECK.md",
 "lead/oracle_spec_20261109/ORACLE_SPEC.md",
 "lead/oracle_spec_20261109/_os_ORACLE_SPEC.md",
 "lead/seal_chronology_20261109/SEAL_CHRONOLOGY.md",
 "lead/seal_chronology_20261109/_sc_SEAL_CHRONOLOGY.md",
 "lead/PENDING_DECISIONS.md",
 "lead/GOAL_THREE_TARGETS_20261018.md",
]
blob = {}
for rel in targets:
    p = ROOT / rel
    if p.is_file(): blob[rel] = p.read_bytes()
out["content_causal"] = {}
for tag, sha in allsha.items():
    hits = [rel for rel, b in blob.items() if sha.encode() in b]
    out["content_causal"][tag] = {"sha256": sha, "appears_in": hits}
# 专门查 seal sha 前缀 16 位
p16 = "63ebd27428c1a011"
out["seal_sha_prefix16_hits"] = [rel for rel, b in blob.items() if p16.encode() in b]

# (6) 目录项顺序：os.scandir 原生顺序 + NTFS 目录项（不解析 MFT，仅登记物理枚举顺序）
out["dir_order_cert"] = [e.name for e in os.scandir(ROOT / "lead/cert_realcheck_20261109")]

# (7) 绑定行复验
import re
pat = re.compile(r"被核对象 SHA256 = ([0-9a-f]{64})，字节数 = (\d+)")
out["binding_check"] = {}
for nm, rel in [("draft","lead/seal_chronology_20261109/_sc_SEAL_CHRONOLOGY.md"),
                ("main","lead/seal_chronology_20261109/SEAL_CHRONOLOGY.md"),
                ("oracle_spec","lead/oracle_spec_20261109/ORACLE_SPEC.md")]:
    txt = (ROOT/rel).read_text(encoding="utf-8")
    hits = pat.findall(txt)
    out["binding_check"][nm] = {"rel": rel, "n_hits": len(hits), "hits": hits,
        "is64hex": all(len(h[0])==64 for h in hits),
        "equals_disk_seal": all(h[0]==seal["sha256"] and int(h[1])==seal["bytes"] for h in hits)}

op = W / "_oe_verify_out.json"
op.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
print("ORCH_ALL_MATCH =", out["orch_all_match"])
print("TIMING_ALL_MATCH =", out["timing_all_match"])
for tag, v in out["deltas_seal_minus"].items():
    print("  seal - %-14s = %+7d s (float %+12.6f)  %s" % (tag, v["int"], v["float"], v["hms"]))
print("CTIME_ANOMALY =", json.dumps(out["ctime_anomaly"], ensure_ascii=False))
print("ATIME distinct =", out["atime_distinct"])
print("SETS =", json.dumps({k:v for k,v in out["sets"].items() if k not in ("seal_items_sorted","flips_sorted","whitelist_sorted")}, ensure_ascii=False))
print("COMBINATORICS =", json.dumps(out["combinatorics"], ensure_ascii=False))
print("SEAL_SHA_PREFIX16_HITS =", out["seal_sha_prefix16_hits"])
for tag, v in out["content_causal"].items():
    if v["appears_in"]: print("  CAUSAL HIT", tag, "->", v["appears_in"])
print("BINDING =", json.dumps(out["binding_check"], ensure_ascii=False))
print("DIR_ORDER_CERT =", out["dir_order_cert"])
print("WROTE", op)
