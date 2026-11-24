# -*- coding: utf-8 -*-
# S604_REFSYNC_FULL final deliverable support: hashlib fingerprints (read-only).
# Run: python -I -X utf8 D:/Project/ra2-campaign-forge/lead/s604_refsync_full_20261109/_full_fp.py
import hashlib
from pathlib import Path

ROOT = Path("D:/Project/ra2-campaign-forge")

# 编排方基线（任务书【编排方指纹】给值），用于 6/6 MATCH 校验
BASE6 = {
    "lead/s604_verdict_entry_20261109/S604_VERDICT_ENTRY_DRAFT.md": ("1e4ceb37187cd12601ad03cdc02f0cf2ee624d1f6870c03c0e35d84cbcb40cfc", 36097),
    "lead/s604_verdict_entry_20261109/_ve_DRAFT_S609.md": ("058630a1b34a8140ed2b57e796f3d64413e76e0f99a5f7f648fd56347577f9ec", 18980),
    "lead/s604_refsync_20261109/S604_REFSYNC_DRAFT.md": ("cbadcb872c696c7a39af50764ecc0b276d42e9a89afd73caead0a8d703338841", 38819),
    "lead/s604_refsync_20261109/_rs_REFSYNC_DRAFT.md": ("7477a869f1d8436b7641b3b5ba09dac778ed078228adbabc0469d5665419d572", 33869),
    "lead/PENDING_DECISIONS.md": ("3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7", 52419),
    "lead/GOAL_THREE_TARGETS_20261018.md": ("2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede", 759518),
}

# §4.2 的 13 件（严数 43 处载体）
FILES13 = [
    "lead/slowframe_r3_20261108/S604_GAP_RECHECK.md",
    "lead/s604_attribution_20261108/S604_ATTRIBUTION.md",
    "lead/s604_attribution_20261108/_sa_ATTRIBUTION_S604.md",
    "lead/ledger_appendix_20261108/LEDGER_APPENDIX_DRAFT.md",
    "lead/ledger_appendix_20261108/_la_draft3_s604_gapdiff.md",
    "lead/ledger_appendix_20261108/_lad_tpl.md",
    "lead/s604_script_gap_20261109/S604_SCRIPT_GAP.md",
    "lead/s604_script_gap_20261109/_sg_FINDINGS.md",
    "lead/s604_exclusive_20261109/S604_EXCLUSIVITY.md",
    "lead/s604_exclusive_20261109/_ex_EXCLUSIVITY.md",
    "lead/slowwindow_n8_20261108/SLOW_WINDOW_LIMITS.md",
    "lead/direction_ruling_20261108/RULING_DIRECTION.md",
    "lead/direction_ruling_20261108/_dr_RULING.md",
]

# 【补齐】回件 c 段登记的 13 件指纹（前 8 位），用于比对
BASE13 = {
    "lead/slowframe_r3_20261108/S604_GAP_RECHECK.md": ("5d1b0ecc", 19291),
    "lead/s604_attribution_20261108/S604_ATTRIBUTION.md": ("8e9a6067", 27182),
    "lead/s604_attribution_20261108/_sa_ATTRIBUTION_S604.md": ("72410261", 17272),
    "lead/ledger_appendix_20261108/LEDGER_APPENDIX_DRAFT.md": ("724458d9", 45719),
    "lead/ledger_appendix_20261108/_la_draft3_s604_gapdiff.md": ("d5dc8f97", 7703),
    "lead/ledger_appendix_20261108/_lad_tpl.md": ("a2313396", 25723),
    "lead/s604_script_gap_20261109/S604_SCRIPT_GAP.md": ("593c7a3e", 20271),
    "lead/s604_script_gap_20261109/_sg_FINDINGS.md": ("a9f293bb", 10925),
    "lead/s604_exclusive_20261109/S604_EXCLUSIVITY.md": ("82347668", 30536),
    "lead/s604_exclusive_20261109/_ex_EXCLUSIVITY.md": ("1ad890b4", 20623),
    "lead/slowwindow_n8_20261108/SLOW_WINDOW_LIMITS.md": ("e7c29e06", 23707),
    "lead/direction_ruling_20261108/RULING_DIRECTION.md": ("0ebd68dd", 16514),
    "lead/direction_ruling_20261108/_dr_RULING.md": ("c6fa7a0a", 20942),
}


def fp(rel):
    b = (ROOT / rel).read_bytes()
    return hashlib.sha256(b).hexdigest(), len(b)


def main():
    print("=== A 段：编排方基线 6 件（任务书给值 vs 本会话 hashlib 实算） ===")
    ok6 = 0
    for rel, (want_sha, want_sz) in BASE6.items():
        got_sha, got_sz = fp(rel)
        m = (got_sha == want_sha and got_sz == want_sz)
        ok6 += 1 if m else 0
        print(f"{'MATCH' if m else 'MISMATCH'} | {rel} | sha256={got_sha} | bytes={got_sz}")
    print(f"A 段小计: {ok6}/6 MATCH")

    print()
    print("=== B 段：绑定行载体（S604_VERDICT_ENTRY_DRAFT.md） ===")
    sha, sz = fp("lead/s604_verdict_entry_20261109/S604_VERDICT_ENTRY_DRAFT.md")
    print(f"被核对象 SHA256 = {sha}，字节数 = {sz}")

    print()
    print("=== C 段：§4.2 的 13 件指纹（本会话 hashlib 实算） ===")
    ok13 = 0
    for rel in FILES13:
        got_sha, got_sz = fp(rel)
        w8, wsz = BASE13[rel]
        m = (got_sha.startswith(w8) and got_sz == wsz)
        ok13 += 1 if m else 0
        print(f"{'MATCH' if m else 'MISMATCH'} | {rel} | sha256={got_sha} | bytes={got_sz}")
    print(f"C 段小计: {ok13}/13 MATCH（对照【补齐】回件 c 段登记值）")

    print()
    print("=== D 段：三组同文对（按 §4.2 :90 口径）逐字比对 ===")
    pairs = [
        ("LEDGER:215 ≡ _lad_tpl:151", "lead/ledger_appendix_20261108/LEDGER_APPENDIX_DRAFT.md", 215, "lead/ledger_appendix_20261108/_lad_tpl.md", 151),
        ("LEDGER:123 ≡ _la_draft3:25", "lead/ledger_appendix_20261108/LEDGER_APPENDIX_DRAFT.md", 123, "lead/ledger_appendix_20261108/_la_draft3_s604_gapdiff.md", 25),
        ("ATTRIBUTION:136 ≡ _sa:90", "lead/s604_attribution_20261108/S604_ATTRIBUTION.md", 136, "lead/s604_attribution_20261108/_sa_ATTRIBUTION_S604.md", 90),
    ]
    for label, f1, l1, f2, l2 in pairs:
        s1 = (ROOT / f1).read_text(encoding="utf-8").splitlines()[l1 - 1]
        s2 = (ROOT / f2).read_text(encoding="utf-8").splitlines()[l2 - 1]
        print(f"{label} | {'IDENTICAL' if s1 == s2 else 'DIFFERENT'} | L1={s1!r} | L2={s2!r}")


if __name__ == "__main__":
    main()
