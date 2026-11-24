"""S1 · 复算 P0 真实待裁量（ENUM.UNDECIDABLE ∖ coverage.entry，entry 统一大写）。

输出：EVIDENCE/pool_1669.tsv（address + ENUM 原始列）、EVIDENCE/s1_numbers.json
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from p0m_common import COVERAGE, ENUM, EVIDENCE, Image, load_lines, norm_addr

img = Image()

# --- coverage.tsv: 表头用逗号、数据行用 TAB（§7 格式陷阱）---
cov_lines = load_lines(COVERAGE)
cov_hdr = cov_lines[0]
cov = set()
cov_bad = 0
for ln in cov_lines[1:]:
    if not ln.strip():
        continue
    parts = ln.split("\t")
    if len(parts) < 2:
        parts = ln.split(",")
        cov_bad += 1
    cov.add(norm_addr(parts[0]))

# --- ENUM.tsv ---
enum_lines = load_lines(ENUM)
hdr = enum_lines[0].split("\t")
verdicts = {"FUNC": 0, "NOT_FUNC": 0, "UNDECIDABLE": 0}
undec = []
rows = []
for ln in enum_lines[1:]:
    if not ln.strip():
        continue
    p = ln.split("\t")
    a = norm_addr(p[0])
    v = p[2]
    verdicts[v] = verdicts.get(v, 0) + 1
    rows.append((a, p))
    if v == "UNDECIDABLE":
        undec.append((a, p))

undec_set = set(a for a, _ in undec)
in_cov = [a for a in undec_set if a in cov]
not_in_cov = sorted(a for a in undec_set if a not in cov)

# 另核 FUNC 20 是否全在表（COMMON §9.0i 声明）
func_rows = [a for a, p in rows if p[2] == "FUNC"]
func_in_cov = [a for a in func_rows if a in cov]
nf_rows = [a for a, p in rows if p[2] == "NOT_FUNC"]
nf_in_cov = [a for a in nf_rows if a in cov]

# 池内地址对齐与所在段自检
align16 = sum(1 for a in not_in_cov if int(a, 16) % 16 == 0)
in_text = sum(1 for a in not_in_cov if img.in_text(int(a, 16)))

os.makedirs(EVIDENCE, exist_ok=True)
with open(os.path.join(EVIDENCE, "pool_1669.tsv"), "w", encoding="utf-8") as f:
    f.write("\t".join(hdr) + "\n")
    keep = {a: p for a, p in undec}
    for a in not_in_cov:
        f.write("\t".join(keep[a]) + "\n")

numbers = dict(
    target_sha256=img.sha256,
    target_size=img.size,
    image_base=hex(img.image_base),
    text=[hex(img.text_start), hex(img.text_end)],
    coverage_data_rows=len(cov_lines) - 1,
    coverage_entries=len(cov),
    coverage_rows_split_by_comma=cov_bad,
    enum_data_rows=len(rows),
    enum_verdicts=verdicts,
    enum_undecidable_total=len(undec_set),
    undecidable_in_coverage=len(in_cov),
    undecidable_not_in_coverage=len(not_in_cov),
    func_total=len(func_rows),
    func_in_coverage=len(func_in_cov),
    not_func_total=len(nf_rows),
    not_func_in_coverage=len(nf_in_cov),
    pool_align16=align16,
    pool_in_text=in_text,
    pool_min=not_in_cov[0] if not_in_cov else None,
    pool_max=not_in_cov[-1] if not_in_cov else None,
)
with open(os.path.join(EVIDENCE, "s1_numbers.json"), "w", encoding="utf-8") as f:
    json.dump(numbers, f, ensure_ascii=False, indent=2)

print(json.dumps(numbers, ensure_ascii=False, indent=2))
