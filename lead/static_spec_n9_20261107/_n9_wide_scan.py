# -*- coding: utf-8 -*-
"""N-9 有界宽扫：lead/re_line_20261105（全部 .md/.txt，跳过 >8MB）、lead/GOAL_*.md。
锚点：F7 三锚点 + F8 五缺口 + F6 五创建点。只读，输出 文件:行:内容。"""
import os
import re

ROOTS = [
    r"D:\Project\ra2-campaign-forge\lead\re_line_20261105",
]
EXTRA = [
    r"D:\Project\ra2-campaign-forge\lead\GOAL_THREE_TARGETS_20261018.md",
]
MAXSZ = 8 * 1024 * 1024

PATTERNS = {
    "0x6E962A": re.compile(r"6[Ee]962[Aa]"),
    "v[231]": re.compile(r"v\[231\]|v231"),
    "0xB0CD48": re.compile(r"0?x?[Bb]0[Cc][Dd]48|\[0xB0CD48\]"),
    "0x7E1738": re.compile(r"0?x?7[Ee]1738"),
    "0x7E3354": re.compile(r"0?x?7[Ee]3354"),
    "0x7F5C70": re.compile(r"0?x?7[Ff]5[Cc]70"),
    "0x7F6318": re.compile(r"0?x?7[Ff]6318"),
    "Smudge": re.compile(r"[Ss]mudge"),
    "NeedsRedraw": re.compile(r"NeedsRedraw|Needs_Redraw|\+0x80\]=0|0x80\] ?== ?0"),
    "0xA8ED6B": re.compile(r"[Aa]8[Ee][Dd]6[Bb]"),
    "0x52C694": re.compile(r"0?x?52[Cc]694"),
    "0x599D80": re.compile(r"0?x?599[Dd]80"),
    "0x6853B4": re.compile(r"0?x?6853[Bb]4"),
    "0x687617": re.compile(r"0?x?687617"),
    "0x6BF84F": re.compile(r"0?x?6[Bb][Ff]84[Ff]"),
    "PatrolScan": re.compile(r"PatrolScan"),
    "万条/帧": re.compile(r"7 万|7万|万条|~70|70k"),
}

def scan_file(path):
    if os.path.getsize(path) > MAXSZ:
        print("SKIP(>8MB):", path)
        return
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            for lineno, line in enumerate(f, 1):
                hits = [name for name, pat in PATTERNS.items() if pat.search(line)]
                if hits:
                    text = line.rstrip("\n")
                    if len(text) > 300:
                        text = text[:300] + " …[截断]"
                    print(f"{path}:{lineno} [{','.join(hits)}]\n    {text}")
    except OSError as e:
        print("ERR:", path, e)

def main():
    for root in ROOTS:
        for dirpath, dirnames, filenames in os.walk(root):
            for fn in sorted(filenames):
                if fn.lower().endswith((".md", ".txt")):
                    scan_file(os.path.join(dirpath, fn))
    for p in EXTRA:
        scan_file(p)

if __name__ == "__main__":
    main()
