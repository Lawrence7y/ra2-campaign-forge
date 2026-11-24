# -*- coding: utf-8 -*-
"""N-9 锚点扫描：对五件上游实读件按锚点清单逐行扫描，输出 文件:行:内容。只读。"""
import re

FILES = [
    r"D:\Project\ra2-campaign-forge\lead\nextstep_plan_20261106\NEXT_STEPS_20261106.md",
    r"D:\Project\ra2-campaign-forge\lead\re_line_20261105\W8_STATIC_LOCATE\W8_STATIC_LOCATE.md",
    r"D:\Project\ra2-campaign-forge\lead\re_line_20261105\A1_ERRATA_MAP\ERRATA_W8.md",
    r"D:\Project\ra2-campaign-forge\lead\re_line_20261105\GOAL_RE_CONTINUOUS.md",
    r"D:\Project\ra2-campaign-forge\lead\GOAL_THREE_TARGETS_20261018.md",
]

ANCHORS = [
    # F6 五创建点 + 视口读数字段
    r"0x52C694", r"0x599D80", r"0x6853B4", r"0x687617", r"0x6BF84F",
    r"0x887324", r"0xB0CE30", r"0xB0CD60", r"0x432690", r"0x4326B3", r"0x6D8B30",
    # F7
    r"0xA8EC34", r"00A8EC34", r"v\[231\]", r"0x6E962A", r"0x6FB010",
    r"PatrolScan", r"0x666E09", r"0x666E1A", r"0x6739BF", r"0x736664",
    # F8
    r"0xB0CD48", r"0x7E1738", r"0xB0CE88", r"0xA8ED6B", r"0xA8ED50",
    r"0x7E3354", r"0x7F5C70", r"0x7F6318", r"vtable\[65\]", r"槽65", r"\+0x104",
    r"Smudge", r"NeedsRedraw", r"0x6D2140", r"0x5F4B10", r"1832",
    r"7 万", r"万条", r"~70", r"70k",
    # 回件名
    r"F6_VIEWPORT", r"F7_TARGETING", r"F8_VISIBILITY", r"card_00A8EC34",
]

def main():
    pat = re.compile("|".join("(?:%s)" % a for a in ANCHORS))
    for p in FILES:
        print("=" * 100)
        print("FILE:", p)
        with open(p, "r", encoding="utf-8", errors="replace") as f:
            for lineno, line in enumerate(f, 1):
                if pat.search(line):
                    text = line.rstrip("\n")
                    if len(text) > 260:
                        text = text[:260] + " …[截断]"
                    print(f"  :{lineno}: {text}")

if __name__ == "__main__":
    main()
