"""修正 canary 注入：从干净语料重建两档，确保每条 canary 只出现一次。

缺陷说明：初版 60K 是从已注入 canary 的 240K 母语料裁出后再注入，
导致 CNY01/02/03 重复出现（共 15 次而非 12 次），题目变简单。
本脚本从源件重新拼接，canary 只注入一次。
"""
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")
LEAD = ROOT / "out/re_work/work_chain/CONTINUE_20261003/lead"
OUT = LEAD / "goal_bench_longinput_20261021"

SOURCES = [
    LEAD / "qc161_u0400_trip/l1a_20261020/E2_SUCCESS_TRIP_REPORT.md",
    LEAD / "goal1_e2_verdict_20261020/E2_GATE_VERDICT.md",
    LEAD / "goal2_crashaddr_20261020/CRASH_ADDR_ANALYSIS.md",
    LEAD / "goal2_crashaddr_20261020/VERIFY_GLM.md",
    LEAD / "goal3_verifyhooks_fix_20261020/RECEIPT.md",
    LEAD / "goal3_p1sbh_merge_20261020/RECEIPT.md",
    LEAD / "goal1_baseline_design_20261020/BASELINE_MEASURE_DESIGN.md",
]

blocks = []
for p in SOURCES:
    if p.exists():
        txt = p.read_text(encoding="utf-8", errors="replace")
        # 源件本身不含 CANARY，但保险起见剥掉
        txt = re.sub(r"\[CANARY\][^\n]*\n", "", txt)
        blocks.append(f"\n\n===== BEGIN {p.name} =====\n{txt}\n===== END {p.name} =====\n")

base = "".join(blocks)
if len(base.encode("utf-8")) < 200_000:
    base += "\n\n----- 附录重复区（同源件复本，用于制造长上下文）-----\n" + "".join(blocks)

# 每条 canary 的值设计成「反直觉但可验证」：数字不递增，防止模型猜规律
CANARY_SPEC = [
    ("CNY01", "517-Q01X"),
    ("CNY02", "204-K02W"),
    ("CNY03", "893-P03V"),
    ("CNY04", "136-B04R"),
    ("CNY05", "748-T05N"),
    ("CNY06", "462-G06M"),
    ("CNY07", "905-Z07H"),
    ("CNY08", "371-C08D"),
    ("CNY09", "628-V09L"),
    ("CNY10", "489-Y10F"),
    ("CNY11", "057-W11S"),
    ("CNY12", "762-J12E"),
]
FRACTIONS = [0.02, 0.10, 0.18, 0.26, 0.34, 0.42, 0.50, 0.58, 0.66, 0.74, 0.87, 0.994]


def build(target_bytes, marker, out_name):
    body = base
    while len(body.encode("utf-8")) < target_bytes:
        body += "\n\n----- 附录重复区 2 -----\n" + "".join(blocks)
    raw = body.encode("utf-8")
    # 截到目标（按行回退）
    raw = raw[:target_bytes]
    while raw and raw[-1:] != b"\n":
        raw = raw[:-1]

    inserts = []
    for (cid, val), frac in zip(CANARY_SPEC, FRACTIONS):
        off = int(len(raw) * frac)
        while off > 0 and raw[off - 1:off] != b"\n":
            off -= 1
        inserts.append((off, f"\n[CANARY] {cid} = {val}\n".encode("utf-8")))
    for off, line in sorted(inserts, key=lambda x: -x[0]):
        raw = raw[:off] + line + raw[off:]

    raw += f"\n===== 语料结束标记 {marker} =====\n".encode("utf-8")

    p = OUT / out_name
    p.write_bytes(raw)

    text = raw.decode("utf-8")
    found = re.findall(r"\[CANARY\] (CNY\d\d) = (\S+)", text)
    assert len(found) == 12, f"canary count should be 12, got {len(found)}"
    assert len(set(c for c, _ in found)) == 12, "duplicate canary ids"
    canaries = dict(found)
    assert canaries == dict(CANARY_SPEC), f"canary value mismatch: {canaries}"

    truth = {
        "corpus_path": str(p),
        "corpus_bytes": len(raw),
        "corpus_lines": raw.count(b"\n"),
        "corpus_chars": len(text),
        "corpus_sha256": hashlib.sha256(raw).hexdigest(),
        "canaries": canaries,
        "canary_count": 12,
        "count_0x0084F2BA": text.count("0x0084F2BA"),
        "count_eof_marker": len(re.findall(r"EOF-MARKER-[0-9A-F]{4}", text)),
        "tail_marker_expected": marker,
        "tail120": raw[-120:].decode("utf-8", errors="replace"),
        # 附加可验证项：唯一性检验（模型若幻觉会答错）
        "canary_positions_pct": [round(100 * raw.find(f"[CANARY] {c}".encode()) / len(raw), 2)
                                 for c, _ in CANARY_SPEC],
    }
    tp = OUT / out_name.replace(".txt", "_truth.json")
    tp.write_text(json.dumps(truth, ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"{out_name}: {len(raw):,} B / {truth['corpus_lines']:,} lines")
    print(f"   sha256 = {truth['corpus_sha256'][:32]}…")
    print(f"   canary = {len(found)} 条（唯一性 OK）")
    print(f"   count_0x0084F2BA = {truth['count_0x0084F2BA']}")
    print(f"   count_eof        = {truth['count_eof_marker']}")
    print(f"   tail             = {marker}")
    print(f"   positions %      = {truth['canary_positions_pct']}")
    print(f"   truth → {tp.name}")
    print()
    return truth


print("=== 重建干净语料 ===")
t60 = build(60_000, "EOF-MARKER-C4D1", "corpus_v2_60k.txt")
t240 = build(240_000, "EOF-MARKER-A8E5", "corpus_v2_240k.txt")

# 同时把 60K 的 truth 覆盖到 ground_truth_60k.json 供评分器使用
(OUT / "ground_truth_60k.json").write_text(
    json.dumps(t60, ensure_ascii=False, indent=1), encoding="utf-8")
(OUT / "ground_truth_240k.json").write_text(
    json.dumps(t240, ensure_ascii=False, indent=1), encoding="utf-8")
print("ground_truth_60k.json / ground_truth_240k.json 已更新")
