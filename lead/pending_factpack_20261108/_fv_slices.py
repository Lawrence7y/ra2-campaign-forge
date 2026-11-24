# -*- coding: utf-8 -*-
# _fv_slices.py — 复核员独立切片核对：打印 factpack 承重行号原文（只读）
import hashlib
import pathlib

BASE = pathlib.Path(r"D:/Project/ra2-campaign-forge")
OUT = []

def slice_of(rel, a, b):
    p = BASE / rel
    lines = p.read_bytes().decode("utf-8", errors="replace").splitlines()
    n = len(lines)
    OUT.append(f"===== {rel} :{a}-{b} (file has {n} lines) =====")
    for i in range(max(1, a), min(n, b) + 1):
        OUT.append(f"{i}\t{lines[i-1]}")

slices = [
    ("lead/PENDING_DECISIONS.md", 20, 56),
    ("lead/PENDING_DECISIONS.md", 57, 66),
    ("lead/PENDING_DECISIONS.md", 88, 125),
    ("lead/PENDING_DECISIONS.md", 126, 182),
    ("lead/nextstep_plan_20261106/NEXT_STEPS_20261106.md", 20, 26),
    ("lead/nextstep_plan_20261106/NEXT_STEPS_20261106.md", 93, 125),
    ("lead/perf_repair_n11_20261108/PERF_REPAIR_HANDOFF.md", 72, 112),
    ("lead/perf_repair_n11_20261108/PERF_REPAIR_HANDOFF.md", 140, 166),
    ("lead/perf_repair_n11_20261108/PERF_REPAIR_HANDOFF.md", 174, 182),
    ("lead/direction_ruling_20261108/RULING_DIRECTION.md", 10, 15),
    ("lead/direction_ruling_20261108/RULING_DIRECTION.md", 25, 30),
    ("lead/direction_ruling_20261108/RULING_DIRECTION.md", 38, 47),
    ("lead/direction_ruling_20261108/RULING_DIRECTION.md", 66, 70),
    ("lead/direction_ruling_20261108/RULING_DIRECTION.md", 90, 97),
    ("lead/d26_ruling_20261106/RULING_D26.md", 1, 12),
    ("lead/d26_ruling_20261106/RULING_D26.md", 25, 32),
    ("lead/d26_ruling_20261106/RULING_D26.md", 38, 44),
    ("lead/static_spec_n9_20261107/STATIC_COUNT_SPEC.md", 95, 102),
    ("lead/static_spec_n9_20261107/STATIC_COUNT_SPEC.md", 135, 145),
    ("lead/static_spec_n9_20261107/STATIC_COUNT_SPEC.md", 150, 171),
    ("lead/static_spec_n9_20261107/STATIC_COUNT_SPEC.md", 188, 200),
    ("lead/re_line_20261105/W8_STATIC_LOCATE/W8_STATIC_LOCATE.md", 125, 132),
    ("lead/re_line_20261105/W8_STATIC_LOCATE/W8_STATIC_LOCATE.md", 158, 164),
    ("lead/n11_protocol_spec_20261108/OBSERVATION_PROTOCOL_SPEC.md", 1, 8),
    ("lead/n11_protocol_spec_20261108/OBSERVATION_PROTOCOL_SPEC.md", 45, 53),
    ("lead/n11_protocol_spec_20261108/OBSERVATION_PROTOCOL_SPEC.md", 58, 61),
    ("lead/n11_protocol_spec_20261108/OBSERVATION_PROTOCOL_SPEC.md", 85, 94),
    ("lead/n11_protocol_spec_20261108/OBSERVATION_PROTOCOL_SPEC.md", 174, 178),
    ("lead/n11_protocol_spec_20261108/OBSERVATION_PROTOCOL_SPEC.md", 265, 271),
    ("lead/n11_protocol_spec_20261108/OBSERVATION_PROTOCOL_SPEC.md", 300, 308),
    ("lead/n11_protocol_spec_20261108/OBSERVATION_PROTOCOL_SPEC.md", 364, 370),
    ("lead/n11_protocol_spec_20261108/OBSERVATION_PROTOCOL_SPEC.md", 422, 440),
    ("lead/n11_protocol_spec_20261108/_ps_N11_MIN_OBS_PROTOCOL_SPEC.md", 300, 306),
    ("lead/GOAL_THREE_TARGETS_20261018.md", 50, 56),
    ("lead/GOAL_THREE_TARGETS_20261018.md", 4387, 4395),
    ("lead/GOAL_THREE_TARGETS_20261018.md", 5136, 5144),
    ("lead/GOAL_THREE_TARGETS_20261018.md", 5822, 5834),
    ("lead/GOAL_THREE_TARGETS_20261018.md", 6015, 6072),
    ("lead/GOAL_THREE_TARGETS_20261018.md", 6640, 6650),
    ("lead/GOAL_THREE_TARGETS_20261018.md", 8400, 8416),
    ("lead/GOAL_THREE_TARGETS_20261018.md", 9737, 9760),
    ("lead/re_line_20261105/GOAL_RE_CONTINUOUS.md", 88, 110),
]
for rel, a, b in slices:
    slice_of(rel, a, b)

# factpack 声称「另实算 7 件」的指纹独立补算
OUT.append("===== extra fingerprints (factpack claims: RULING_D24/D26/D27/D28/D29/D30/W8) =====")
extra = [
    "lead/re_line_20261105/D24_RULING/RULING_D24.md",
    "lead/d26_ruling_20261106/RULING_D26.md",
    "lead/d27_ruling_20261106/RULING_D27.md",
    "lead/re_line_20261105/W8_STATIC_LOCATE/W8_STATIC_LOCATE.md",
]
for rel in extra:
    data = (BASE / rel).read_bytes()
    OUT.append(f"{rel}|sha256={hashlib.sha256(data).hexdigest()}|bytes={len(data)}")

# D27..D30 撰写人自述「正文本体未读」——复核同样只列指纹存在性，不读本体
d28 = list(BASE.glob("lead/**/RULING_D28.md"))
d29 = list(BASE.glob("lead/**/RULING_D29.md"))
d30 = list(BASE.glob("lead/**/RULING_D30.md"))
OUT.append(f"glob RULING_D28.md -> {[str(x) for x in d28]}")
OUT.append(f"glob RULING_D29.md -> {[str(x) for x in d29]}")
OUT.append(f"glob RULING_D30.md -> {[str(x) for x in d30]}")

text = "\n".join(OUT) + "\n"
out_path = BASE / "lead/pending_factpack_20261108/_fv_slices_out.txt"
out_path.write_text(text, encoding="utf-8")
print(f"written {out_path} bytes={len(text.encode('utf-8'))} slices={len(slices)}")
