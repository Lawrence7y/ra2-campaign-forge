# -*- coding: utf-8 -*-
"""_ec_fp_baseline.py — 逐件复核编排方给出的 15 件基线指纹（sha256 + bytes）。只读，不写任何被检对象。
绑定行格式固定：被核对象 SHA256 = <64hex>，字节数 = <n>
"""
import hashlib
import os
import sys

ROOT = r"D:\Project\ra2-campaign-forge"

EXPECTED = {
    "lead/PENDING_DECISIONS.md": ("3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7", 52419),
    "lead/GOAL_THREE_TARGETS_20261018.md": ("2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede", 759518),
    "lead/const_exit_20261109/CONST_EXIT_CENSUS.md": ("ed3c379fc1021b85a1605c898bee370935e49a9300efe6f6416163f652893f90", 165107),
    "lead/const_exit_20261109/_ce_final_out.json": ("87bd73318897da4bc7d9a0449b92396d258b42294c4e5076e09d9274b6e6d14b", 312187),
    "lead/andk_rerun_20261109/ANDK_RERUN.md": ("9dabbed8c27ccbc7f4fffc2f2dae37211d1cbe19c42c85b3def76abfccda88d5", 61049),
    "lead/andk_rerun_20261109/_ak_summary.json": ("36af304c7f7cfbd111686eb0d9bed642d42b7f7111ec5e422dc471ab253c9c00", 67597),
    "lead/d27_ruling_20261106/check_d27.py": ("3b769d7c64c2725100186439725198dbc134a277914e2cb2e9b0af844fe7671c", 3764),
    "lead/d28_ruling_20261106/check_d28.py": ("5b42a34a40046d7a705776002d7aebe8ffda34248849a75b628d40712d9df268", 4539),
    "lead/d29_ruling_20261106/check_d29.py": ("2a50b09adff555dbce4c5740a2af78b779876cad771b6fdf887ba3c0dc780f14", 3906),
    "lead/d30_ruling_20261106/check_d30.py": ("6cb737963fc62a0e045f51247b4fa57ef190acb0b524da3aa6b7713fd05ee9fd", 3926),
    "lead/re_line_20261105/D21_RULING/_d21_burden5.py": ("7e4091381486663da57fbd2c0ef113bcbc3d6d69352ddf2762a2e891a7ac36ba", 2929),
    "lead/re_line_20261105/V6_V3_REVIEW/_leader_crossframe_check.py": ("2d17264e77251270d506c488760df020b18380023d40d118ce8455b7bd930ae6", 4688),
    "lead/re_line_20261105/_leader/_a7_acf_probe.py": ("e42a79f3c1d1214f8cd7ebf01b92505f095dd7f6db7b1bf2434f3d833f3ac6e5", 5763),
    "lead/re_line_20261105/_leader/_intra_frame_census.py": ("c4e537ab45dc01219e1ccea0f3e61edfdbfcdcd94f39b0ce6c91c567fd7f0eba", 6279),
    "lead/goal1_a8_fix_20261022/VERIFY_A8.py": ("179f3af88fac380437311fe4c52f2d8367733f3b92c8b13ab99cb742d12544a2", 38317),
}


def main():
    print("python:", sys.version.replace("\n", " "))
    bad = 0
    for rel, (want_sha, want_b) in EXPECTED.items():
        p = os.path.join(ROOT, rel.replace("/", os.sep))
        try:
            with open(p, "rb") as f:
                data = f.read()
        except OSError as e:
            print("OPEN_FAIL", rel, repr(e))
            bad += 1
            continue
        sha = hashlib.sha256(data).hexdigest()
        n = len(data)
        ok = (sha == want_sha) and (n == want_b)
        print("被核对象 SHA256 = %s，字节数 = %d" % (sha, n))
        if not ok:
            print("   expect  SHA256 = %s，字节数 = %d" % (want_sha, want_b))
        print("   => %s %s" % ("MATCH" if ok else "MISMATCH", rel))
        if not ok:
            bad += 1
    print("\nTOTAL=%d MISMATCH=%d" % (len(EXPECTED), bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
