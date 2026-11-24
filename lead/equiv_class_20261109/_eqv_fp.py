# _eqv_fp.py — 复核员①独立实算指纹（只读，零写盘到被核件）
# 约束: python -I -X utf8 本文件(绝对路径)；hashlib 逐块读；不修改任何被核件
import hashlib, os, sys

BASE = "D:/Project/ra2-campaign-forge"

FILES = [
    # 编排方基线 10 件
    "lead/samedoc_link_20261109/SAMEDOC_LINK.md",
    "lead/samedoc_link_20261109/_sl_link.py",
    "lead/samedoc_link_20261109/_sl_run10_out.json",
    "lead/f2d_rootcause_20261109/F2D_ROOT_CAUSE.md",
    "lead/r11_f2_fix_20261109/_f2_r11plus.py",
    "lead/gate_fp7_20261108/_g7_predicates.py",
    "lead/b2b_isolated_20261107/_integ_INTEGRATION_REPORT.md",
    "lead/b2b_isolated_20261107/qc151_trip.isolated.py",
    "lead/PENDING_DECISIONS.md",
    "lead/GOAL_THREE_TARGETS_20261018.md",
    # 被核对象
    "lead/equiv_class_20261109/_eq_criteria.md",
    # 撰写人写域件（§6 声明的指纹）
    "lead/equiv_class_20261109/_eq_proto.py",
    "lead/equiv_class_20261109/_eq_proto_out.json",
    "lead/equiv_class_20261109/_eq_surface_probe.py",
    # 条3 两路径
    "lead/b2b_candidate_lf_20261107/qc151_trip.candidate_lf.py",
    "lead/b2b_isolated_20261107/qc151_trip.isolated.py",
    # 反例件
    "lead/b2b_candidate_review_20261106/TASK.md",
    "lead/b2b_candidate_review2_20261106/TASK.md",
]

EXPECT = {
    "lead/samedoc_link_20261109/SAMEDOC_LINK.md": ("7e55c03861ea5eeff0adf9c02f74e2286134af2c52e507eae2216921d5b9b340", 27995),
    "lead/samedoc_link_20261109/_sl_link.py": ("a4ae4dc1d87d1ed052c4480883b207db9f70d6ca4868960e467bef17ed3cd7a5", 12475),
    "lead/samedoc_link_20261109/_sl_run10_out.json": ("ed031e01e90e004dab43552085f5f6e5b5d184e7d1efa6f5699d6f76b5da454c", 36749),
    "lead/f2d_rootcause_20261109/F2D_ROOT_CAUSE.md": ("d789c9f64d1c0586075bec3d62b2a544e2adf4ed3282bf391a21e3f9218fa0f1", 32939),
    "lead/r11_f2_fix_20261109/_f2_r11plus.py": ("83f8217fb9a194befdd389f0fd9e699660d3240f0cf1eec365cc3d612fdf8f75", 15723),
    "lead/gate_fp7_20261108/_g7_predicates.py": ("02c17e49764a6f87f2b0d26c6689f0cbeb96498509e5c75bf843104829c51120", 11743),
    "lead/b2b_isolated_20261107/_integ_INTEGRATION_REPORT.md": ("9742f2cc2d7e5657799b7db4ab9d73b1b076a2a29f6701591b2431d141506334", 15179),
    "lead/b2b_isolated_20261107/qc151_trip.isolated.py": ("ca23c116064b25a61d6072f93458673990b0bf766b2430524f1980addd3c76d2", 412759),
    "lead/PENDING_DECISIONS.md": ("3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7", 52419),
    "lead/GOAL_THREE_TARGETS_20261018.md": ("2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede", 759518),
    "lead/equiv_class_20261109/_eq_criteria.md": ("30355f3764242e6ad684db8ccb5c11d20fd42a8ad24d3cbf0ae7f0640f0e9a64", 19143),
    "lead/equiv_class_20261109/_eq_proto.py": ("dcb01858955f9b236f0a430430f8172bd5539a82b0aeb7014932c42c4fda4458", 7645),
    "lead/equiv_class_20261109/_eq_proto_out.json": ("c5e19d798c46ee53e5fccafbb1e082ed38f22d1aaa508061d6e617c6d30959f7", 7519),
}

def fp(p):
    h = hashlib.sha256(); n = 0
    with open(p, "rb") as fh:
        while True:
            b = fh.read(1 << 20)
            if not b:
                break
            h.update(b); n += len(b)
    return h.hexdigest(), n

for rel in FILES:
    p = os.path.join(BASE, rel)
    try:
        hexd, n = fp(p)
    except OSError as e:
        print("MISSING", rel, e)
        continue
    mark = ""
    if rel in EXPECT:
        eh, en = EXPECT[rel]
        mark = "  BASELINE_OK" if (hexd == eh and n == en) else f"  BASELINE_MISMATCH(exp {eh[:16]}…/{en})"
    print(f"{hexd} {n:>8} {rel}{mark}")

# 条3 两件逐字节比较
a = os.path.join(BASE, "lead/b2b_isolated_20261107/qc151_trip.isolated.py")
b = os.path.join(BASE, "lead/b2b_candidate_lf_20261107/qc151_trip.candidate_lf.py")
identical = open(a, "rb").read() == open(b, "rb").read()
print("byte_identical(isolated vs candidate_lf) =", identical)

# 反例② 两轮 TASK.md 比较
a2 = os.path.join(BASE, "lead/b2b_candidate_review_20261106/TASK.md")
b2 = os.path.join(BASE, "lead/b2b_candidate_review2_20261106/TASK.md")
ha, na = fp(a2); hb, nb = fp(b2)
print("review TASK.md  ", ha, na)
print("review2 TASK.md ", hb, nb, "identical=", (ha == hb and na == nb))
