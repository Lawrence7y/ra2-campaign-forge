# -*- coding: utf-8 -*-
# _fdv_build.py — 复核员沙箱搭建：两件原件字节级副本（copyfile+SHA256 校验）
# 副本只落 _fdv_sandbox/；不修改任何保护件；dont_write_bytecode 防 __pycache__
import sys, os, json, hashlib, shutil
sys.dont_write_bytecode = True

ROOT = r"D:/Project/ra2-campaign-forge"
WD = ROOT + r"/lead/fp_discriminate_20261109"
SB = WD + r"/_fdv_sandbox"
os.makedirs(SB, exist_ok=True)

SRCS = [
    (ROOT + "/lead/dneg_generative_20261109/_dg_core.py",
     "7a8074ef8d85dbc6c64136fc71bb793be1cb3dd8c500245778ce1d6644fe2ae1", 12322,
     SB + "/_fdv_dg_core_base.py"),
    (ROOT + "/lead/gate_fp7_20261108/_g7_predicates.py",
     "02c17e49764a6f87f2b0d26c6689f0cbeb96498509e5c75bf843104829c51120", 11743,
     SB + "/_fdv_g7_base.py"),
]
res = []
for src, exp_sha, exp_n, dst in SRCS:
    b = open(src, "rb").read()
    ok1 = hashlib.sha256(b).hexdigest() == exp_sha and len(b) == exp_n
    shutil.copyfile(src, dst)
    b2 = open(dst, "rb").read()
    ok2 = hashlib.sha256(b2).hexdigest() == exp_sha and len(b2) == exp_n
    print("COPY %s -> %s  原件指纹核验=%s  副本逐字节校验=%s  sha=%s  bytes=%d"
          % (src, dst, ok1, ok2, hashlib.sha256(b2).hexdigest(), len(b2)))
    res.append({"src": src, "dst": dst, "src_ok": ok1, "copy_ok": ok2,
                "sha": hashlib.sha256(b2).hexdigest(), "bytes": len(b2)})
assert all(r["src_ok"] and r["copy_ok"] for r in res), "沙箱副本校验失败"
json.dump(res, open(WD + "/_fdv_build_out.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("written: _fdv_build_out.json")
