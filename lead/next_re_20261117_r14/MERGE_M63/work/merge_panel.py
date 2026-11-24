# -*- coding: utf-8 -*-
"""M63 PANEL.md sync. Line-targeted, assertion-guarded edits only.
Only lines 17, 68, 72, 77 (main panel) and 118, 122, 127 (strict table) change.
"""
import hashlib, os, sys
sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.join(r"D:\Project\ra2-campaign-forge", "lead", "next_re_20261117_r14")
PANEL = os.path.join(ROOT, "COVERAGE", "PANEL.md")
WORK = os.path.join(ROOT, "MERGE_M63", "work")
BAK = os.path.join(WORK, "PANEL.md.bak")

NOTE = ("M63 并表 NAMED_PUSH 审计 PASS 6 行（S18 005414C0/0071F8C0 + S14 "
        "0041F580/00503040/00512290/00512480，均 atlas 内，evidence_path 改指 "
        "NAMED_PUSH_AUDIT/VERDICT.md；同卡 005C46E0/0065AC40 审计 FAIL 整行拒绝），"
        "来源批次 NAMED_PUSH_S18_B1/B2 与 S14_B1")


def sha(b):
    return hashlib.sha256(b).hexdigest()


def cells(line):
    return line.split("|")


def put_note(parts, idx, note):
    parts[idx] = " " + note + "；" + parts[idx].strip() + " "


def main():
    raw = open(PANEL, "rb").read()
    assert not raw.startswith(b"\xef\xbb\xbf") and b"\r\n" not in raw
    before_sha = sha(raw)
    open(BAK, "wb").write(raw)
    before_lines = raw.decode("utf-8").split("\n")
    lines = list(before_lines)

    # ---- line 17 (idx16): 全表/atlas 内 proved ----
    l = lines[16]
    assert l.startswith("| 全表 `[已证]` / atlas 内 `[已证]` |"), repr(l[:60])
    p = cells(l)
    assert len(p) == 5 and p[2].strip() == "**1,496 / 1,490**", p
    p[2] = " **1,502 / 1,496** "
    put_note(p, 3, NOTE + "；全表 [已证] 1,496→1,502、atlas 内 1,490→1,496、atlas 外仍 6")
    lines[16] = "|".join(p)

    # ---- line 68 (idx67): main S14 ----
    l = lines[67]
    assert l.startswith("| S14 | 489 | 330 |"), repr(l[:60])
    p = cells(l)
    assert len(p) == 13 and p[9].strip() == "107" and p[10].strip() == "21.88", p
    p[9] = " 111 "
    p[10] = " 22.70 "
    put_note(p, 11, NOTE + "；proved 107→111/489=22.70%，未达标")
    lines[67] = "|".join(p)

    # ---- line 72 (idx71): main S18 ----
    l = lines[71]
    assert l.startswith("| S18 | 659 | 497 |"), repr(l[:60])
    p = cells(l)
    assert len(p) == 13 and p[9].strip() == "54" and p[10].strip() == "8.19", p
    p[9] = " 56 "
    p[10] = " 8.50 "
    put_note(p, 11, NOTE + "；proved 54→56/659=8.50%，未达标")
    lines[71] = "|".join(p)

    # ---- line 77 (idx76): main TOTAL ----
    l = lines[76]
    assert l.startswith("| **TOTAL** | **12,916** | **7210** |"), repr(l[:60])
    p = cells(l)
    assert len(p) == 13 and p[9].strip() == "**1490**" and p[10].strip() == "**11.54**", p
    p[9] = " **1496** "
    p[10] = " **11.58** "
    put_note(p, 11, NOTE + "；M63 +6（S18 2 + S14 4，全 atlas 内）：全表 [已证] 1,496→1,502、"
             "atlas 内 1,490→1,496、atlas 外仍 6；TOTAL proved_pct 11.54→11.58"
             "（实算 1,496/12,916=11.5825%→11.58）；named/L/strict 各列不变")
    lines[76] = "|".join(p)

    # ---- line 118 (idx117): strict S14 ----
    l = lines[117]
    assert l.startswith("| S14 | 489 | 107 |"), repr(l[:60])
    p = cells(l)
    assert len(p) == 11 and [p[i].strip() for i in (3,4,5,6)] == ["107","21.88","**94**","**19.22**"], p
    p[3] = " 111 "; p[4] = " 22.70 "; p[5] = " **98** "; p[6] = " **20.04** "
    lines[117] = "|".join(p)

    # ---- line 122 (idx121): strict S18 ----
    l = lines[121]
    assert l.startswith("| S18 | 659 | 54 |"), repr(l[:60])
    p = cells(l)
    assert len(p) == 11 and [p[i].strip() for i in (3,4,5,6)] == ["54","8.19","**44**","**6.68**"], p
    p[3] = " 56 "; p[4] = " 8.50 "; p[5] = " **46** "; p[6] = " **6.98** "
    lines[121] = "|".join(p)

    # ---- line 127 (idx126): strict TOTAL ----
    l = lines[126]
    assert l.startswith("| **TOTAL** | **12916** | **1490** |"), repr(l[:60])
    p = cells(l)
    assert len(p) == 11 and [p[i].strip() for i in (3,4,5,6)] == ["**1490**","**11.54**","**1163**","**9.00**"], p
    p[3] = " **1496** "; p[4] = " **11.58** "; p[5] = " **1169** "; p[6] = " **9.05** "
    # 达标列（名义 3/22、严格 1/22）不动
    assert p[8].strip() == "**3/22**" and p[9].strip() == "**1/22**", p
    lines[126] = "|".join(p)

    after_raw = "\n".join(lines).encode("utf-8")
    open(PANEL, "wb").write(after_raw)
    after_sha = sha(after_raw)

    # ---- verification: only 7 lines changed ----
    after_lines = after_raw.decode("utf-8").split("\n")
    assert len(after_lines) == len(before_lines)
    diff = [i for i in range(len(before_lines)) if before_lines[i] != after_lines[i]]
    assert diff == [16, 67, 71, 76, 117, 121, 126], diff
    # M47 historical snapshot (1-based 185,189) untouched
    assert after_lines[184] == before_lines[184] and after_lines[188] == before_lines[188]

    result = {
        "before_sha256": before_sha, "after_sha256": after_sha,
        "before_bytes": len(raw), "after_bytes": len(after_raw),
        "changed_lines_1based": [i+1 for i in diff],
        "changed_count": len(diff),
        "m47_snapshot_untouched": True,
        "dod_unchanged_main_total": cells(after_lines[76])[8].strip(),
    }
    with open(os.path.join(WORK, "panel_merge_result.json"), "w", encoding="utf-8") as f:
        import json
        json.dump(result, f, ensure_ascii=False, indent=1)
    print(__import__("json").dumps(result, ensure_ascii=False, indent=1))


main()
