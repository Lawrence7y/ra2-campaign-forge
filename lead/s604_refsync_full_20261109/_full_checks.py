# -*- coding: utf-8 -*-
# Final deliverable support: precise substring counting + §2.1 registration count + errata spots.
# Run: python -I -X utf8 D:/Project/ra2-campaign-forge/lead/s604_refsync_full_20261109/_full_checks.py
import os
from pathlib import Path

ROOT = Path("D:/Project/ra2-campaign-forge")
LEAD = ROOT / "lead"

TERMS = [
    "三选一不可定谳",
    "三选一**不可定谳**",
    "确切错误机理无法归属",
    "不能定位当年错误步骤",
    "不存在（且从未落盘）",
    "口径不可审计",
    "不臆断标签反转或列索引",
    "「为什么错」零解释",
]


def walk_md():
    out = []
    skipped = []
    for base, dirs, files in os.walk(LEAD):
        try:
            dirs = [d for d in dirs if (Path(base) / d).is_dir()]
        except OSError:
            skipped.append(base)
        for fn in files:
            if fn.lower().endswith((".md", ".py", ".txt", ".json")):
                p = Path(base) / fn
                try:
                    out.append(p)
                except OSError:
                    pass
    return out, skipped


def main():
    paths, skipped = walk_md()
    print(f"scanned files = {len(paths)} | unreadable dirs skipped = {len(skipped)}")
    for s in skipped[:5]:
        print(f"  SKIP {s}")
    print()
    print("=== 精确子串命中（全树 md/py/txt/json，逐文件逐行） ===")
    for term in TERMS:
        hits = []
        for p in paths:
            try:
                text = p.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            for i, line in enumerate(text.splitlines(), 1):
                if term in line:
                    hits.append((p.relative_to(ROOT).as_posix(), i))
        print(f'TERM {term!r} -> {len(hits)} hits')
        for rel, ln in hits:
            print(f"   {rel}:{ln}")
        print()

    print("=== 同步草案 S604_REFSYNC_DRAFT.md §2.1 登记的 13 件覆盖计数 ===")
    sync = (ROOT / "lead/s604_refsync_20261109/S604_REFSYNC_DRAFT.md").read_text(encoding="utf-8").splitlines()
    sec21 = "\n".join(sync[16:52])  # :17-52 §2.1
    files13 = [
        "slowframe_r3_20261108/S604_GAP_RECHECK.md",
        "s604_attribution_20261108/S604_ATTRIBUTION.md",
        "s604_attribution_20261108/_sa_ATTRIBUTION_S604.md",
        "ledger_appendix_20261108/LEDGER_APPENDIX_DRAFT.md",
        "ledger_appendix_20261108/_la_draft3_s604_gapdiff.md",
        "ledger_appendix_20261108/_lad_tpl.md",
        "s604_script_gap_20261109/S604_SCRIPT_GAP.md",
        "s604_script_gap_20261109/_sg_FINDINGS.md",
        "s604_exclusive_20261109/S604_EXCLUSIVITY.md",
        "s604_exclusive_20261109/_ex_EXCLUSIVITY.md",
        "slowwindow_n8_20261108/SLOW_WINDOW_LIMITS.md",
        "direction_ruling_20261108/RULING_DIRECTION.md",
        "direction_ruling_20261108/_dr_RULING.md",
    ]
    reg = [f for f in files13 if f in sec21]
    notreg = [f for f in files13 if f not in sec21]
    print(f"§2.1 登记 = {len(reg)} 件: {reg}")
    print(f"§2.1 未登记 = {len(notreg)} 件: {notreg}")

    print()
    print("=== 五件旧指纹第三方登记点（精确 file:line 点查） ===")
    spots = [
        ("lead/PENDING_DECISIONS.md", 26, "0ebd68dd"),
        ("lead/direction_ruling_20261108/RULING_DIRECTION.md", 56, "c6fa7a0a"),
        ("lead/s604_exclusive_20261109/S604_EXCLUSIVITY.md", 27, "a9f293bb"),
        ("lead/s604_exclusive_20261109/_exw_verify.py", 46, "a9f293bb"),
    ]
    for rel, ln, frag in spots:
        try:
            line = (ROOT / rel).read_text(encoding="utf-8", errors="replace").splitlines()[ln - 1]
            print(f"{rel}:{ln} | 含 {frag} = {frag in line} | {line[:160]}")
        except Exception as e:
            print(f"{rel}:{ln} | ERROR {e}")

    print()
    print("=== _sg_FINDINGS.md:71 「时长-空档…」引号内是否有 ** ===")
    l71 = (ROOT / "lead/s604_script_gap_20261109/_sg_FINDINGS.md").read_text(encoding="utf-8").splitlines()[70]
    print(f"「**时长-空档错帧对齐类实现错误（高置信度）**」in line = {'「**时长-空档错帧对齐类实现错误（高置信度）**」' in l71}")
    print(f"「时长-空档错帧对齐类实现错误（高置信度）」in line = {'「时长-空档错帧对齐类实现错误（高置信度）」' in l71}")
    print(f"LINE = {l71[-120:]}")


if __name__ == "__main__":
    main()
