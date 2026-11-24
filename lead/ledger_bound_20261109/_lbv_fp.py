# -*- coding: utf-8 -*-
# 独立复核员 hy4 自建指纹核验脚本（不采信编排方脚本/输出）
import os, hashlib, sys

BASE = r"D:\Project\ra2-campaign-forge"

# 编排方基线（11 件）
BASELINE = {
    r"lead\ledger_appendix_20261108\LEDGER_APPENDIX_DRAFT.md": ("724458d9e2fdaab8ba34d6c7f64612e722f62618381768132246a5cbaa155f4e", 45719),
    r"lead\ledger_appendix_20261108\_la_draft1_n9_p6_erratum.md": ("e863b593bf5c29a9f2ce38aca4773b7feacb625f6ac32e33d04b5e9a2bae02e4", 7806),
    r"lead\ledger_appendix_20261108\_la_draft2_o4_necessity.md": ("213fb89819d316e5a74e5acb065cc17cd2845602b9f79a45e5e10b73bb6ae4da", 6714),
    r"lead\ledger_appendix_20261108\_la_draft3_s604_gapdiff.md": ("d5dc8f979503a65573bcf542fdd28dbf43f13e54dcf0d98229106db43b2f24a6", 7703),
    r"lead\ledger_appendix_20261108\_la_draft4_yi_supersede_jia.md": ("bf010e8d22cf70892365cbadf555c8fd3b51291a355e4b49c429dc86c46f892e", 10080),
    r"lead\s604_verdict_entry_20261109\_ve_DRAFT_S609.md": ("058630a1b34a8140ed2b57e796f3d64413e76e0f99a5f7f648fd56347577f9ec", 18980),
    r"lead\s604_verdict_entry_20261109\S604_VERDICT_ENTRY_DRAFT.md": ("1e4ceb37187cd12601ad03cdc02f0cf2ee624d1f6870c03c0e35d84cbcb40cfc", 36097),
    r"lead\s604_refsync_20261109\_rs_REFSYNC_DRAFT.md": ("7477a869f1d8436b7641b3b5ba09dac778ed078228adbabc0469d5665419d572", 33869),
    r"lead\a_class_fix_20261109\_ac_A1A4A5_FIX_DRAFT_20261109.md": ("6c02341b319360e06bc9f1ad096e4c8d5a04ff649c83389e806337c8ead615bc", 23258),
    r"lead\PENDING_DECISIONS.md": ("3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7", 52419),
    r"lead\GOAL_THREE_TARGETS_20261018.md": ("2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede", 759518),
}

def fp(rel):
    p = os.path.join(BASE, rel)
    with open(p, "rb") as f:
        d = f.read()
    return hashlib.sha256(d).hexdigest(), len(d), d

print("=== ① 十一件基线 vs 编排方 ===")
ok = 0
for rel, (esh, eb) in BASELINE.items():
    sh, b, _ = fp(rel)
    m = (sh == esh and b == eb)
    ok += 1 if m else 0
    print(("OK  " if m else "FAIL") + "  " + str(b).rjust(7) + "  " + sh + "  " + rel.split("\\")[-1])
    if not m:
        print("      expect=" + str(eb) + "  " + esh)
print("BASELINE_MATCH = %d/11" % ok)

print()
print("=== 主件 + 产出文件现盘指纹（被核对象） ===")
OUT = [
    r"lead\ledger_bound_20261109\_lb_BOUND_VOLUME.md",
    r"lead\ledger_bound_20261109\_lb_build.py",
    r"lead\ledger_bound_20261109\_lb_fp_out.txt",
    r"lead\ledger_bound_20261109\_lb_VERIFY.md",
    r"lead\ledger_bound_20261109\_lb_verify_print.py",
]
CLAIM = {
    "_lb_BOUND_VOLUME.md": ("7770da46b5c684add476ec286673d70d73f332fb5ac286d07cabcdaadc4eac43", 60272),
    "_lb_build.py": (None, 36779),
    "_lb_fp_out.txt": (None, 2141),
    "_lb_VERIFY.md": (None, 4859),
    "_lb_verify_print.py": (None, 5437),
}
for rel in OUT:
    sh, b, d = fp(rel)
    name = rel.split("\\")[-1]
    esh, eb = CLAIM[name]
    crlf = d.count(b"\r\n")
    lf = d.count(b"\n")
    print("%-26s bytes=%-7d crlf=%-4d lf=%-5d sha=%s" % (name, b, crlf, lf, sh))
    if esh:
        print("    vs claim sha MATCH=" + str(sh == esh) + " bytesMATCH=" + str(b == eb))
    else:
        print("    vs claim bytesMATCH=" + str(b == eb))
