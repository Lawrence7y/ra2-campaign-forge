# -*- coding: utf-8 -*-
"""_mc_empirical.py — 用真实 merged rec 实测消费方表达式（只读消费，不改被扫件）。
1) 从 _re_linked.py 载入并调用 link_triple()，在既有 Ffull_merged 夹具上产出一个真实 merged rec；
2) 打印其形状（path/match/tier/members/是否有 verified_path/recomputed/bytes）；
3) 把现盘各消费方的「原样表达式」套到该 rec 上，记录 崩 / 误读 / 正常。
零真机、零采样、不写只读件、不启动进程。
"""
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(r"D:\Project\ra2-campaign-forge")
RE = ROOT / "lead" / "r33e_merge_20261109" / "_re_linked.py"
FIX = ROOT / "lead" / "r33e_merge_20261109" / "_re_fixtures" / "Ffull_merged"

# 载入并入版（只读）
spec = importlib.util.spec_from_file_location("_mc_re_linked", RE)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

# 用既有夹具重建真实 merged 形态
blob = (FIX / "a_one.py").read_bytes()
FH = hashlib.sha256(blob).hexdigest()
NB = len(blob)
text = (FIX / "doc.md").read_text(encoding="utf-8")
problems, warnings, rec = m.link_triple(text, FIX, FH, NB)

print("=== GENUINE MERGED REC (from _re_linked.link_triple on Ffull_merged fixture) ===")
print("verdict(link)   =", m.link(text, FIX, FH, NB)["verdict"])
print("tier            =", rec.get("tier"))
print("match           =", rec.get("match"))
print("path            =", rec.get("path"))
print("keys            =", sorted(rec.keys()))
print("has verified_path =", "verified_path" in rec)
print("has recomputed    =", "recomputed" in rec)
print("has bytes         =", "bytes" in rec)
print("members_n       =", len(rec.get("members") or []))
print("decl_lines      =", rec.get("decl_lines"))
print("problems        =", problems)
print("warnings_n      =", len(warnings))

results = []


def trial(label, fn):
    """执行一个消费方表达式，记录结果。"""
    try:
        out = fn()
        results.append((label, "OK", repr(out)[:140]))
    except Exception as e:
        results.append((label, "EXCEPTION", "%s: %s" % (type(e).__name__, e)))


# ---- 现盘消费方表达式（逐件照抄其关键行） ----

# _f2v_verify9.py:21-29（最危险：match=True ⇒ 走 verified_path/bytes 单对象）
def c_verify9():
    b = rec
    if b.get("match") is not True:
        return "SKIP(match!=True)"
    src = b.get("alt") or b
    vp = Path(src.get("verified_path") or src.get("path"))   # :24
    data = vp.read_bytes()                                     # :25
    size = len(data)
    ok = size == src["bytes"]                                 # :29
    return (str(vp), ok)
trial("A _f2v_verify9.py:21-29 (match⇒verified_path/bytes)", c_verify9)

# 同上但只到 :24（Path(None) 本身）
def c_verify9_p24():
    src = rec.get("alt") or rec
    return Path(src.get("verified_path") or src.get("path"))
trial("A' _f2v_verify9.py:24 only (Path(verified_path or path))", c_verify9_p24)

# _f2_selftest.py:110  .get("verified_path","").endswith
def c_selftest110():
    return rec.get("verified_path", "").endswith("_f2_r11plus.py")
trial("B _f2_selftest.py:110 (.get default '')", c_selftest110)

# _f2v_final.py:54,57-58  path 计数 + match⇒tier 计数
def c_final():
    pb = [rec]
    plus_path = sum(1 for b in pb if b.get("path"))
    tiers = {}
    for b in pb:
        if b.get("match") is True:
            t = b.get("tier")
            tiers[t] = tiers.get(t, 0) + 1
    return {"plus_path": plus_path, "match_count": 1, "tiers": tiers}
trial("C _f2v_final.py:54/57-58 (path 计数 / match⇒tier)", c_final)

# _f2_compare.py:67,69  plus_path / plus_match 计数
def c_compare():
    n_bind = [rec]
    return (sum(1 for b in n_bind if b.get("path")),
            sum(1 for b in n_bind if b.get("match") is True))
trial("D _f2_compare.py:67/69 (plus_path / plus_match)", c_compare)

# _f2v_run.py:49-52  orig_paths 用 ["path"] 直接下标 / plus 用 .get
def c_run():
    return {"plus_paths": [b.get("path") for b in [rec]],
            "plus_match": [b.get("match") for b in [rec]],
            "plus_tiers": [b.get("tier") for b in [rec]]}
trial("E _f2v_run.py:49-52 (.get 列表化)", c_run)

# _f2w_extract.py:26-33 全 .get，报告打印
def c_extract():
    pb = rec
    vp = pb.get("verified_path", "") or ""
    rc = pb.get("recomputed", "") or ""
    return "verified=%s recomputed=%s bytes=%s path=%r" % (
        vp, (rc[:16] + "...") if rc else "-", pb.get("bytes", "-"), pb.get("path"))
trial("F _f2w_extract.py:26-33 (全 .get 报告)", c_extract)

# _g9_gate.py:157-158  reverified 计数 / match 计数
def c_g9():
    bindings = [dict(rec)]
    return (sum(1 for b in bindings if b.get("path")),
            sum(1 for b in bindings if b.get("match") is True))
trial("G _g9_gate.py:157-158 (reverified / n_match)", c_g9)

# _f2_repro.py:49  mine = [(b["declared"], b["path"], b["match"]) ...] 直接下标
def c_repro():
    return [(b["declared"], b["path"], b["match"]) for b in [rec]]
trial("H _f2_repro.py:49 (declared/path/match 直接下标)", c_repro)

# r33e 测试件正确写法：走 members
def c_good_members():
    if rec.get("tier") == "SAMEDOC_LINK_EQ" and rec.get("path") is None:
        return sorted(m["path"] for m in rec.get("members") or [])
    return rec.get("path")
trial("Z GOOD (tier 分支 + 走 members，r33e 测试件写法)", c_good_members)

print("\n=== CONSUMER EXPRESSION TRIALS (real code lines applied to genuine merged rec) ===")
for label, status, detail in results:
    print("[%-9s] %-58s | %s" % (status, label, detail))

# 汇总
crash = [r for r in results if r[1] == "EXCEPTION"]
print("\nCRASH_COUNT=%d / %d" % (len(crash), len(results)))
