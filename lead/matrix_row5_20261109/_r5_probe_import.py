# -*- coding: utf-8 -*-
"""_r5_ 重叠输入实跑探针：标准 import 协议隔离加载候选真实函数（非 eval/非动态源码拼接），
跑 9 类 pre × 8 类 post 全格矩阵 + 5 项关键格断言。零真机、零采样；只读候选文件。
"""
import importlib.util
import sys

CAND = r"D:\Project\ra2-campaign-forge\lead\b2b_candidate_lf_20261107\qc151_trip.candidate_lf.py"

spec = importlib.util.spec_from_file_location("_r5_cand_mod", CAND)
mod = importlib.util.module_from_spec(spec)
sys.modules["_r5_cand_mod"] = mod
spec.loader.exec_module(mod)   # 标准 import 协议：仅执行模块顶层（常量/def，无 main）
classify = mod.classify_except_freshness
print("FRESHNESS_SNAPSHOT_STATES =", mod.FRESHNESS_SNAPSHOT_STATES)

PRE = {
    "None":         None,
    "empty{}":      {},
    "缺state":       {"sha256": "X", "exists": True},
    "脏值":          {"state": "garbage", "exists": True},
    "显式unknown":   {"state": "unknown", "exists": None, "sha256": None, "mtime_pre": None},
    "absent_conf":  {"state": "absent_confirmed", "exists": False, "size": None,
                     "sha256": None, "mtime_pre": None},
    "present":      {"state": "present", "exists": True, "size": 3,
                     "sha256": "AAA", "mtime_pre": 1000.0},
    "present缺pre_sha": {"state": "present", "exists": True, "size": 3,
                         "sha256": None, "mtime_pre": 1000.0},
    "error":        {"state": "dict state=error", "exists": None, "size": None,
                     "sha256": None, "mtime_pre": None,
                     "error": "OSError: pre-snap boom", "traceback": "tb"},
}
# 上行 error 项 state 值须为 "error"；上表为注释说明，真实值在下方覆盖
PRE["error"] = {"state": "error", "exists": None, "size": None,
                "sha256": None, "mtime_pre": None,
                "error": "OSError: pre-snap boom", "traceback": "tb"}

POST = {
    "read_error":    {"exists": None, "size": None, "sha256": None, "mtime_post": None,
                      "captured_at_iso": "iso", "read_error": "OSError: post-read boom"},
    "无件":          {"exists": False, "size": None, "sha256": None, "mtime_post": None,
                      "captured_at_iso": "iso", "code": None, "read_error": None},
    "在场sha异":      {"exists": True, "size": 3, "sha256": "BBB", "mtime_post": 2000.0,
                       "captured_at_iso": "iso", "read_error": None},
    "在场sha同mt同":  {"exists": True, "size": 3, "sha Triple": None, "mtime_post": 1000.0,
                       "captured_at_iso": "iso", "read_error": None},
}
# 修正 POST 表（避免手误）：完整重建
POST = {
    "read_error":    {"exists": None, "size": None, "sha256": None, "mtime_post": None,
                      "captured_at_iso": "iso", "read_error": "OSError: post-read boom"},
    "无件":          {"exists": False, "size": None, "sha256": None, "mtime_post": None,
                      "captured_at_iso": "iso", "read_error": None},
    "在场sha异":      {"exists": True, "size": 3, "sha256": "BBB", "mtime_post": 2000.0,
                       "captured_at_iso": "iso", "read_error": None},
    "在场sha同mt同":  {"exists": True, "size": 3, "sha256": "AAA", "mtime_post": 1000.0,
                       "captured_at_iso": "iso", "read_error": None},
    "在场sha同mt升":  {"exists": True, "size": 3, "sha256": "AAA", "mtime_post": 1500.0,
                       "captured_at_iso": "iso", "read_error": None},
    "在场sha同mt降":  {"exists": 2 > 1, "size": 3, "sha256": "AAA", "mtime_post": 500.0,
                       "captured_at_iso": "iso", "read_error": None},
    "在场sha同mt缺":  {"exists": True, "size": 3, "sha256": "AAA", "mtime_post": None,
                       "captured_at": "iso", "read_error": None},
    "在场缺post_sha": {"exists": True, "size": 3, "sha256": None, "mtime_post": 2000.0,
                       "captured_at_iso": "iso", "read_error": None},
}

print("\n==== 全格实跑：行=pre 变体，列=post 变体，格=verdict|conf|is_new ====")
print("pre\\post".ljust(20) + "".join(p[:13].ljust(15) for p in POST))
rows = {}
for pn, pv in PRE.items():
    line = pn.ljust(20)
    for qn, qv in POST.items():
        r = classify(pv, qv)
        rows[(pn, qn)] = (r["verdict"], r["confidence"], r["is_new"])
        line += f'{r["verdict"]}|{r["confidence"]}|{r["is_new"]}'.ljust(15)
    print(line)

print("\n==== 关键格断言 ====")
checks = [
    ("C1 pre=None + read_error → post_read_error（R2:53 同输入；码序 :4643<:4648）",
     ("None", "read_error"), ("post_read_error", "none", None)),
    ("C2 pre=absent_confirmed + read_error → post_read_error（:4643<:4657/:4666）",
     ("absent_conf", "read_error"), ("post_read_error", "none", None)),
    ("C3 pre=error + read_error → post_read_error（:4643<:4652；:4 行 condition 未排除此格）",
     ("error", "read_error"), ("post_read_error", "none", None)),
    ("C4 pre=显式unknown + 跑后在 → unknown（:3 行只写「跑后无件」，此格矩阵无行）",
     ("显式unknown", "在场sha异"), ("unknown", "none", None)),
    ("C5 pre=present缺pre_sha + read_error → post_read_error（:4643<:4673；:5/:13 重叠）",
     ("present缺pre_sha", "read_error"), ("post_read_error", "none", None)),
]
allpass = True
for label, key, expect in checks:
    got = rows[key]
    ok = got == expect
    allpass = allpass and ok
    print(("PASS" if ok else "FAIL") + f"  {label}  实测={got}")
print("\nPROBE_ALL_" + ("PASS" if allpass else "FAIL"))
