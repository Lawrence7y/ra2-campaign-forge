# -*- coding: utf-8 -*-
"""_re_fp_check.py — J4 并入前只读件指纹基线核验。只读+stdout，零写盘。
编排方实跑指纹（任务件给出的基线）逐一对账；DRIFT 行=与基线不符。"""
import hashlib
import os

ROOT = r"D:\Project\ra2-campaign-forge"
EXPECT = {
    r"lead\samedoc_link_20261109\_sl_link.py": (
        "a4ae4dc1d87d1ed052c4480883b207db9f70d6ca4868960e467bef17ed3cd7a5", 12475),
    r"lead\samedoc_link_20261109\SAMEDOC_LINK.md": (
        "7e55c03861ea5eeff0adf9c02f74e2286134af2c52e507eae2216921d5b9b340", 27995),
    r"lead\samedoc_link_20261109\_sl_run10_out.json": (
        "ed031e01e90e004dab43552085f5f6e5b5d184e7d1efa6f5699d6f76b5da454c", 36749),
    r"lead\equiv_class_20261109\_eq_criteria.md": (
        "30355f3764242e6ad684db8ccb5c11d20fd42a8ad24d3cbf0ae7f0640f0e9a64", 19143),
    r"lead\equiv_class_20261109\_eq_proto.py": (
        "dcb01858955f9b236f0a430430f8172bd5539a82b0aeb7014932c42c4fda4458", 7645),
    r"lead\equiv_class_20261109\_eq_proto_out.json": (
        "c5e19d798c46ee53e5fccafbb1e082ed38f22d1aaa508061d6e617c6d30959f7", 7519),
    r"lead\f2d_rootcause_20261109\_f2d_ROOTCAUSE.md": (
        "d12efd856c0aebe5dc8a882cb7cbd486154c7bb8602028e83a6f3ef290668b05", 21424),
    r"lead\r11_f2_fix_20261109\_f2_r11plus.py": (
        "83f8217fb9a194befdd389f0fd9e699660d3240f0cf1eec365cc3d612fdf8f75", 15723),
    r"lead\PENDING_DECISIONS.md": (
        "3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7", 52419),
    r"lead\GOAL_THREE_TARGETS_20261018.md": (
        "2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede", 759518),
}
ok = True
for rel, (eh, eb) in EXPECT.items():
    p = os.path.join(ROOT, rel)
    with open(p, "rb") as f:
        b = f.read()
    h = hashlib.sha256(b).hexdigest()
    m = (h == eh and len(b) == eb)
    ok = ok and m
    print(("OK    " if m else "DRIFT "), rel.replace("\\", "/"), h, len(b))
print("ALL_MATCH" if ok else "SOME_DRIFT")
