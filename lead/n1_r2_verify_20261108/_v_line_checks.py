# -*- coding: utf-8 -*-
"""验收员行锚核验：对 r2 MD/JSON 所引既有映射行逐条做「行号+关键词」存在性断言。只读。"""
BASE = r"D:\Project\ra2-campaign-forge"

def load(rel):
    with open(BASE + "\\" + rel.replace("/", "\\"), encoding="utf-8") as f:
        return f.read().splitlines()

W8 = load("lead/re_line_20261105/W8_STATIC_LOCATE/W8_STATIC_LOCATE.md")
W9 = load("lead/re_line_20261105/W9_SINGLESTEP_7CFC9F/W9_SINGLESTEP.md")
EW = load("lead/re_line_20261105/A1_ERRATA_MAP/ERRATA_W8.md")
A1 = load("lead/re_line_20261105/A1_ERRATA_MAP/A1_ERRATA_MAP.md")

CHECKS = [
    # (文件, 行号1-based, 必须出现的关键词列表)
    ("W8", 96,  ["House 级", "✅"]),
    ("W8", 97,  ["House 级", "90 帧", "✅"]),
    ("W8", 112, ["0x740B60", "nop 填充"]),
    ("W8", 147, ["House 级"]),
    ("W8", 177, ["6FB03D", "节略"]),
    ("W8", 178, ["740B51", "0x740B60"]),
    ("W8", 179, ["House 级", "存疑登记"]),
    ("W8", 185, ["NEXT_INSN1_DIST", "NEXT_INSN_DIST"]),
    ("W8", 196, ["回件自曝未验要点", "12"]),
    ("W8", 198, ["口径修正生效"]),
    ("W9", 151, ["qc151_trip.py:4575", "if not src.exists"]),
    ("W9", 155, ["QC124_VERDICT.json:8"]),
    ("W9", 156, ["VERDICT_T11.md:148", "ERRATA_EXCEPT_RESTORE.md:12,16,17"]),
    ("W9", 157, ["零真机"]),
    ("W9", 182, ["C2"]),
    ("W9", 184, [":67/:72/:301-302/:171/:176/:77/:169-172/:73-74"]),
    ("W9", 193, ["QC124_VERDICT.json:8,36,47-50,60-63,74-87", "BASELINE_A4_PROPOSAL.md:79,92,104"]),
    ("W9", 200, ["PENDING_DECISIONS.md", "可复核形式"]),
    ("W9", 210, ["02:12 / 02:15:47 / 02:10:46", "qc151_trip.py:4575"]),
    ("W9", 230, ["零真机" ]),
    ("EW", 39,  ["①类"]),
    ("EW", 42,  ["完全无落点"]),
    ("EW", 48,  ["W8-6"]),
    ("EW", 49,  ["W8-11"]),
    ("EW", 52,  ["通吃" ]),
    ("EW", 109, ["6. （小）§1.1 引文补"]),
    ("EW", 110, ["0x6FB03D"]),
    ("EW", 111, ["节略"]),
    ("EW", 113, ["未落实"]),
    ("EW", 114, ["CONFIRMED"]),
    ("EW", 116, ["★ 本组唯一 PARTIAL" ]),
    ("EW", 118, ["7. （小）"]),
    ("EW", 120, ["定位未验"]),
    ("EW", 121, ["PARTIAL（被修原文定位未验）"]),
    ("EW", 122, ["F7_review.md:91-95"]),
    ("EW", 123, ["部分落实"]),
    ("EW", 124, ["PARTIAL"]),
    ("EW", 128, ["F7_TARGETING.md:182"]),
    ("EW", 130, ["存疑登记"]),
    ("EW", 132, ["部分落实"]),
    ("EW", 133, ["CONFIRMED"]),
    ("EW", 156, ["NEXT_INSN1_DIST"]),
    ("EW", 158, ["NEXT_INSN_DIST"]),
    ("EW", 160, ["未落实"]),
    ("EW", 161, ["CONFIRMED"]),
    ("EW", 201, ["未验项"]),
    ("A1", 14,  ["be22211ccf7c694ff8363212aaa639737cb3b09d64293b867e677ba2e6b652ba"]),
    ("A1", 86,  ["W9-2"]),
    ("A1", 88,  ["74-87", "BASELINE_A4_PROPOSAL"]),
    ("A1", 89,  ["版本时刻"]),
    ("A1", 90,  ["02:15:47"]),
    ("A1", 97,  ["W9-2", ":155,:156,:157,:230", "部分落实", "CONFIRMED"]),
    ("A1", 104, ["W9-9", "部分落实", "CONFIRMED"]),
    ("A1", 114, ["W9-19", "部分落实", "CONFIRMED"]),
    ("A1", 122, ["mustFix", "Q4_review.md:427"]),
    ("A1", 130, ["PARTIAL"]),
    ("A1", 144, ["②类"]),
    ("A1", 145, ["③类"]),
    ("A1", 146, ["④类", "完全无落点"]),
    ("A1", 159, ["W8-6", "CONFIRMED"]),
    ("A1", 160, ["W8-7", "PARTIAL"]),
    ("A1", 161, ["W8-8", "部分落实", "CONFIRMED"]),
    ("A1", 164, ["W8-11", "CONFIRMED"]),
    ("A1", 250, ["版本时刻"]),
    ("A1", 255, ["W9-2", "74-87", "W9-9", "W9-19"]),
    ("A1", 263, ["07:50"]),
    ("A1", 284, ["0x6FB03D"]),
    ("A1", 285, ["PARTIAL（被修原文定位未验）", "F7_review.md:94-95"]),
    ("A1", 286, ["存疑登记"]),
    ("A1", 292, ["NEXT_INSN_DIST"]),
    ("A1", 294, ["总限定" ]),
]

FILES = {"W8": W8, "W9": W9, "EW": EW, "A1": A1}
NAMES = {"W8": "W8_STATIC_LOCATE.md", "W9": "W9_SINGLESTEP.md",
         "EW": "ERRATA_W8.md", "A1": "A1_ERRATA_MAP.md"}

npass = nfail = 0
for tag, ln, kws in CHECKS:
    lines = FILES[tag]
    text = lines[ln - 1] if 0 < ln <= len(lines) else ""
    missing = [k for k in kws if k not in text]
    ok = bool(text) and not missing
    status = "PASS" if ok else "FAIL"
    if ok:
        npass += 1
    else:
        nfail += 1
    print(f"[{status}] {NAMES[tag]}:{ln}  缺关键词={missing if missing else '无'}")
    if not ok:
        print("      实际行 = " + text[:200])
print(f"PASS={npass} FAIL={nfail} / TOTAL={len(CHECKS)}")
