# -*- coding: utf-8 -*-
"""_verify_hit_structure.py — 确认两命中 mjs 的尾串全部位于第 9 行 payload，
且 payload 解码后 DIR/DOC 与回件一致。只读。"""
import json, re, os
R = r"D:\Project\ra2-campaign-forge\.zcode\workflow-runs"
for fn in ["dwfrun-a05ccb49-e10b-4004-8ce6-5f5b48d7820e.mjs",
           "dwfrun-a7c7b5f9-25d5-400a-bd45-6f32a262430b.mjs"]:
    t = open(os.path.join(R, fn), encoding="utf-8").read()
    lines = t.split("\n")
    L = lines[8]
    pat = re.compile(r'"((?:[^"\\]|\\.)*)"')
    for mm in pat.finditer(L):
        s = mm.group(1)
        if len(s) > 500:
            d = json.loads('"' + s + '"')
            print(fn[:22], "payload_chars", len(d), "payload_lines", len(d.split("\n")))
            for i, l in enumerate(d.split("\n"), 1):
                if "const DIR" in l or "const DOC" in l:
                    print("   P%03d| %s" % (i, l))
            break
    outside = [(i, l[:160]) for i, l in enumerate(lines, 1)
               if i != 9 and ("26f3fb61829756dfeecf" in l or "b6f95763794" in l)]
    print("   occurrences_outside_line9 =", len(outside), outside[:3])
