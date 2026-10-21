"""构建长输入可靠性基准语料 + 标准答案。

语料来源：真实项目件拼接（不造假），在受控字节偏移处注入 12 条 canary。
标准答案写入 ground_truth.json，供独立核验。
"""
import hashlib
import json
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")
LEAD = ROOT / "out/re_work/work_chain/CONTINUE_20261003/lead"
OUT = LEAD / "goal_bench_longinput_20261021"
OUT.mkdir(parents=True, exist_ok=True)

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
        blocks.append(f"\n\n===== BEGIN {p.name} =====\n{txt}\n===== END {p.name} =====\n")

# 目标约 180KB：循环拼接直到够长
body = "".join(blocks)
while len(body.encode("utf-8")) < 150_000:
    body += "\n\n----- 附录重复区（同源件复本，用于制造长上下文）-----\n" + "".join(blocks)
body += "\n\n===== 语料结束标记 EOF-MARKER-9F3A =====\n"

raw = body.encode("utf-8")
print(f"base corpus = {len(raw):,} B")

# ---- 注入 12 条 canary，位置按比例散布（含最尾部一条，测截断） ----
FRACTIONS = [0.03, 0.11, 0.19, 0.27, 0.35, 0.43, 0.51, 0.59, 0.67, 0.75, 0.86, 0.995]
canaries = {}
inserts = []  # (byte_offset, bytes)

for i, frac in enumerate(FRACTIONS, 1):
    cid = f"CNY{i:02d}"
    # 确定性值：三位数 + 字母 + 序号，可复现且与正文数字不混淆
    val = f"{137 + i * 61}-{chr(65 + i % 26)}{i:02d}Z"
    canaries[cid] = val
    off = int(len(raw) * frac)
    # 回退到最近的换行，避免截断多字节字符
    while off > 0 and raw[off - 1:off] != b"\n":
        off -= 1
    line = f"\n[CANARY] {cid} = {val}\n".encode("utf-8")
    inserts.append((off, line))

# 从后往前插入，保证前面偏移不失效
for off, line in sorted(inserts, key=lambda x: -x[0]):
    raw = raw[:off] + line + raw[off:]

corpus_path = OUT / "long_corpus.txt"
corpus_path.write_bytes(raw)

# ---- 计算题目答案 ----
text = raw.decode("utf-8")
n_bytes = len(raw)
n_lines = raw.count(b"\n")
n_chars = len(text)
sha = hashlib.sha256(raw).hexdigest()

# 额外可验证题：语料中出现的 "0x0084F2BA" 次数、"§314" 次数
cnt_addr = text.count("0x0084F2BA")
cnt_sec314 = text.count("§314")
cnt_eof = text.count("EOF-MARKER-9F3A")

# 尾部事实：最后 200 字节的内容
tail200 = raw[-200:].decode("utf-8", errors="replace")

truth = {
    "corpus_path": str(corpus_path),
    "corpus_bytes": n_bytes,
    "corpus_lines": n_lines,
    "corpus_chars": n_chars,
    "corpus_sha256": sha,
    "canaries": canaries,
    "canary_count": len(canaries),
    "count_0x0084F2BA": cnt_addr,
    "count_sec314": cnt_sec314,
    "count_eof_marker": cnt_eof,
    "tail200": tail200,
}
(OUT / "ground_truth.json").write_text(
    json.dumps(truth, ensure_ascii=False, indent=1), encoding="utf-8")

print(f"final corpus = {n_bytes:,} B / {n_lines:,} lines / {n_chars:,} chars")
print(f"sha256 = {sha}")
print(f"canaries = {len(canaries)}")
for k, v in canaries.items():
    print(f"   {k} = {v}")
print(f"count 0x0084F2BA = {cnt_addr}")
print(f"count §314      = {cnt_sec314}")
print(f"count EOF-MARKER= {cnt_eof}")
print(f"\nwrote {corpus_path}")
print(f"wrote {OUT / 'ground_truth.json'}")
