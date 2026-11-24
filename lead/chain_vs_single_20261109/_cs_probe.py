# -*- coding: utf-8 -*-
# _cs_probe.py : 只读指纹复核 + 两份回归 JSON 结构勘察
# 零真机 / 零采样代码 / 绝对只读证据件
import os, sys, hashlib, json, glob

ROOT = r"D:\Project\ra2-campaign-forge"
os.chdir(ROOT)

def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest(), os.path.getsize(p)

# 编排方指纹表（来自任务正文）
FPS = {
    "lead/gate_pipeline_20261109/_gp_regression_out.json": ("d3543657aa4f9914c9023710f6daef8348a12ca0aa11957110e8b7c45baec6fe", 38575),
    "lead/gate_pipeline_20261109/_gp_regression_v1_union_out.json": ("68c7ecd3aafc94be87092bf65f1e3d05ab28cc5a20de5193117f994882e16358", 37461),
    "lead/gate_pipeline_20261109/_gp_pipeline.py": ("25c7753f097b8e98e1abb424419e42780bc1ed94fed4a674c142be6c6c1625a7", 15811),
    "lead/gate_pipeline_20261109/_gp_DESIGN.md": ("412e816fb0ad75618c91ac40806f11cd2919195f2eba5300c469862a65f840bc", 39058),
    "lead/gate_v1v2_20261109/_v12_rule.py": ("15e4211ffe8397027757aa4d0fb9b9cc5dc41126a08024b9f6cb5bbd8be4a1c0", 9148),
    "lead/gate_fp7_20261108/_g7_predicates.py": ("02c17e49764a6f87f2b0d26c6689f0cbeb96498509e5c75bf843104829c51120", 11743),
    "lead/PENDING_DECISIONS.md": ("3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7", 52419),
    "lead/GOAL_THREE_TARGETS_20261018.md": ("2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede", 759518),
}
# 编排方给的 lead/gate_n13_20261109/_n13_predicates.py 指纹（16649 字节），需在 gate_n13 / gate_fp7 里反查真实文件
SECRET_FP = ("e1195b3b220ad97b5b91b8746a24e332b02ce28085452e947554f99b7f2f3079", 16649)

print("=== [A] 编排方指纹表逐件复核（hashlib.sha256） ===")
for rel, (want_h, want_b) in FPS.items():
    got_h, got_b = sha(rel)
    print("%-62s %s bytes=%d  %s" % (rel, "MATCH" if (got_h == want_h and got_b == want_b) else "MISMATCH", got_b,
                                     "" if got_h == want_h else "got=" + got_h))

print("\n=== [B] 反查 lead/gate_n13_20261109/_n13_predicates.py (16649 B, e1195b...) 的真实文件名 ===")
cands = []
for d in ["lead/gate_n13_20261109", "lead/gate_fp7_20261108", "lead/gate_pipeline_20261109",
          "lead/gate_v1v2_20261109", "lead/gate_r9r12_20261109"]:
    for p in glob.glob(d + "/*"):
        if os.path.isfile(p):
            try:
                h, b = sha(p)
            except Exception:
                continue
            if h == SECRET_FP[0] or b == SECRET_FP[1]:
                cands.append((p, h, b, h == SECRET_FP[0]))
for p, h, b, ok in cands:
    print("  candidate %s  sha=%s bytes=%d match=%s" % (p, h, b, ok))
if not cands:
    print("  NO MATCH FOUND")

print("\n=== [C] 两份回归 JSON 顶层结构 ===")
for rel in ["lead/gate_pipeline_20261109/_gp_regression_out.json",
            "lead/gate_pipeline_20261109/_gp_regression_v1_union_out.json"]:
    with open(rel, "r", encoding="utf-8") as f:
        obj = json.load(f)
    print("\n-- %s" % rel)
    print("   type=%s" % type(obj).__name__)
    if isinstance(obj, dict):
        print("   keys=%s" % list(obj.keys()))
        for k, v in obj.items():
            if isinstance(v, list):
                print("     %s : list len=%d" % (k, len(v)))
                if v:
                    print("       first elem type=%s" % type(v[0]).__name__)
                    if isinstance(v[0], dict):
                        print("       first elem keys=%s" % list(v[0].keys()))
            elif isinstance(v, dict):
                print("     %s : dict keys=%s" % (k, list(v.keys())[:20]))
            else:
                print("     %s : %r" % (k, (str(v)[:200])))
    elif isinstance(obj, list):
        print("   len=%d" % len(obj))
        print("   first elem=%r" % (obj[0],))
