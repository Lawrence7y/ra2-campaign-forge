# -*- coding: utf-8 -*-
"""M64 PANEL.md sync. Line-targeted, assertion-guarded edits only.
Changed lines (1-based): 17, 59, 68, 77 (main panel) and 109, 118, 127 (strict table).
Header line 1, RULING section, 达标 columns and M47 historical snapshot are untouched.
"""
import hashlib, os, sys, json
sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.join(r"D:\Project\ra2-campaign-forge", "lead", "next_re_20261117_r14")
PANEL = os.path.join(ROOT, "COVERAGE", "PANEL.md")
WORK = os.path.join(ROOT, "MERGE_M64", "work")
BAK = os.path.join(WORK, "PANEL.md.bak")

NOTE = ("M64 并表 NAMED_PUSH_AUDIT2 审计 PASS 10 行（S14 "
        "00691EE0/00691FA0/006A4930/006E87F0/006E9140 + S05 "
        "00410C30/00414290/0041CFE0/00524D70/005F9950，均 atlas 内，"
        "evidence_path 改指 NAMED_PUSH_AUDIT2/VERDICT.md；同卡 006A48A0 审计 FAIL 整行拒绝；"
        "00748190 未审不并）")
LIMIT = "〔模板级低信息量 ③b②：析构体内容器 Find 返 -1 哨兵分支成立；与既有 6 行同型，未收紧口径〕"


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
    assert len(p) == 5 and p[2].strip() == "**1,502 / 1,496**", p
    p[2] = " **1,512 / 1,506** "
    put_note(p, 3, NOTE + "；全表 [已证] 1,502→1,512、atlas 内 1,496→1,506、atlas 外仍 6")
    lines[16] = "|".join(p)

    # ---- line 59 (idx58): main S05 ----
    l = lines[58]
    assert l.startswith("| S05 | 643 | 521 |"), repr(l[:60])
    p = cells(l)
    assert len(p) == 13 and p[9].strip() == "165" and p[10].strip() == "25.66", p
    p[9] = " 170 "
    p[10] = " 26.44 "
    put_note(p, 11, NOTE + "；proved 165→170/643=26.44%，未达标")
    lines[58] = "|".join(p)

    # ---- line 68 (idx67): main S14 ----
    l = lines[67]
    assert l.startswith("| S14 | 489 | 330 |"), repr(l[:60])
    p = cells(l)
    assert len(p) == 13 and p[9].strip() == "111" and p[10].strip() == "22.70", p
    p[9] = " 116 "
    p[10] = " 23.72 "
    put_note(p, 11, NOTE + "；" + LIMIT + "；proved 111→116/489=23.72%，未达标")
    lines[67] = "|".join(p)

    # ---- line 77 (idx76): main TOTAL ----
    l = lines[76]
    assert l.startswith("| **TOTAL** | **12,916** | **7210** |"), repr(l[:60])
    p = cells(l)
    assert len(p) == 13 and p[9].strip() == "**1496**" and p[10].strip() == "**11.58**", p
    p[9] = " **1506** "
    p[10] = " **11.66** "
    put_note(p, 11, NOTE + "；M64 +10（S14 5 + S05 5，全 atlas 内）：全表 [已证] 1,502→1,512、"
             "atlas 内 1,496→1,506、atlas 外仍 6；TOTAL proved_pct 11.58→11.66"
             "（实算 1,506/12,916=11.6601%→11.66）；named/L/strict 各列不变")
    lines[76] = "|".join(p)

    # ---- line 109 (idx108): strict S05 ----
    l = lines[108]
    assert l.startswith("| S05 | 643 | 165 |"), repr(l[:60])
    p = cells(l)
    assert len(p) == 11 and [p[i].strip() for i in (3,4,5,6)] == ["165","25.66","**133**","**20.68**"], p
    p[3] = " 170 "; p[4] = " 26.44 "; p[5] = " **138** "; p[6] = " **21.46** "
    lines[108] = "|".join(p)

    # ---- line 118 (idx117): strict S14 ----
    l = lines[117]
    assert l.startswith("| S14 | 489 | 111 |"), repr(l[:60])
    p = cells(l)
    assert len(p) == 11 and [p[i].strip() for i in (3,4,5,6)] == ["111","22.70","**98**","**20.04**"], p
    p[3] = " 116 "; p[4] = " 23.72 "; p[5] = " **103** "; p[6] = " **21.06** "
    lines[117] = "|".join(p)

    # ---- line 127 (idx126): strict TOTAL ----
    l = lines[126]
    assert l.startswith("| **TOTAL** | **12916** | **1496** |"), repr(l[:60])
    p = cells(l)
    assert len(p) == 11 and [p[i].strip() for i in (3,4,5,6)] == ["**1496**","**11.58**","**1169**","**9.05**"], p
    p[3] = " **1506** "; p[4] = " **11.66** "; p[5] = " **1179** "; p[6] = " **9.13** "
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
    assert diff == [16, 58, 67, 76, 108, 117, 126], diff
    # header line 1, RULING section, M47 historical snapshot untouched
    assert after_lines[0] == before_lines[0]
    assert after_lines[184] == before_lines[184] and after_lines[188] == before_lines[188]
    assert after_lines[25] == before_lines[25] and after_lines[26] == before_lines[26]  # D-38/D-44

    result = {
        "before_sha256": before_sha, "after_sha256": after_sha,
        "before_bytes": len(raw), "after_bytes": len(after_raw),
        "changed_lines_1based": [i+1 for i in diff],
        "changed_count": len(diff),
        "header_untouched": True,
        "dod_columns_unchanged": True,
        "m47_snapshot_untouched": True,
    }
    with open(os.path.join(WORK, "panel_merge_result.json"), "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=1)
    print(json.dumps(result, ensure_ascii=False, indent=1))


main()
