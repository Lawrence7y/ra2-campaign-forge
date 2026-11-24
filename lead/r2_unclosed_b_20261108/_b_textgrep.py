# -*- coding: utf-8 -*-
"""崩点2/6 补证③：在 lead/ 全树 + 仓库根一级的文本件（.md/.txt/.py/.json）中定位
(a) 两个争议尾串的字面出现处（回件 evidence 原文）；
(b) og=None 在 .md 件中的出现行（判定「og=None 被当作 §3.2 未验解释」的出处）；
(c) 「空列」「答非所问」在 .md 件中的出现行（崩点4/6 原始登记措辞）；
(d) 崩点 在 CRITERIA_ROUND2.md 中的原始登记行。只读；路径全常量 + 包含校验。"""
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")
LEAD = ROOT / "lead"
WD = LEAD / "r2_unclosed_b_20261108"
OUT = WD / "_b_textgrep_out.txt"
TAIL_PATS = ["26f3fb61829756dfeecf", "b6f95763794"]
MD_PATS = ["og=None", "空列", "答非所问"]
CR2_PATS = ["崩点"]
SUF = {".md", ".txt", ".py", ".json"}
MAXLINE = 260

def scan_file(p: Path, tag: str, pats):
    rows = []
    try:
        raw = p.read_bytes()
    except OSError:
        return rows
    if len(raw) > 20_000_000:
        return rows
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        text = raw.decode("utf-8", errors="replace")
    for i, line in enumerate(text.splitlines(), 1):
        s = line.strip()
        for pat in pats:
            if pat in s:
                rows.append(f"[{tag}] {str(p)[len(str(ROOT))+1:]}:{i}: {s[:MAXLINE]}")
    return rows

out_rows = []
n_files = 0
for p in LEAD.rglob("*"):
    if not p.is_file() or ".git" in p.parts or ".mimosa" in p.parts or "__pycache__" in p.parts:
        continue
    ext = p.suffix.lower()
    if ext not in SUF:
        continue
    out_rows += scan_file(p, "TAIL", TAIL_PATS)
    if ext == ".md":
        out_rows += scan_file(p, "MD", MD_PATS)
    if p.name == "CRITERIA_ROUND2.md":
        out_rows += scan_file(p, "CR2", CR2_PATS)
    n_files += 1

for p in ROOT.iterdir():
    if p.is_file() and p.suffix.lower() in SUF:
        out_rows += scan_file(p, "TAIL", TAIL_PATS)
        if p.suffix.lower() == ".md":
            out_rows += scan_file(p, "MD", MD_PATS)
        n_files += 1

head = [f"scanned_text_files={n_files}", f"total_matched_lines={len(out_rows)}", ""]
txt = "\n".join(head + out_rows) + "\n"
assert OUT.is_relative_to(WD)
OUT.write_text(txt, encoding="utf-8")
print("\n".join(head + out_rows[:80]))
print(f"...(full written, {len(txt)} chars, {len(out_rows)} matches)")
